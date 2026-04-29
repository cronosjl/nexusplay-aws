import random
from locust import HttpUser
from locust import task
from locust import between


class NexusPlayUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_games(self):
        self.client.get("/prod/games")

    @task(1)
    def view_users(self):
        self.client.get("/prod/users")

    @task(1)
    def mock_error(self):
        # On teste un endpoint inexistant pour vérifier le monitoring
        self.client.get("/prod/unknown", name="/error_test")
