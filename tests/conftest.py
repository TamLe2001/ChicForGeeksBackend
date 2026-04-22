import os

import mongomock
import pytest

import run as app_run


@pytest.fixture
def app(monkeypatch):
    os.environ.setdefault("FLASK_DEBUG", "False")
    os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
    os.environ.setdefault("MONGO_DB_NAME", "test_database")
    os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

    monkeypatch.setattr(app_run, "MongoClient", mongomock.MongoClient)
    monkeypatch.setattr(
        app_run.FileService,
        "download_default_files",
        lambda self, uploads_path: None,
    )
    monkeypatch.setattr(app_run, "CloudService", lambda db, config: object())

    flask_app = app_run.create_app()
    flask_app.config["TESTING"] = True

    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def register_user(client, name="tester", email="tester@example.com", password="Test1234"):
    response = client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
        },
    )
    return response


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}
