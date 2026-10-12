from rest_framework.test import APITestCase


class HealthTests(APITestCase):
    def test_health_is_public_and_returns_ok(self):
        """Анонимный запрос к /api/health/ → 200 и {"status": "ok"}."""
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
