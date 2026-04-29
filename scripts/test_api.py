import requests, json, sys, os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def print_result(test_name, resp):
    status = "✅" if resp.status_code < 400 else "❌"
    print(f"  {status} [{resp.status_code}] {test_name}")
    try:
        print(f"     {json.dumps(resp.json(), indent=6)[:400]}")
    except:
        print(f"     {resp.text[:200]}")
    print()

def test_games(base):
    print("─── /games ───────────────────────────────────────")
    print_result("GET all games",    requests.get(f"{base}/games"))
    print_result("GET game ?id=1",   requests.get(f"{base}/games", params={"id": "1"}))
    print_result("POST create game", requests.post(f"{base}/games", json={"name": "Battle Royale", "max_players": 50}))
    print_result("POST join game",   requests.post(f"{base}/games", json={"id": "1", "action": "join"}))
    print_result("PUT game",         requests.put(f"{base}/games",  json={"id": "1", "status": "maintenance"}))
    print_result("DELETE game",      requests.delete(f"{base}/games", json={"id": "2"}))

def test_users(base):
    print("─── /users ───────────────────────────────────────")
    print_result("GET leaderboard",  requests.get(f"{base}/users"))
    print_result("GET user ?id=1",   requests.get(f"{base}/users", params={"id": "1"}))
    print_result("POST new player",  requests.post(f"{base}/users", json={"username": "newplayer", "email": "new@nexusplay.io"}))
    print_result("PUT score update", requests.put(f"{base}/users",  json={"id": "1", "score": 2000}))
    print_result("DELETE user",      requests.delete(f"{base}/users", json={"id": "3"}))

def test_notifications(base):
    print("─── /notifications ───────────────────────────────")
    print_result("GET health",       requests.get(f"{base}/notifications"))
    print_result("POST info notif",  requests.post(f"{base}/notifications", json={"type": "info",    "message": "Server maintenance in 1h", "subject": "NexusPlay Info"}))
    print_result("POST alert notif", requests.post(f"{base}/notifications", json={"type": "alert",   "message": "High traffic detected!",   "subject": "NexusPlay Alert"}))
    print_result("POST no message",  requests.post(f"{base}/notifications", json={"type": "warning"}))

def main():
    config = load_config()
    stage  = sys.argv[1] if len(sys.argv) > 1 else "dev"
    base   = config["endpoints"].get(stage)
    if not base:
        print(f"❌ Stage '{stage}' not found"); sys.exit(1)
    print(f"\n🧪 NexusPlay API Tests — {stage.upper()}")
    print(f"   Base URL: {base}\n")
    test_games(base)
    test_users(base)
    test_notifications(base)
    print("🏁 Tests complete!")

if __name__ == "__main__":
    main()
