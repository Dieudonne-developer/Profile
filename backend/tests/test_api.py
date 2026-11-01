import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def _register(client, suffix: str, **extra):
    payload = {
        "email": extra.get("email", f"{suffix}@example.com"),
        "username": extra.get("username", suffix),
        "password": extra.get("password", "SecurePass1"),
        "full_name": extra.get("full_name", "Test User"),
    }
    created = client.post("/api/auth/register", json=payload)
    assert created.status_code == 201, created.text
    token = created.json()["access_token"]
    return payload, {"Authorization": f"Bearer {token}"}


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    home = client.get("/")
    assert home.status_code == 200
    assert home.json()["status"] == "ok"
    icon = client.get("/favicon.ico")
    assert icon.status_code == 204


def test_register_login_and_profile(client, tmp_path):
    unique = tmp_path.name.replace("-", "")[:8]
    payload, headers = _register(client, f"user{unique}")
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    profile = client.get("/api/profile/me", headers=headers)
    assert profile.status_code == 200
    updated = client.put(
        "/api/profile/me",
        headers=headers,
        json={
            "full_name": "Test User",
            "headline": "Engineer",
            "bio": "I build software.",
            "location": "Remote",
            "phone": "",
            "public_email": payload["email"],
            "website": "",
            "github": "",
            "linkedin": "",
            "twitter": "",
            "is_public": True,
        },
    )
    assert updated.status_code == 200
    skill = client.post(
        "/api/skills",
        headers=headers,
        json={"name": "Python", "category": "Languages", "level": 90},
    )
    assert skill.status_code == 201
    public = client.get(f"/api/u/{payload['username']}")
    assert public.status_code == 200
    assert public.json()["skills"][0]["name"] == "Python"
    token = profile.json()["share_token"]
    shared = client.get(f"/api/s/{token}")
    assert shared.status_code == 200
    assert shared.json()["user"]["username"] == payload["username"]


def test_public_profile_accepts_reserved_email_domains(client):
    payload, _headers = _register(
        client,
        "localuser",
        email="owner@portfolio.local",
    )
    public = client.get(f"/api/u/{payload['username']}")
    assert public.status_code == 200, public.text
    assert public.json()["user"]["email"] == "owner@portfolio.local"


def test_rejects_invalid_username(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "badname@example.com",
            "username": "not valid!",
            "password": "SecurePass1",
            "full_name": "Bad",
        },
    )
    assert response.status_code == 422


def test_ai_improve_requires_auth(client):
    response = client.post(
        "/api/ai/improve",
        json={"kind": "bio", "text": "I like building things with Python and React."},
    )
    assert response.status_code == 401


