import assert from "node:assert/strict";
import { afterEach, test } from "node:test";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const ts = require("typescript");
const route = readFileSync(
  new URL("../app/api/[...path]/route.ts", import.meta.url),
  "utf8",
);
const compiled = ts.transpileModule(route, {
  fileName: "route.ts",
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2022,
    inlineSourceMap: true,
    inlineSources: true,
    sourceRoot: new URL("../app/api/[...path]/", import.meta.url).pathname,
  },
}).outputText;
mkdirSync(new URL("../.test-build/", import.meta.url), { recursive: true });
const compiledUrl = new URL("../.test-build/proxy-route.mjs", import.meta.url);
writeFileSync(compiledUrl, compiled);
const { GET, POST, PUT, PATCH } = await import(compiledUrl.href);

const originalFetch = globalThis.fetch;
const originalEnvironment = { ...process.env };
afterEach(() => {
  globalThis.fetch = originalFetch;
  process.env = { ...originalEnvironment };
});
function request(method = "GET", headers = {}, body) {
  const result = new Request("http://localhost:3000/api/research-runs", {
    method,
    headers: { host: "localhost:3000", ...headers },
    body,
    ...(body instanceof ReadableStream ? { duplex: "half" } : {}),
  });
  result.nextUrl = new URL(result.url);
  return result;
}
const context = { params: Promise.resolve({ path: ["research-runs"] }) };

test("proxy forwards separate identity and service credentials and relays cooldown", async () => {
  process.env.RESEARCH_API_URL = "http://private-api:8000";
  process.env.API_BEARER_TOKEN = "fixture-service-token-32-characters";
  globalThis.fetch = async (target, init) => {
    assert.equal(String(target), "http://private-api:8000/research-runs");
    assert.equal(init.headers.get("authorization"), "Bearer fixture-access");
    assert.equal(
      init.headers.get("x-neurolab-service-token"),
      process.env.API_BEARER_TOKEN,
    );
    assert.equal(
      init.headers.get("cookie"),
      "neurolab_refresh=fixture; neurolab_csrf=csrf",
    );
    assert.equal(init.redirect, "manual");
    return new Response("{}", {
      status: 429,
      headers: { "retry-after": "30", "content-type": "application/json" },
    });
  };
  const response = await GET(
    request("GET", {
      authorization: "Bearer fixture-access",
      cookie: "other=private; neurolab_refresh=fixture; neurolab_csrf=csrf",
    }),
    context,
  );
  assert.equal(response.status, 429);
  assert.equal(response.headers.get("retry-after"), "30");
  assert.equal(response.headers.get("x-neurolab-service-token"), null);
});

test("cross-origin mutations are rejected before contacting FastAPI", async () => {
  globalThis.fetch = () => {
    throw new Error("must not contact upstream");
  };
  const response = await POST(
    request("POST", { origin: "https://attacker.invalid" }, "{}"),
    context,
  );
  assert.equal(response.status, 403);
});

test("same-origin mutations relay CSRF and multiple HttpOnly cookies", async () => {
  globalThis.fetch = async (_target, init) => {
    assert.equal(init.headers.get("x-csrf-token"), "csrf");
    const headers = new Headers();
    headers.append(
      "set-cookie",
      "neurolab_refresh=rotated; HttpOnly; SameSite=Lax",
    );
    headers.append("set-cookie", "neurolab_csrf=rotated-csrf; SameSite=Lax");
    return new Response("{}", { headers });
  };
  const response = await POST(
    request(
      "POST",
      { origin: "http://localhost:3000", "x-csrf-token": "csrf" },
      "{}",
    ),
    context,
  );
  assert.equal(response.status, 200);
  assert.equal(response.headers.getSetCookie().length, 2);
});

test("oversize chunked bodies are rejected before upstream execution", async () => {
  globalThis.fetch = () => {
    throw new Error("must not contact upstream");
  };
  const body = new ReadableStream({
    start(controller) {
      controller.enqueue(new Uint8Array(262145));
      controller.close();
    },
  });
  const response = await POST(request("POST", {}, body), context);
  assert.equal(response.status, 413);
});

test("invalid lengths and unavailable upstreams return bounded errors", async () => {
  const invalid = await POST(
    request("POST", { "content-length": "invalid" }, "{}"),
    context,
  );
  assert.equal(invalid.status, 400);
  globalThis.fetch = () => {
    throw new Error("fixture failure containing private service details");
  };
  const failed = await GET(request(), context);
  assert.equal(failed.status, 502);
  assert.doesNotMatch(await failed.text(), /private service details/);
});

