import os
import sys

import httpx

BASE = os.getenv("REDTAG_API", "http://localhost:8080/api/v1")


def main() -> int:
    with httpx.Client(timeout=10) as client:
        health = client.get(f"{BASE}/health")
        health.raise_for_status()
        incidents = client.get(f"{BASE}/incidents")
        incidents.raise_for_status()
        print("Health:", health.json())
        print("Incidents:", len(incidents.json()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
