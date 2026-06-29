import unittest

from app import create_app
from scheduler import SchedulerEngine


class FlaskAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SchedulerEngine(autostart=False, aging_factor=0.5)
        self.app = create_app(testing=True, engine=self.engine)
        self.client = self.app.test_client()

    def test_health_endpoint(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_create_job_endpoint(self) -> None:
        response = self.client.post(
            "/api/jobs",
            json={"name": "Video_A", "burst_time": 4},
        )

        payload = response.get_json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["job"]["name"], "Video_A")
        self.assertEqual(payload["state"]["running_job"]["pid"], payload["job"]["pid"])

    def test_invalid_job_rejected(self) -> None:
        response = self.client.post(
            "/api/jobs",
            json={"name": "", "burst_time": 0},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_reset_endpoint(self) -> None:
        self.client.post("/api/jobs", json={"name": "Video_A", "burst_time": 4})
        response = self.client.post("/api/reset")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["clock_seconds"], 0)
        self.assertEqual(payload["stats"]["total_jobs"], 0)
        self.assertEqual(payload["running_job"], None)


if __name__ == "__main__":
    unittest.main()
