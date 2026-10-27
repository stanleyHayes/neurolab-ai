"""FastAPI surface for datasets, bounded research runs, events and artifacts."""

from __future__ import annotations

import asyncio
import hmac
import json
import os
import time
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .agent import ResearchAgent
from .auth import (
    AuthenticationError,
    assert_production_auth_config,
    decode_access_token,
    hash_password,
    issue_access_token,
    keyed_hash,
    new_csrf_token,
    new_refresh_token,
    new_session_expiry,
    normalize_email,
    session_now,
    verify_keyed_hash,
    verify_password,
)
from .evaluation import write_evaluation
from .ghana import load_ghana
from .planner import refine_plan, validate_execution_plan
from .providers import (
    ModelContextLimitError,
    ModelProviderError,
    OpenAICompatibleAdapter,
    adapter_status,
)
from .research_context import (
    MAX_RESEARCH_REQUEST_BYTES,
    DraftSaveRequest,
    ResearchConfiguration,
    ResearchDraft,
    ResearchPlanRefinementRequest,
    ResearchRunRequest,
    build_deterministic_plan,
    objective_digest,
    validate_objective,
)
from .science import dataset_profile
from .store import RunStore
from .tools import ToolValidationError, execute_tool

HEALTH_PATH = "/health"
AUTH_REQUIRED = "Authentication is required"
CSRF_FAILED = "CSRF verification failed"


HTTP_ERROR_RESPONSES = {
    400: {"description": "Malformed request"},
    401: {"description": "Authentication required"},
    403: {"description": "Request not authorized or CSRF verification failed"},
    404: {"description": "Resource not found"},
    409: {"description": "Conflicting resource state"},
    413: {"description": "Request body too large"},
    422: {"description": "Validation or scientific applicability error"},
    429: {"description": "Rate or active-run budget exceeded"},
    502: {"description": "Invalid provider response"},
    503: {"description": "Service or model unavailable"},
}

assert_production_auth_config()

ROOT = Path(__file__).resolve().parents[1]
DATASET = load_ghana(ROOT)
MANIFEST = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
_database_url = os.getenv("DATABASE_URL", "postgresql:///neurolab")
STORE = RunStore(_database_url)

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
if APP_ENV not in {"development", "test", "production"}:
    raise RuntimeError("APP_ENV must be development, test, or production")

API_BEARER_TOKEN = os.getenv("API_BEARER_TOKEN", "").strip()
if APP_ENV == "production" and len(API_BEARER_TOKEN) < 32:
    raise RuntimeError("Production requires an API_BEARER_TOKEN of at least 32 characters")

_raw_allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [
    host.strip()
    for host in (_raw_allowed_hosts or "localhost,127.0.0.1,testserver").split(",")
    if host.strip()
]
if APP_ENV == "production" and (
    not _raw_allowed_hosts or not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS
):
    raise RuntimeError("Production requires explicit ALLOWED_HOSTS; wildcard hosts are unsafe")


