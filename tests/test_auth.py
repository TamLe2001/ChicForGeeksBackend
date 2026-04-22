import os
import unittest
from unittest.mock import patch

import mongomock
import run as app_run


class TestAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("FLASK_DEBUG", "False")
        os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
        os.environ.setdefault("MONGO_DB_NAME", "test_database")
        os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

        cls.mongo_patcher = patch.object(app_run, "MongoClient", mongomock.MongoClient)
        cls.download_patcher = patch.object(
            app_run.FileService,
            "download_default_files",
            lambda self, uploads_path: None,
        )
        cls.cloud_patcher = patch.object(app_run, "CloudService", lambda db, config: object())

        cls.mongo_patcher.start()
        cls.download_patcher.start()
        cls.cloud_patcher.start()

        cls.app = app_run.create_app()
        cls.app.config["TESTING"] = True

    @classmethod
    def tearDownClass(cls):
        cls.cloud_patcher.stop()
        cls.download_patcher.stop()
        cls.mongo_patcher.stop()

    def setUp(self):
        self.client = self.app.test_client()
        self.app.db.users.delete_many({})

    def register_user(self, name="tester", email="tester@example.com", password="Test1234"):
        return self.client.post(
            "/api/auth/register",
            json={
                "name": name,
                "email": email,
                "password": password,
            },
        )

    @staticmethod
    def auth_header(token):
        return {"Authorization": f"Bearer {token}"}

    def test_register_login_and_me(self):
        register_response = self.register_user()
        self.assertEqual(register_response.status_code, 201)

        register_body = register_response.get_json()
        self.assertIn("token", register_body)
        self.assertEqual(register_body["user"]["email"], "tester@example.com")

        login_response = self.client.post(
            "/api/auth/login",
            json={
                "user_info": "tester@example.com",
                "password": "Test1234",
            },
        )
        self.assertEqual(login_response.status_code, 200)

        login_body = login_response.get_json()
        token = login_body["token"]

        me_response = self.client.get("/api/auth/me", headers=self.auth_header(token))
        self.assertEqual(me_response.status_code, 200)

        me_body = me_response.get_json()
        self.assertEqual(me_body["email"], "tester@example.com")


if __name__ == "__main__":
    unittest.main()
