import sys
import json
import requests

# Chargement de la config pour récupérer l'URL
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        api_id = config.get("api_id")
        region = config.get("region", "us-east-1")
except Exception:
    print("❌ Erreur : Impossible de lire config.json")
    sys.exit(1)

stage = sys.argv[1] if len(sys.argv) > 1 else "prod"
base_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/{stage}"


def test_endpoint(path):
    url = f"{base_url}/{path}"
    print(f"🔍 Testing {url}...")
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            print(f"  ✅ {path}: Success (200)")
            return True
        else:
            print(f"  ❌ {path}: Failed ({r.status_code})")
            return False
    except Exception as e:
        print(f"  💥 {path}: Error -> {e}")
        return False


def main():
    endpoints = ["games", "users"]
    results = [test_endpoint(e) for e in endpoints]

    if all(results):
        print("\n🚀 All API tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()