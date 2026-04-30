import requests
import json
import sys
import time
import concurrent.futures

CONFIG_PATH = "../config.json"

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def test_concurrent_requests(base_url, endpoint, n=20):
    print(f"🔥 Test concurrent {n} requests → {endpoint}")
    results = {"success": 0, "error": 0, "total_time": 0}

    def make_request(_):
        start = time.time()
        try:
            resp = requests.get(f"{base_url}/{endpoint}", timeout=10)
            return resp.status_code, time.time() - start
        except:
            return 0, 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as executor:
        futures = [executor.submit(make_request, i) for i in range(n)]
        for future in concurrent.futures.as_completed(futures):
            status, elapsed = future.result()
            if 200 <= status < 400:
                results["success"] += 1
            else:
                results["error"] += 1
            results["total_time"] += elapsed
    return results

def test_autoscaling_behavior(base_url, duration_minutes=4):
    print(f"\n🚀 Lancement du test de montée en charge ({duration_minutes} min)...")
    print("   Surveille ton CloudWatch : CPU > 70%")
    
    end_time = time.time() + (60 * duration_minutes)
    while time.time() < end_time:
        # On frappe la route /stress avec 40 requêtes simultanées
        test_concurrent_requests(base_url, "stress", n=40)
        time.sleep(0.5)

def main():
    config = load_config()
    stage = sys.argv[1] if len(sys.argv) > 1 else "prod"
    base_url = config["endpoints"].get(stage)
    
    if not base_url:
        print(f"❌ Stage '{stage}' non trouvé")
        sys.exit(1)

    print(f"🛡️  NexusPlay Resilience & Scaling Test — {stage.upper()}")
    
    # 1. Tests classiques
    test_concurrent_requests(base_url, "health", n=10)
    
    # 2. Test de montée en charge pour déclencher l'ASG
    test_autoscaling_behavior(base_url)

if __name__ == "__main__":
    main()