test("production rejects missing service configuration", async () => {
  process.env.NODE_ENV = "production";
  delete process.env.RESEARCH_API_URL;
  delete process.env.API_BEARER_TOKEN;
  const response = await GET(request(), context);
  assert.equal(response.status, 503);
});

for (const [method, handler] of [
  ["PUT", PUT],
  ["PATCH", PATCH],
]) {
  test(`${method} preserves authenticated draft/profile mutation semantics`, async () => {
    globalThis.fetch = async (_target, init) => {
      assert.equal(init.method, method);
      assert.equal(init.headers.get("authorization"), "Bearer fixture-access");
      assert.equal(init.headers.get("x-csrf-token"), "csrf");
      assert.equal(
        new TextDecoder().decode(init.body),
        '{"objective":"Exact\\ntext"}',
      );
      return new Response('{"revision":1}', {
        headers: { "content-type": "application/json" },
      });
    };
    const response = await handler(
      request(
        method,
        {
          origin: "http://localhost:3000",
          authorization: "Bearer fixture-access",
          "x-csrf-token": "csrf",
        },
        '{"objective":"Exact\\ntext"}',
      ),
      context,
    );
    assert.equal(response.status, 200);
  });
}

test("proxy discards browser-supplied client identity unless an ingress header is explicitly trusted", async () => {
  process.env.RESEARCH_API_URL = "http://private-api:8000";
  process.env.API_BEARER_TOKEN = "fixture-service-token-32-characters";
  delete process.env.NEUROLAB_TRUSTED_CLIENT_IP_HEADER;
  globalThis.fetch = async (_target, init) => {
    assert.equal(init.headers.get("x-neurolab-client-ip"), null);
    assert.equal(init.headers.get("x-forwarded-for"), null);
    return new Response("{}", { status: 200 });
  };
  await GET(
    request("GET", {
      "x-neurolab-client-ip": "198.51.100.7",
      "x-forwarded-for": "198.51.100.8",
    }),
    context,
  );
});

test("proxy forwards only a single valid IP from the configured trusted ingress field", async () => {
  process.env.RESEARCH_API_URL = "http://private-api:8000";
  process.env.API_BEARER_TOKEN = "fixture-service-token-32-characters";
  process.env.NEUROLAB_TRUSTED_CLIENT_IP_HEADER = "x-edge-client-ip";
  const received = [];
  globalThis.fetch = async (_target, init) => {
    received.push(init.headers.get("x-neurolab-client-ip"));
    return new Response("{}", { status: 200 });
  };
  await GET(
    request("GET", {
      "x-edge-client-ip": "2001:db8::1",
      "x-neurolab-client-ip": "198.51.100.99",
    }),
    context,
  );
  await GET(
    request("GET", { "x-edge-client-ip": "198.51.100.1, 198.51.100.2" }),
    context,
  );
  await GET(
    request("GET", { "x-edge-client-ip": "fe80::1%arbitrary" }),
    context,
  );
  assert.deepEqual(received, ["2001:db8::1", null, null]);
});

test("SSE reconnect forwards the persisted event cursor without replaying earlier frames", async () => {
  process.env.RESEARCH_API_URL = "http://private-api:8000";
  process.env.API_BEARER_TOKEN = "fixture-service-token-32-characters";
  globalThis.fetch = async (target, init) => {
    assert.equal(
      String(target),
      "http://private-api:8000/research-runs/owned-run/events",
    );
    assert.equal(init.headers.get("last-event-id"), "41");
    assert.equal(init.headers.get("authorization"), "Bearer fixture-access");
    return new Response("id: 42\nevent: evidence.updated\ndata: {}\n\n", {
      headers: {
        "content-type": "text/event-stream",
        "cache-control": "no-cache",
      },
    });
  };
  const response = await GET(
    request("GET", {
      accept: "text/event-stream",
      authorization: "Bearer fixture-access",
      "last-event-id": "41",
    }),
    {
      params: Promise.resolve({
        path: ["research-runs", "owned-run", "events"],
      }),
    },
  );
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("content-type"), "text/event-stream");
  assert.equal(
    await response.text(),
    "id: 42\nevent: evidence.updated\ndata: {}\n\n",
  );
});
