"""Smoke load profile. Run with: locust -f loadtests/locustfile.py --host http://localhost:8000"""

from locust import HttpUser, between, task


class PublicSmoke(HttpUser):
    wait_time = between(0.5, 1.5)

    @task(3)
    def health(self):
        self.client.get("/api/v1/health/")

    @task(1)
    def pricing_schema(self):
        self.client.get("/api/v1/schema/")
