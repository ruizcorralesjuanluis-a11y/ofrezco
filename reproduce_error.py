
from fastapi.testclient import TestClient
from app.main import app
import sys
import traceback

client = TestClient(app)

print("--- Testing / ---")
try:
    response = client.get("/")
    print(f"Status: {response.status_code}")
except Exception:
    traceback.print_exc()

print("\n--- Testing /ui/results ---")
try:
    response = client.get("/ui/results")
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print("Response text partial:", response.text[:500])
except Exception:
    traceback.print_exc()