def test_ai_improve_local_provider(client):
    _, headers = _register(client, "writerdemo")
    response = client.post(
        "/api/ai/improve",
        headers=headers,
        json={"kind": "bio", "text": "I like building things with Python and React."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["improved"]
    assert body["provider"] in {"local", "local-fallback", "openai"}


def test_projects_social_notifications_and_network(client):
    owner, owner_headers = _register(client, "ownerone")
    guest, guest_headers = _register(client, "guestone", full_name="Guest One")
    project = client.post(
        "/api/projects",
        headers=owner_headers,
        json={
            "title": "Portfolio API",
            "summary": "REST backend",
            "description": "FastAPI service with PostgreSQL.",
            "tags": ["FastAPI"],
            "featured": True,
        },
    )
    assert project.status_code == 201
    project_id = project.json()["id"]

    liked = client.post(f"/api/projects/{project_id}/like", headers=guest_headers)
    assert liked.status_code == 200
    assert liked.json()["liked"] is True
    commented = client.post(
        f"/api/projects/{project_id}/comments",
        headers=guest_headers,
        json={"body": "Great work."},
    )
    assert commented.status_code == 201
    follow = client.post("/api/network/follow/ownerone", headers=guest_headers)
    assert follow.status_code == 200
    assert follow.json()["is_following"] is True

    notes = client.get("/api/notifications", headers=owner_headers)
    assert notes.status_code == 200
    types = {item["type"] for item in notes.json()}
    assert {"like", "comment", "follow"} <= types
    unread = client.get("/api/notifications/unread-count", headers=owner_headers)
    assert unread.json()["count"] >= 3

    people = client.get("/api/network/people?q=guest", headers=owner_headers)
    assert people.status_code == 200
    assert any(row["username"] == "guestone" for row in people.json())

    feed = client.get("/api/projects/feed")
    assert feed.status_code == 200
    assert any(row["id"] == project_id for row in feed.json())


def test_analytics_and_cv_download(client):
    payload, headers = _register(client, "cvowner")
    client.post(
        "/api/experience",
        headers=headers,
        json={
            "title": "Developer",
            "company": "Studio",
            "start_date": "2024-01",
            "is_current": True,
            "description": "Built web apps.",
        },
    )
    track = client.post(
        "/api/analytics/track",
        json={"username": payload["username"], "event_type": "profile_view", "path": "/u/cvowner"},
    )
    assert track.status_code == 200
    cv = client.get(f"/api/cv/{payload['username']}")
    assert cv.status_code == 200
    assert cv.headers["content-type"].startswith("application/pdf")
    mine = client.get("/api/cv/me", headers=headers)
    assert mine.status_code == 200
    summary = client.get("/api/analytics/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["profile_views"] >= 1
    assert summary.json()["cv_downloads"] >= 1


def test_private_profile_is_hidden(client):
    payload, headers = _register(client, "privateone")
    client.put(
        "/api/profile/me",
        headers=headers,
        json={
            "full_name": "Hidden",
            "headline": "",
            "bio": "",
            "location": "",
            "phone": "",
            "public_email": "",
            "website": "",
            "github": "",
            "linkedin": "",
            "twitter": "",
            "is_public": False,
        },
    )
    hidden = client.get(f"/api/u/{payload['username']}")
    assert hidden.status_code == 403
    visible = client.get(f"/api/u/{payload['username']}", headers=headers)
    assert visible.status_code == 200


def test_photo_upload_rejects_non_image(client):
    _, headers = _register(client, "photouser")
    response = client.post(
        "/api/profile/photo",
        headers=headers,
        files={"file": ("notes.txt", b"not-an-image", "text/plain")},
    )
    assert response.status_code == 400
    ok = client.post(
        "/api/profile/photo",
        headers=headers,
        files={"file": ("photo.png", b"\x89PNG\r\n\x1a\n" + b"0" * 32, "image/png")},
    )
    assert ok.status_code == 200
    assert ok.json()["photo_path"].endswith(".png")


def test_ml_score_and_leaf_without_colab(client):
    status = client.get("/api/ml/status")
    assert status.status_code == 200
    body = status.json()
    assert body["notebook"].endswith(".ipynb")
    assert body["colab_connected"] is False
    score = client.post("/api/ml/predict/score", json={"hours": 6})
    assert score.status_code == 200
    predicted = score.json()["predicted_score"]
    assert 0 <= predicted <= 100
    missing = client.post("/api/ml/predict/leaf", files={"file": ("leaf.jpg", b"tiny", "image/jpeg")})
    assert missing.status_code == 503
    huge = client.post(
        "/api/ml/predict/leaf",
        files={"file": ("leaf.jpg", b"x" * (5 * 1024 * 1024 + 8), "image/jpeg")},
    )
    assert huge.status_code == 400


def test_ml_leaf_inprocess_hook(client):
    from app.api import ml as ml_routes

    ml_routes.inprocess_leaf = lambda _raw: {
        "label": "Healthy",
        "confidence": 0.91,
        "probabilities": {"Healthy": 0.91, "Cordana": 0.03, "Pestalotiopsis": 0.03, "Sigatoka": 0.03},
        "backend": "colab-inprocess",
    }
    try:
        status = client.get("/api/ml/status")
        assert status.json()["colab_connected"] is True
        result = client.post("/api/ml/predict/leaf", files={"file": ("leaf.jpg", b"tiny", "image/jpeg")})
        assert result.status_code == 200
        assert result.json()["label"] == "Healthy"
    finally:
        ml_routes.inprocess_leaf = None


def test_contact_form_reaches_owner_inbox(client, tmp_path, monkeypatch):
    unique = tmp_path.name.replace("-", "")[:8]
    payload, headers = _register(client, f"owner{unique}")
    mailed = {}

    def fake_send(owner, item):
        mailed["to"] = owner.email
        mailed["from"] = item.sender_email
        mailed["body"] = item.body
        return True

    monkeypatch.setattr("app.api.contact.send_contact_email", fake_send)
    sent = client.post(
        f"/api/contact/{payload['username']}",
        json={
            "name": "Hiring Manager",
            "email": "hiring@example.com",
            "subject": "Internship",
            "message": "We would like to discuss an ML internship with you.",
        },
    )
    assert sent.status_code == 201, sent.text
    inbox = client.get("/api/contact/inbox", headers=headers)
    assert inbox.status_code == 200
    assert inbox.json()[0]["sender_email"] == "hiring@example.com"
    notes = client.get("/api/notifications", headers=headers)
    assert any(item["type"] == "contact" for item in notes.json())
    assert mailed["from"] == "hiring@example.com"
    assert "internship" in mailed["body"].lower()


def test_blog_posts_appear_on_public_profile(client, tmp_path):
    unique = tmp_path.name.replace("-", "")[:8]
    payload, headers = _register(client, f"blog{unique}")
    created = client.post(
        "/api/posts",
        headers=headers,
        json={
            "title": "Serving a PyTorch model",
            "summary": "FastAPI around EfficientNet-B0",
            "body": "I wrap the banana leaf classifier in FastAPI so a photo can return a prediction.",
            "published": True,
        },
    )
    assert created.status_code == 201, created.text
    draft = client.post(
        "/api/posts",
        headers=headers,
        json={
            "title": "Unpublished draft",
            "summary": "Hidden",
            "body": "This should not appear on the public page.",
            "published": False,
        },
    )
    assert draft.status_code == 201, draft.text
    public = client.get(f"/api/u/{payload['username']}")
    titles = [item["title"] for item in public.json()["posts"]]
    assert "Serving a PyTorch model" in titles
    assert "Unpublished draft" not in titles
    mine = client.get("/api/posts", headers=headers)
    assert len(mine.json()) == 2


def test_public_registration_can_be_closed(client):
    from app.core.config import get_settings

    settings = get_settings()
    previous = settings.allow_registration
    settings.allow_registration = False
    try:
        blocked = client.post(
            "/api/auth/register",
            json={
                "email": "new@example.com",
                "username": "newperson",
                "password": "SecurePass1",
                "full_name": "New Person",
            },
        )
        assert blocked.status_code == 403
    finally:
        settings.allow_registration = previous
