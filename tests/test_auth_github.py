from urllib.parse import parse_qs, urlparse

from httpx import AsyncClient


class _FakeResponse:
    def __init__(self, status_code: int, data: dict | list):
        self.status_code = status_code
        self._data = data
        self.text = ""

    def json(self):
        return self._data


class _FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url: str, **kwargs):
        return _FakeResponse(200, {"access_token": "gho_test_token"})

    async def get(self, url: str, **kwargs):
        if url.endswith("/user"):
            return _FakeResponse(
                200,
                {
                    "id": 42,
                    "login": "octocat",
                    "name": "The Octocat",
                    "email": "octocat@example.com",
                    "html_url": "https://github.com/octocat",
                    "avatar_url": "https://github.com/octocat.png",
                },
            )
        return _FakeResponse(200, [])


async def test_login_requires_client_id(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("routers.auth_github.GITHUB_CLIENT_ID", "")
    resp = await client.get("/auth/login/github", follow_redirects=False)
    assert resp.status_code == 500
    assert resp.json()["detail"] == "GITHUB_CLIENT_ID is not configured"


async def test_callback_missing_state_returns_400(client: AsyncClient):
    resp = await client.get("/auth/github/callback", params={"code": "abc"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Missing code or state parameter"


async def test_callback_invalid_state_returns_400(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("routers.auth_github.GITHUB_CLIENT_ID", "client-id")
    login = await client.get("/auth/login/github", follow_redirects=False)
    assert login.status_code == 302
    resp = await client.get(
        "/auth/github/callback",
        params={"code": "abc", "state": "not-the-session-state"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid or expired OAuth state"


async def test_me_unauthenticated_returns_401(client: AsyncClient):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


async def test_callback_happy_path_then_me_and_logout(
    client: AsyncClient, monkeypatch
):
    monkeypatch.setattr("routers.auth_github.GITHUB_CLIENT_ID", "client-id")
    monkeypatch.setattr("routers.auth_github.GITHUB_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr("routers.auth_github.httpx.AsyncClient", _FakeAsyncClient)

    login = await client.get("/auth/login/github", follow_redirects=False)
    assert login.status_code == 302
    location = login.headers["location"]
    state = parse_qs(urlparse(location).query)["state"][0]

    callback = await client.get(
        "/auth/github/callback",
        params={"code": "oauth-code", "state": state},
    )
    assert callback.status_code == 200
    body = callback.json()
    assert body["message"] == "GitHub OAuth successful"
    assert body["github_user"]["login"] == "octocat"
    assert "access_token" not in body
    assert "access_token" not in body["github_user"]

    me = await client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == 42
    assert me.json()["email"] == "octocat@example.com"

    logout = await client.get("/auth/logout")
    assert logout.status_code == 200
    assert logout.json() == {"status": "logged out"}

    me_after = await client.get("/auth/me")
    assert me_after.status_code == 401