class RequestSecurityMiddleware:
    """Bound request memory/volume and add baseline security response headers.

    Rate limits are per-process and keyed only on the ASGI peer address. Deployments
    behind a gateway still need edge/shared-store limits and a private API network.
    """

    EXPENSIVE_POST_PATHS = {
        "/research-runs",
        "/research-runs/legacy",
        "/research-objectives/refine",
        "/research-tools/execute",
        "/evaluations/baselines",
    }
    AUTH_POST_PATHS = {"/auth/register", "/auth/login", "/auth/refresh", "/auth/change-password"}

    def __init__(
        self,
        app,
        *,
        max_body_bytes: int = MAX_RESEARCH_REQUEST_BYTES,
        requests_per_minute: int = 120,
        expensive_requests_per_minute: int = 10,
        window_seconds: int = 60,
        bearer_token: str = API_BEARER_TOKEN,
        require_auth: bool = APP_ENV == "production",
    ):
        self.app = app
        self.max_body_bytes = max_body_bytes
        self.requests_per_minute = requests_per_minute
        self.expensive_requests_per_minute = expensive_requests_per_minute
        self.window_seconds = window_seconds
        self.bearer_token = bearer_token
        self.require_auth = require_auth
        self._buckets: dict[tuple[str, str], tuple[int, int, float]] = {}
        self._last_cleanup = time.monotonic()

    @staticmethod
    async def _respond(send, status: int, payload: dict[str, str], extra_headers=()):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
            (b"cache-control", b"no-store"),
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"referrer-policy", b"strict-origin-when-cross-origin"),
        ]
        headers.extend(extra_headers)
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})

    def _allow_request(self, peer: str, bucket_name: str, limit: int, now: float) -> bool:
        window = int(now // self.window_seconds)
        key = (peer, bucket_name)
        current_window, count, _last_seen = self._buckets.get(key, (window, 0, now))
        if current_window != window:
            count = 0
        if count >= limit:
            return False
        if key not in self._buckets and len(self._buckets) >= 10_000:
            self._buckets = {
                item_key: item
                for item_key, item in self._buckets.items()
                if item[2] >= now - self.window_seconds
            }
            if len(self._buckets) >= 10_000:
                for stale_key in list(self._buckets)[: len(self._buckets) // 2]:
                    self._buckets.pop(stale_key, None)
        self._buckets[key] = (window, count + 1, now)
        if now - self._last_cleanup >= self.window_seconds:
            self._buckets = {
                item_key: item
                for item_key, item in self._buckets.items()
                if item[2] >= now - self.window_seconds
            }
            self._last_cleanup = now
        return True

    async def _reject_service_auth(self, path, request_headers, send):
        if self.require_auth and path != HEALTH_PATH:
            service_credential = request_headers.get(b"x-neurolab-service-token", b"").decode(
                "latin-1", errors="ignore"
            )
            if not self.bearer_token or not hmac.compare_digest(
                service_credential, self.bearer_token
            ):
                await self._respond(
                    send,
                    401,
                    {"detail": "Valid service authentication is required"},
                )
                return True

        return False

    async def _reject_rate_or_docs(self, method, path, peer, now, send):
        if path != HEALTH_PATH and not self._allow_request(
            peer, "all", self.requests_per_minute, now
        ):
            await self._respond(
                send,
                429,
                {"detail": "Request rate limit exceeded"},
                ((b"retry-after", str(self.window_seconds).encode("ascii")),),
            )
            return True

        if (
            method == "POST"
            and path in self.AUTH_POST_PATHS
            and not self._allow_request(peer, "auth", 30, now)
        ):
            await self._respond(
                send,
                429,
                {"detail": "Authentication request rate limit exceeded"},
                ((b"retry-after", str(self.window_seconds).encode("ascii")),),
            )
            return True

        if APP_ENV == "production" and path in {"/docs", "/redoc", "/openapi.json"}:
            await self._respond(send, 404, {"detail": "Not Found"})
            return True

        if (
            path != HEALTH_PATH
            and method == "POST"
            and path in self.EXPENSIVE_POST_PATHS
            and not self._allow_request(peer, "expensive", self.expensive_requests_per_minute, now)
        ):
            await self._respond(
                send,
                429,
                {"detail": "Analysis request rate limit exceeded"},
                ((b"retry-after", str(self.window_seconds).encode("ascii")),),
            )
            return True

        return False

    async def _reject_content_length(self, request_headers, send):
        content_length = request_headers.get(b"content-length")
        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError:
                await self._respond(send, 400, {"detail": "Invalid Content-Length"})
                return True
            if declared_length < 0:
                await self._respond(send, 400, {"detail": "Invalid Content-Length"})
                return True
            if declared_length > self.max_body_bytes:
                await self._respond(send, 413, {"detail": "Request body exceeds the size limit"})
                return True

        return False

    async def _read_request_body(self, method, request_headers, receive, send):
        if await self._reject_content_length(request_headers, send):
            return None

        replay_messages = []
        if method not in {"GET", "HEAD", "OPTIONS"}:
            total_bytes = 0
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return None
                chunk = message.get("body", b"")
                total_bytes += len(chunk)
                if total_bytes > self.max_body_bytes:
                    await self._respond(
                        send, 413, {"detail": "Request body exceeds the size limit"}
                    )
                    return None
                replay_messages.append(message)
                if not message.get("more_body", False):
                    break

        return replay_messages

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET").upper()
        path = scope.get("path", "/")
        peer = (scope.get("client") or ("unknown", 0))[0]
        now = time.monotonic()
        request_headers = {key.lower(): value for key, value in scope.get("headers", [])}

        if await self._reject_rate_or_docs(method, path, peer, now, send):
            return
        if await self._reject_service_auth(path, request_headers, send):
            return
        replay_messages = await self._read_request_body(method, request_headers, receive, send)
        if replay_messages is None:
            return

        async def replay_receive():
            if replay_messages:
                return replay_messages.pop(0)
            return await receive()

        async def secure_send(message):
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                present = {name.lower() for name, _ in response_headers}
                security_headers = (
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                )
                response_headers.extend(
                    (name, value) for name, value in security_headers if name not in present
                )
                if (
                    APP_ENV == "production"
                    and scope.get("scheme") == "https"
                    and b"strict-transport-security" not in present
                ):
                    response_headers.append(
                        (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
                    )
                message["headers"] = response_headers
            await send(message)

        await self.app(scope, replay_receive, secure_send)


app = FastAPI(
    title="NeuroLab AI Research API",
    version="0.1.0",
    description=(
        "Reproducible observational research tools. Replay mode is a deterministic local baseline, "
        "not Meta model inference."
    ),
    docs_url=None if APP_ENV == "production" else "/docs",
    redoc_url=None if APP_ENV == "production" else "/redoc",
    openapi_url=None if APP_ENV == "production" else "/openapi.json",
)
app.add_middleware(RequestSecurityMiddleware)
if APP_ENV == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)


class ToolCallRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trace_id: str = Field(min_length=1, max_length=128)
    hypothesis_id: str = Field(min_length=1, max_length=128)
    dataset_id: str
    action: str
    parameters: dict[str, Any] = Field(default_factory=dict)


DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
PasswordValue = Annotated[str, StringConstraints(min_length=12, max_length=1024)]


def _valid_email(value: str) -> bool:
    if len(value) > 254 or value.count("@") != 1 or any(char.isspace() for char in value):
        return False
    local, domain = value.split("@")
    return bool(
        local
        and domain
        and "." in domain
        and not domain.startswith(".")
        and not domain.endswith(".")
    )


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=254)]
    password: PasswordValue
    display_name: DisplayName
    invite_code: str | None = Field(default=None, max_length=256)

    @model_validator(mode="after")
    def validate_email(self):
        if not _valid_email(self.email):
            raise ValueError("Enter a valid email address")
        return self


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=254)]
    password: Annotated[str, StringConstraints(min_length=1, max_length=1024)]


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: DisplayName


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: Annotated[str, StringConstraints(min_length=1, max_length=1024)]
    new_password: PasswordValue


