from locust import HttpUser, task, between
import random

class LaEscobaUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts"""
        self.match_id = None
    
    @task(3)
    def health_check(self):
        """Health check - most common operation"""
        self.client.get("/health")
    
    @task(2)
    def get_all_cards(self):
        """Get all cards"""
        self.client.get("/cards/cards")
    
    @task(2)
    def get_specific_card(self):
        """Get specific card"""
        card_id = random.randint(1, 40)
        self.client.get(f"/cards/cards/{card_id}")
    
    @task(1)
    def create_match(self):
        """Create a new match"""
        response = self.client.post(
            "/matches/matches",
            json={
                "player1": f"player{random.randint(1, 1000)}",
                "player2": f"player{random.randint(1001, 2000)}"
            }
        )
        
        # Store match_id for subsequent requests
        if response.status_code == 201:
            try:
                self.match_id = response.json().get("match_id")
            except:
                self.match_id = None
    
    @task(2)
    def get_match_state(self):
        """Get match state if we have a match_id"""
        if self.match_id:
            player = random.choice(["player1", "player2"])
            self.client.get(f"/matches/matches/{self.match_id}?player={player}")

class HighLoadUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    @task(10)
    def health_check_high_load(self):
        self.client.get("/health")
    
    @task(5)
    def get_cards_high_load(self):
        self.client.get("/cards/cards")
