import requests
import socket
import time

def check_network():
    print("🌐 Network Diagnostic checking api.motherduck.com ...")
    
    # 1. DNS Resolution
    try:
        ip = socket.gethostbyname("api.motherduck.com")
        print(f"✅ DNS Resolved: api.motherduck.com -> {ip}")
    except Exception as e:
        print(f"❌ DNS Resolution Failed: {e}")
        return

    # 2. HTTPS Connect
    try:
        t0 = time.time()
        resp = requests.get("https://api.motherduck.com/health", timeout=10)
        dur = time.time() - t0
        print(f"✅ HTTPS Connection successful (status={resp.status_code}, time={dur:.2f}s)")
    except Exception as e:
        print(f"❌ HTTPS Connection Failed: {e}")

if __name__ == "__main__":
    check_network()