def _current_user(request: Request) -> dict[str, Any]:
    authorization = request.headers.get("authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail=AUTH_REQUIRED)
    try:
        claims = decode_access_token(authorization.removeprefix("Bearer "))
    except AuthenticationError:
        raise HTTPException(status_code=401, detail=AUTH_REQUIRED) from None
    user = STORE.get_user(claims["sub"])
    if (
        user is None
        or not user["is_active"]
        or not STORE.get_active_auth_session(claims["sid"], user["user_id"], session_now())
    ):
        raise HTTPException(status_code=401, detail=AUTH_REQUIRED)
    return {**user, "session_id": claims["sid"]}


UserDependency = Annotated[dict[str, Any], Depends(_current_user)]


def _issue_auth_response(user: dict[str, Any], session_id: str) -> dict[str, Any]:
    return {
        "access_token": issue_access_token(user["user_id"], session_id),
        "token_type": "bearer",
        "expires_in": 720,
        "user": user,
    }


def _set_auth_cookies(response: Response, refresh_token: str, csrf_token: str) -> None:
    production = APP_ENV == "production"
    response.set_cookie(
        "neurolab_refresh",
        refresh_token,
        max_age=14 * 24 * 60 * 60,
        httponly=True,
        secure=production,
        samesite="lax",
        path="/api/auth",
    )
    response.set_cookie(
        "neurolab_csrf",
        csrf_token,
        max_age=14 * 24 * 60 * 60,
        # Public CSRF nonce for double-submit; the separate refresh cookie is HttpOnly.
        httponly=False,
        secure=production,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        "neurolab_refresh", path="/api/auth", secure=APP_ENV == "production", samesite="lax"
    )
    response.delete_cookie(
        "neurolab_csrf", path="/", secure=APP_ENV == "production", samesite="lax"
    )


def _require_csrf(request: Request, refresh_token: str) -> None:
    cookie = request.cookies.get("neurolab_csrf", "")
    header = request.headers.get("x-csrf-token", "")
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise HTTPException(status_code=403, detail=CSRF_FAILED)
    stored_hash = STORE.get_csrf_hash(keyed_hash(refresh_token))
    if stored_hash is None or not verify_keyed_hash(cookie, stored_hash):
        raise HTTPException(status_code=403, detail=CSRF_FAILED)


def _require_double_submit_csrf(request: Request) -> None:
    cookie = request.cookies.get("neurolab_csrf", "")
    header = request.headers.get("x-csrf-token", "")
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise HTTPException(status_code=403, detail=CSRF_FAILED)


@app.get(
    HEALTH_PATH,
    responses=HTTP_ERROR_RESPONSES,
)
def health() -> dict[str, Any]:
    if APP_ENV == "production":
        return {"status": "ok"}
    provider = adapter_status()
    return {
        "status": "ok",
        "manifest_file_count": len(MANIFEST),
        "dataset_hash": DATASET.source_sha256,
        "model_adapter": provider,
        "model_inference_live": provider["enabled_for_runs"],
        "default_run_mode": "replay",
    }


def _registration_enabled(invite_code: str | None) -> bool:
    configured = os.getenv("AUTH_INVITE_CODE", "").strip()
    if not configured:
        return False
    return bool(invite_code) and hmac.compare_digest(invite_code, configured)


def _auth_response_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


def _create_login_session(user: dict[str, Any], response: Response) -> dict[str, Any]:
    session_id = str(uuid.uuid4())
    refresh_token = new_refresh_token()
    csrf_token = new_csrf_token()
    STORE.create_auth_session(
        session_id=session_id,
        user_id=user["user_id"],
        refresh_token_hash=keyed_hash(refresh_token),
        csrf_token_hash=keyed_hash(csrf_token),
        family_id=str(uuid.uuid4()),
        expires_at=new_session_expiry(),
    )
    _set_auth_cookies(response, refresh_token, csrf_token)
    return _issue_auth_response(user, session_id)


def _check_auth_attempt(identifier: str) -> str:
    now = session_now()
    key = keyed_hash(normalize_email(identifier))
    blocked = STORE.auth_rate_limit_seconds(key, now)
    if blocked:
        raise HTTPException(
            status_code=429,
            detail="Authentication temporarily unavailable; try again later",
            headers={"Retry-After": str(blocked)},
        )
    return key


@app.post(
    "/auth/register",
    status_code=201,
    responses=HTTP_ERROR_RESPONSES,
)
def register(payload: RegisterRequest, request: Request, response: Response) -> dict[str, Any]:
    _auth_response_headers(response)
    _require_double_submit_csrf(request)
    if not _registration_enabled(payload.invite_code):
        raise HTTPException(status_code=403, detail="Registration is currently invite-only")
    email = normalize_email(payload.email)
    if not _valid_email(email):
        raise HTTPException(status_code=422, detail="Enter a valid email address")
    try:
        user = STORE.create_user(email, hash_password(payload.password), payload.display_name)
    except Exception as exc:
        # Avoid reflecting DB details or distinguishing an email already in use.
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            raise HTTPException(
                status_code=409, detail="Unable to create account with those details"
            ) from None
        raise
    return _create_login_session(user, response)


@app.post(
    "/auth/login",
    responses=HTTP_ERROR_RESPONSES,
)
def login(payload: LoginRequest, request: Request, response: Response) -> dict[str, Any]:
    _auth_response_headers(response)
    _require_double_submit_csrf(request)
    email = normalize_email(payload.email)
    attempt_key = _check_auth_attempt(email)
    blocked_seconds = STORE.login_rate_limit_seconds(attempt_key, session_now())
    if blocked_seconds:
        raise HTTPException(
            status_code=429,
            detail="Authentication temporarily unavailable; try again later",
            headers={"Retry-After": str(blocked_seconds)},
        )
    user = STORE.get_user_by_email(email)
    password_hash = STORE.get_password_hash(user["user_id"]) if user else None
    if not user or not password_hash or not verify_password(password_hash, payload.password):
        STORE.record_login_failure(attempt_key, session_now())
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    STORE.clear_login_failures(attempt_key)
    return _create_login_session(user, response)


@app.post(
    "/auth/refresh",
    responses=HTTP_ERROR_RESPONSES,
)
def refresh_session(request: Request, response: Response) -> dict[str, Any]:
    _auth_response_headers(response)
    old_token = request.cookies.get("neurolab_refresh", "")
    if not old_token:
        raise HTTPException(status_code=401, detail="Authentication session is required")
    _require_csrf(request, old_token)
    new_token = new_refresh_token()
    csrf_token = new_csrf_token()
    now = session_now()
    state, result = STORE.rotate_auth_session(
        old_refresh_hash=keyed_hash(old_token),
        new_session_id=str(uuid.uuid4()),
        new_refresh_hash=keyed_hash(new_token),
        new_csrf_hash=keyed_hash(csrf_token),
        new_expires_at=new_session_expiry(),
        now=now,
    )
    if state != "rotated" or result is None:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Authentication session is invalid")
    _set_auth_cookies(response, new_token, csrf_token)
    return _issue_auth_response(result["user"], result["session_id"])


@app.post(
    "/auth/logout",
    status_code=204,
    responses=HTTP_ERROR_RESPONSES,
)
def logout(request: Request, response: Response, user: UserDependency) -> Response:
    _auth_response_headers(response)
    STORE.revoke_auth_session(user["session_id"], user["user_id"], session_now())
    _clear_auth_cookies(response)
    response.delete_cookie(
        "neurolab_csrf", path="/", secure=APP_ENV == "production", samesite="lax"
    )
    response.status_code = 204
    return response


@app.post(
    "/auth/logout-all",
    status_code=204,
    responses=HTTP_ERROR_RESPONSES,
)
def logout_all(response: Response, user: UserDependency) -> Response:
    _auth_response_headers(response)
    STORE.revoke_all_auth_sessions(user["user_id"], session_now())
    _clear_auth_cookies(response)
    response.delete_cookie(
        "neurolab_csrf", path="/", secure=APP_ENV == "production", samesite="lax"
    )
    response.status_code = 204
    return response


@app.get(
    "/auth/me",
    responses=HTTP_ERROR_RESPONSES,
)
def current_profile(response: Response, user: UserDependency) -> dict[str, Any]:
    _auth_response_headers(response)
    return {key: value for key, value in user.items() if key != "session_id"}


@app.get(
    "/research-draft",
    responses=HTTP_ERROR_RESPONSES,
)
def get_research_draft(user: UserDependency) -> dict[str, Any]:
    stored = STORE.get_research_draft(user["user_id"])
    if stored is not None:
        return stored
    return {"revision": 0, "draft": ResearchDraft().model_dump(mode="json"), "updated_at": None}


@app.put(
    "/research-draft",
    responses=HTTP_ERROR_RESPONSES,
)
def save_research_draft(payload: DraftSaveRequest, user: UserDependency) -> dict[str, Any]:
    if payload.draft.objective:
        validate_objective(payload.draft.objective)
    result = STORE.save_research_draft(
        user["user_id"], payload.expected_revision, payload.draft.model_dump(mode="json")
    )
    if result is None:
        raise HTTPException(
            status_code=409, detail="Draft changed in another session. Reload before saving."
        )
    return result


@app.patch(
    "/auth/me",
    responses=HTTP_ERROR_RESPONSES,
)
def update_profile(
    request: ProfileUpdateRequest,
    response: Response,
    user: UserDependency,
) -> dict[str, Any]:
    _auth_response_headers(response)
    updated = STORE.update_profile(user["user_id"], request.display_name)
    if updated is None:
        raise HTTPException(status_code=401, detail=AUTH_REQUIRED)
    return updated


@app.post(
    "/auth/change-password",
    status_code=204,
    responses=HTTP_ERROR_RESPONSES,
)
def change_password(
    request: ChangePasswordRequest,
    response: Response,
    user: UserDependency,
) -> Response:
    _auth_response_headers(response)
    password_hash = STORE.get_password_hash(user["user_id"])
    if not password_hash or not verify_password(password_hash, request.current_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    if request.current_password == request.new_password:
        raise HTTPException(status_code=422, detail="Choose a different password")
    STORE.change_password(user["user_id"], hash_password(request.new_password), user["session_id"])
    response.status_code = 204
    return response


@app.get(
    "/auth/csrf",
    responses=HTTP_ERROR_RESPONSES,
)
def auth_csrf(request: Request, response: Response) -> dict[str, bool]:
    """Issue a short-lived anonymous double-submit token for login/register CSRF."""
    _auth_response_headers(response)
    token = new_csrf_token()
    response.set_cookie(
        "neurolab_csrf",
        token,
        max_age=10 * 60,
        # Public CSRF nonce for double-submit; the separate refresh cookie is HttpOnly.
        httponly=False,
        secure=APP_ENV == "production",
        samesite="lax",
        path="/",
    )
    return {"csrf_ready": True}


@app.get(
    "/datasets",
    responses=HTTP_ERROR_RESPONSES,
)
def datasets(user: UserDependency) -> list[dict[str, Any]]:
    return [
        {
            "dataset_id": "ghana_combined",
            "source_file": DATASET.source_file,
            "source_sha256": DATASET.source_sha256,
            "row_count": DATASET.source_row_count,
            "citation": "Abu et al. (2026), DOI 10.5281/zenodo.22666201",
            "license": "CC BY 4.0",
            "analysis_enabled": True,
            "scope": "observational field-trial records; not a field recommendation",
        }
    ]


@app.get(
    "/datasets/{dataset_id}/profile",
    responses=HTTP_ERROR_RESPONSES,
)
def dataset_profile_endpoint(dataset_id: str, user: UserDependency) -> dict[str, Any]:
    if dataset_id != "ghana_combined":
        raise HTTPException(status_code=404, detail="Dataset is not available for this service")
    return dataset_profile(DATASET)


@app.post(
    "/research-tools/execute",
    responses=HTTP_ERROR_RESPONSES,
)
def research_tool_execute(request: ToolCallRequest, user: UserDependency) -> dict[str, Any]:
    try:
        return execute_tool(request.model_dump(), DATASET, seed=2026)
    except ToolValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _execute_run(request: ResearchRunRequest, run_id: str) -> None:
    try:
        started = time.monotonic()
        configuration = request.configuration or ResearchConfiguration(
            dataset_id=request.dataset_id, constraints=request.constraints
        )
        adapter = OpenAICompatibleAdapter.from_environment() if request.mode == "meta" else None
        plan = request.plan or build_deterministic_plan(request.objective, configuration)
        if (
            adapter
            and request.plan is None
            and configuration.autonomy_preferences.auto_plan_with_meta
        ):
            STORE.add_event(
                run_id,
                "planning.requested",
                {
                    "provider": adapter.provider,
                    "model_id": adapter.model_id,
                    "objective_sha256": objective_digest(request.objective),
                },
            )
            plan = refine_plan(
                request.objective,
                configuration,
                adapter,
                timeout=min(45, configuration.constraints.max_seconds),
            )
            STORE.update_research_plan(run_id, plan.model_dump(mode="json"))
            STORE.add_event(
                run_id,
                "planning.completed",
                {
                    "provider": adapter.provider,
                    "model_id": adapter.model_id,
                    "task_count": len(plan.tasks),
                    "unsupported_requirements": plan.unsupported_requirements,
                },
            )
        remaining = configuration.constraints.max_seconds - (time.monotonic() - started)
        if remaining <= 0:
            raise TimeoutError("Research planning exhausted the run time budget before analysis")
        agent = ResearchAgent(
            DATASET,
            STORE,
            max_steps=configuration.constraints.max_steps,
            max_tool_calls=configuration.constraints.max_tool_calls,
            max_wall_time=remaining,
            mode=request.mode,
            model_adapter=adapter,
            configuration=configuration,
            research_plan=plan,
        )
        agent.run(request.objective, seed=request.seed, run_id=run_id)
    except Exception as exc:
        sanitized = (
            str(exc)
            if isinstance(exc, (ModelProviderError, TimeoutError, ValueError))
            else (
                "Unexpected research execution error; inspect server logs without exposing secrets."
            )
        )
        STORE.add_event(
            run_id,
            "run.failed",
            {
                "error_type": type(exc).__name__,
                "message": sanitized[:200],
                "retryable": isinstance(exc, ModelProviderError),
            },
        )


@app.post(
    "/research-runs",
    status_code=202,
    responses=HTTP_ERROR_RESPONSES,
)
def create_research_run(
    request: ResearchRunRequest,
    background_tasks: BackgroundTasks,
    user: UserDependency,
) -> dict[str, Any]:
    try:
        validate_objective(request.objective)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    configuration = request.configuration or ResearchConfiguration(
        dataset_id=request.dataset_id, constraints=request.constraints
    )
    if configuration.dataset_id != "ghana_combined":
        raise HTTPException(
            status_code=422, detail="Only Ghana combined is enabled for actual analysis execution."
        )
    if request.plan is not None:
        try:
            validate_execution_plan(request.plan, request.objective)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        plan = request.plan
    else:
        plan = build_deterministic_plan(request.objective, configuration)
    if request.mode == "meta" and not adapter_status()["enabled_for_runs"]:
        raise HTTPException(
            status_code=503,
            detail="Meta runs require a configured provider and META_MODEL_VERIFIED=true after a successful smoke test.",
        )
    if not request.objective.strip():
        raise HTTPException(status_code=422, detail="objective must contain non-whitespace text")
    if STORE.count_active_runs(user["user_id"]) >= 2:
        raise HTTPException(
            status_code=429, detail="You already have the maximum number of active runs"
        )
    run_id = STORE.create_run(
        configuration.dataset_id,
        request.objective,
        DATASET.source_sha256,
        request.seed,
        owner_user_id=user["user_id"],
        research_configuration=configuration.model_dump(mode="json"),
        research_plan=plan.model_dump(mode="json"),
    )
    STORE.add_event(
        run_id,
        "request.accepted",
        {
            "mode": request.mode,
            "max_steps": configuration.constraints.max_steps,
            "max_tool_calls": configuration.constraints.max_tool_calls,
            "objective_characters": len(request.objective),
            "objective_sha256": objective_digest(request.objective),
        },
    )
    STORE.set_stage(
        run_id, "PLANNING", "Validated structured research plan and exact original objective"
    )
    STORE.set_stage(run_id, "QUEUED", "Run accepted and queued for bounded execution")
    background_tasks.add_task(_execute_run, request, run_id)
    report = None
    return {
        "run_id": run_id,
        "status": "QUEUED",
        "mode": request.mode,
        "report": report,
    }


@app.post(
    "/research-runs/legacy",
    status_code=202,
    responses=HTTP_ERROR_RESPONSES,
)
def create_legacy_research_run(
    request: ResearchRunRequest,
    background_tasks: BackgroundTasks,
    user: UserDependency,
) -> dict[str, Any]:
    plan = build_deterministic_plan(
        request.objective,
        ResearchConfiguration(dataset_id=request.dataset_id, constraints=request.constraints),
    )
    extended = ResearchRunRequest(
        objective=request.objective,
        configuration=ResearchConfiguration(
            dataset_id=request.dataset_id, constraints=request.constraints
        ),
        plan=plan,
        seed=request.seed,
        mode=request.mode,
    )
    return create_research_run(extended, background_tasks, user)


@app.post(
    "/research-objectives/refine",
    responses=HTTP_ERROR_RESPONSES,
)
def refine_research_objective(
    payload: ResearchPlanRefinementRequest,
    user: UserDependency,
) -> dict[str, Any]:
    """Return a proposal only; the submitted objective is never overwritten."""
    try:
        validate_objective(payload.objective)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not adapter_status()["enabled_for_runs"]:
        raise HTTPException(
            status_code=503, detail="Meta refinement requires a verified live Meta adapter."
        )
    adapter = OpenAICompatibleAdapter.from_environment()
    try:
        plan = refine_plan(payload.objective, payload.configuration, adapter, timeout=45)
    except ModelContextLimitError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ModelProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail="Meta returned an invalid structured research plan."
        ) from exc
    return {"original_objective": payload.objective, "plan": plan.model_dump(mode="json")}


def _run_or_404(run_id: str, owner_user_id: str) -> dict[str, Any]:
    run = STORE.get_run(run_id, owner_user_id=owner_user_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run


@app.get(
    "/research-runs/{run_id}",
    responses=HTTP_ERROR_RESPONSES,
)
def get_research_run(run_id: str, user: UserDependency) -> dict[str, Any]:
    return _run_or_404(run_id, user["user_id"])


@app.get(
    "/research-runs",
    responses=HTTP_ERROR_RESPONSES,
)
def list_research_runs(user: UserDependency, limit: int = 20) -> list[dict[str, Any]]:
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    return STORE.list_runs(limit, owner_user_id=user["user_id"])


def _active_stream_run(run_id, user):
    run = STORE.get_run(run_id, owner_user_id=user["user_id"])
    session = STORE.get_active_auth_session(user["session_id"], user["user_id"], session_now())
    return run if session else None


def _terminal_run(run):
    return run is None or run["status"] in {
        "COMPLETE",
        "PARTIAL",
        "FAILED",
        "CANCELLED",
        "TIMED_OUT",
    }


async def _stream_run_events(run_id, request, user, after):
    cursor = after
    while not await request.is_disconnected():
        run = _active_stream_run(run_id, user)
        if run is None:
            break
        events = STORE.list_events(run_id, after_sequence=cursor)
        for event in events:
            cursor = event["sequence"]
            yield f"id: {cursor}\nevent: {event['event_type']}\ndata: {json.dumps(event, separators=(',', ':'))}\n\n"
        if _terminal_run(STORE.get_run(run_id, owner_user_id=user["user_id"])):
            break
        if not events:
            yield ": keep-alive\n\n"
        await asyncio.sleep(0.25)


@app.get(
    "/research-runs/{run_id}/events",
    responses=HTTP_ERROR_RESPONSES,
)
async def research_run_events(
    run_id: str,
    request: Request,
    user: UserDependency,
    after: int = 0,
) -> StreamingResponse:
    _run_or_404(run_id, user["user_id"])
    last_event_id = request.headers.get("last-event-id")
    if last_event_id:
        try:
            after = max(after, int(last_event_id))
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Last-Event-ID must be an integer sequence"
            ) from None

    return StreamingResponse(
        _stream_run_events(run_id, request, user, after),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "X-Event-Stream-Mode": "durable-cursor-replay",
        },
    )


