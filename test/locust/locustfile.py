from locust import HttpUser, task

class LoadTest(HttpUser):

    @task
    def get_cards(self):
        self.client.get("/cards/cards")

    @task
    def health_auth(self):
        self.client.get("/auth/health")

    @task
    def health_match(self):
        self.client.get("/matches/health")