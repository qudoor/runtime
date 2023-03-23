import json
from django.utils.crypto import get_random_string
from rest_framework.test import APITestCase

from .models import User


class UserTestCase(APITestCase):
    user_admin = None
    user_admin_username = "test_admin"
    user_admin_password = "test-admin"
    user_general = None
    user_general_username = "test_general"
    user_general_password = "test-general"

    @classmethod
    def setUpClass(cls):
        cls.user_admin = User.objects.create_superuser(
            cls.user_admin_username,
            email=f"{cls.user_admin_username}@test.com",
            password=cls.user_admin_password
        )
        cls.user_general = User.objects.create_user(
            cls.user_general_username,
            email=f"{cls.user_general_password}@test.com",
            password=cls.user_general_password
        )

    @classmethod
    def tearDownClass(cls):
        cls.user_admin.delete()
        cls.user_general.delete()

    def login(self, data):
        res = self.client.post("/api/auth/login/", json.dumps(data), content_type="application/json")
        return res

    def test_01_login_success(self):
        data = {
            "username": self.user_admin_username,
            "password": self.user_admin_password
        }
        res = self.login(data)
        self.assertEqual(res.status_code, 200)

    def test_02_login_fail(self):
        data = {
            "username": get_random_string(),
            "password": get_random_string()
        }
        res = self.login(data)
        self.assertEqual(res.status_code, 400)

    def test_03_user_list(self):
        data = {
            "username": self.user_admin_username,
            "password": self.user_admin_password
        }
        res = self.login(data)
        token = res.json()['token']
        res2 = self.client.get("/api/auth/manage/user/", HTTP_AUTHORIZATION=f"JWT {token}")
        self.assertEqual(res2.status_code, 200)

    def test_04_invalid_token(self):
        token = get_random_string()
        res2 = self.client.get("/api/auth/manage/user/", HTTP_AUTHORIZATION=f"JWT {token}")
        self.assertEqual(res2.status_code, 401)

    def test_05_permission_denied(self):
        data = {
            "username": self.user_general_username,
            "password": self.user_general_password
        }
        res = self.login(data)
        token = res.json()['token']
        res2 = self.client.get("/api/auth/manage/user/", HTTP_AUTHORIZATION=f"JWT {token}")
        self.assertEqual(res2.status_code, 403)