@app.get(
    "/research-runs/{run_id}/artifacts",
    responses=HTTP_ERROR_RESPONSES,
)
def research_run_artifacts(run_id: str, user: UserDependency) -> list[dict[str, Any]]:
    _run_or_404(run_id, user["user_id"])
    return STORE.list_artifacts(run_id)


@app.get(
    "/research-runs/{run_id}/report",
    responses=HTTP_ERROR_RESPONSES,
)
def research_run_report(run_id: str, user: UserDependency) -> dict[str, Any]:
    run = _run_or_404(run_id, user["user_id"])
    if run["report"] is None:
        raise HTTPException(status_code=409, detail="Report is not ready")
    return run["report"]


@app.post(
    "/evaluations/baselines",
    responses=HTTP_ERROR_RESPONSES,
)
def run_baseline_evaluation(
    user: UserDependency, seed: int = 2026, budget: int = 2
) -> dict[str, Any]:
    if not 1 <= budget <= 10:
        raise HTTPException(status_code=422, detail="budget must be between 1 and 10")
    return write_evaluation(DATASET, ROOT / "eval", seed=seed, budget=budget)


@app.post(
    "/research-runs/{run_id}/cancel",
    status_code=202,
    responses=HTTP_ERROR_RESPONSES,
)
def cancel_research_run(run_id: str, user: UserDependency) -> dict[str, str]:
    run = _run_or_404(run_id, user["user_id"])
    if run["status"] == "COMPLETE":
        raise HTTPException(
            status_code=409, detail="Run is already complete and cannot be cancelled"
        )
    if run["status"] in {"PARTIAL", "FAILED", "CANCELLED", "TIMED_OUT"}:
        raise HTTPException(status_code=409, detail="Run is already terminal")
    STORE.request_cancel(run_id)
    event = STORE.add_event(
        run_id,
        "run.cancel_requested",
        {"note": "Cancellation will be applied at the next safe boundary"},
    )
    if run["status"] in {"CREATED", "QUEUED"}:
        STORE.add_event(run_id, "run.cancelled", {"reason": "cancelled_before_execution"})
    return {"run_id": run_id, "status": "cancel_requested", "event_id": event["event_id"]}
