import { isIP } from "node:net";
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const maxDuration = 300;

// Research objectives are capped at 20k Unicode characters; JSON, config and
// UTF-8 expansion require headroom while remaining bounded well below 1 MiB.
const MAX_REQUEST_BYTES = 262_144;

type RouteContext = { params: Promise<{ path: string[] }> };

function isSameOrigin(request: NextRequest, origin: string): boolean {
  try {
    const suppliedOrigin = new URL(origin);
    if (suppliedOrigin.origin === request.nextUrl.origin) return true;

    // Next's normalized URL can differ from the browser-facing authority when
    // development is bound to 127.0.0.1. Use the incoming Host header rather
    // than trusting caller-controlled forwarded headers.
    const host = request.headers.get("host");
    const protocol = request.nextUrl.protocol.replace(/:$/, "");
    if (!host || !["http", "https"].includes(protocol.toLowerCase()))
      return false;

    return suppliedOrigin.origin === new URL(`${protocol}://${host}`).origin;
  } catch {
    return false;
  }
}

async function readBoundedBody(
  request: NextRequest,
): Promise<ArrayBuffer | null> {
  if (!request.body) return new ArrayBuffer(0);
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let totalBytes = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      totalBytes += value.byteLength;
      if (totalBytes > MAX_REQUEST_BYTES) {
        await reader.cancel();
        return null;
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const body = new Uint8Array(totalBytes);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body.buffer;
}

function proxyError(detail: string, status: number): Response {
  return Response.json(
    { detail },
    { status, headers: { "cache-control": "no-store" } },
  );
}

function isCrossOriginMutation(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  if (origin) return !isSameOrigin(request, origin);
  const site = request.headers.get("sec-fetch-site");
  return Boolean(site && site !== "same-origin" && site !== "none");
}

function upstreamHeaders(
  request: NextRequest,
  serviceToken: string | undefined,
): Headers {
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");
  const lastEventId = request.headers.get("last-event-id");
  const authorization = request.headers.get("authorization");
  const csrfToken = request.headers.get("x-csrf-token");
  const cookie = request.headers.get("cookie");
  if (contentType) headers.set("content-type", contentType);
  if (accept) headers.set("accept", accept);
  if (lastEventId) headers.set("last-event-id", lastEventId);
  if (authorization) headers.set("authorization", authorization);
  if (csrfToken) headers.set("x-csrf-token", csrfToken);
  if (cookie) {
    const authCookies = cookie
      .split(";")
      .map((value) => value.trim())
      .filter(
        (value) =>
          value.startsWith("neurolab_refresh=") ||
          value.startsWith("neurolab_csrf="),
      );
    if (authCookies.length) headers.set("cookie", authCookies.join("; "));
  }
  const trustedIpHeader =
    process.env.NEUROLAB_TRUSTED_CLIENT_IP_HEADER?.trim().toLowerCase();
  if (trustedIpHeader && /^[a-z][a-z0-9-]{0,63}$/.test(trustedIpHeader)) {
    const suppliedIp = request.headers.get(trustedIpHeader)?.trim();
    if (suppliedIp && isIP(suppliedIp) && !suppliedIp.includes("%"))
      headers.set("x-neurolab-client-ip", suppliedIp);
  }
  if (serviceToken) headers.set("x-neurolab-service-token", serviceToken);
  return headers;
}

async function mutationBody(
  request: NextRequest,
): Promise<ArrayBuffer | Response> {
  const rawLength = request.headers.get("content-length");
  const length = rawLength === null ? undefined : Number(rawLength);
  if (length !== undefined && (!Number.isSafeInteger(length) || length < 0)) {
    return proxyError("Invalid Content-Length.", 400);
  }
  if (length !== undefined && length > MAX_REQUEST_BYTES) {
    return proxyError("Request body exceeds the size limit.", 413);
  }
  const body = await readBoundedBody(request);
  return body ?? proxyError("Request body exceeds the size limit.", 413);
}

function downstreamHeaders(response: Response): Headers {
  const responseHeaders = new Headers();
  for (const name of [
    "content-type",
    "cache-control",
    "x-event-stream-mode",
    "x-accel-buffering",
    "retry-after",
    "www-authenticate",
  ]) {
    const value = response.headers.get(name);
    if (value) responseHeaders.set(name, value);
  }
  for (const value of response.headers.getSetCookie())
    responseHeaders.append("set-cookie", value);
  return responseHeaders;
}

async function forward(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  const { path } = await context.params;
  const configuredUpstream = process.env.RESEARCH_API_URL;
  const upstream = configuredUpstream ?? "http://127.0.0.1:8000";
  const serviceToken = process.env.API_BEARER_TOKEN;
  if (
    process.env.NODE_ENV === "production" &&
    (!configuredUpstream || !serviceToken || serviceToken.length < 32)
  ) {
    return Response.json(
      {
        detail:
          "Research API proxy is missing its production service configuration.",
      },
      { status: 503, headers: { "cache-control": "no-store" } },
    );
  }

  const isMutation =
    request.method !== "GET" &&
    request.method !== "HEAD" &&
    request.method !== "OPTIONS";
  if (isMutation && isCrossOriginMutation(request)) {
    return proxyError(
      "Cross-origin state-changing requests are not allowed.",
      403,
    );
  }

  const target = new URL(
    `${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`,
    `${upstream.replace(/\/$/, "")}/`,
  );
  const headers = upstreamHeaders(request, serviceToken);

  try {
    const body = isMutation ? await mutationBody(request) : undefined;
    if (body instanceof Response) return body;

    const response = await fetch(target, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      redirect: "manual",
      signal: request.signal,
    });
    const responseHeaders = downstreamHeaders(response);
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch {
    return Response.json(
      {
        detail:
          "Research API is unavailable. Start FastAPI on the configured RESEARCH_API_URL.",
      },
      { status: 502 },
    );
  }
}

export const GET = forward;
export const POST = forward;
export const DELETE = forward;
export const PUT = forward;
export const PATCH = forward;
