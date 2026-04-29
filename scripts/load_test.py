from locust import HttpUser, task, between
import json, random

class NexusPlayUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_games(self):
        self.client.get("/prod/games")

    @task(2)
    def get_leaderboard(self):
        self.client.get("/prod/users")

    @task(1)
    def join_game(self):
        self.client.post("/prod/games", json={"id": str(random.randint(1, 3)), "action": "join"})

    @task(1)
    def create_user(self):
        self.client.post("/prod/users", json={
            "username": f"player_{random.randint(1000, 9999)}",
            "email":    f"player_{random.randint(1000, 9999)}@nexusplay.io"
        })

    @task(1)
    def send_notification(self):
        self.client.post("/prod/notifications", json={
            "type":    "info",
            "message": "Load test notification",
            "subject": "Load Test"
        })
