import os
import unittest
from unittest.mock import patch

import mongomock
import run as app_run


class TestOutfitInteractions(unittest.TestCase):
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
        self.app.db.outfits.delete_many({})
        self.app.db.likes.delete_many({})
        self.app.db.comments.delete_many({})

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

    def test_likes_and_comments_roundtrip(self):
        register_response = self.register_user(
            name="fituser",
            email="fituser@example.com",
            password="Test1234",
        )
        self.assertEqual(register_response.status_code, 201)

        token = register_response.get_json()["token"]

        create_outfit_response = self.client.post(
            "/api/outfits",
            json={
                "name": "Street Fit",
                "gender": "female",
                "description": "Test outfit",
                "published": True,
            },
            headers=self.auth_header(token),
        )
        self.assertEqual(create_outfit_response.status_code, 201)

        outfit_id = create_outfit_response.get_json()["id"]

        like_response = self.client.post(
            f"/api/outfits/{outfit_id}/likes",
            headers=self.auth_header(token),
        )
        self.assertIn(like_response.status_code, (200, 201))

        likes_response = self.client.get(f"/api/outfits/{outfit_id}/likes")
        self.assertEqual(likes_response.status_code, 200)

        likes_body = likes_response.get_json()
        self.assertEqual(likes_body["count"], 1)
        self.assertEqual(len(likes_body["likes"]), 1)

        comment_response = self.client.post(
            f"/api/outfits/{outfit_id}/comments",
            json={"content": "Great look"},
            headers=self.auth_header(token),
        )
        self.assertEqual(comment_response.status_code, 201)

        comments_response = self.client.get(f"/api/outfits/{outfit_id}/comments")
        self.assertEqual(comments_response.status_code, 200)

        comments_body = comments_response.get_json()
        self.assertEqual(comments_body["count"], 1)
        self.assertEqual(comments_body["comments"][0]["content"], "Great look")


if __name__ == "__main__":
    unittest.main()
