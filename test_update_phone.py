import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
PROFILE_ID = 1 # Asumimos perfil 1, cambiar si es necesario

def test_update_phone():
    url = f"{BASE_URL}/profiles/{PROFILE_ID}/phone"
    payload = {"phone": "+34666777888"}
    
    print(f"Probando PUT {url} con {payload}...")
    try:
        response = requests.put(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Actualización de teléfono exitosa.")
        else:
            print("❌ Fallo en la actualización.")
            
    except Exception as e:
        print(f"❌ Error conectando: {e}")

if __name__ == "__main__":
    test_update_phone()
