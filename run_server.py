import sys
import socket
from waitress import serve
from app import create_app

# Ensure UTF-8 console output on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_lan_ip():
    """Detect active local network IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually send packets; determines outbound interface
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

app = create_app('production')

if __name__ == '__main__':
    port = 5000
    lan_ip = get_lan_ip()

    print("=" * 64)
    print(" KITAAB BANK - SMART SCHOOL BOOK EXCHANGE (کتاب بینک)")
    print(" Production Local Server (Waitress WSGI)")
    print("=" * 64)
    print(f" Local Machine:  http://127.0.0.1:{port}")
    print(f" School Wi-Fi:   http://{lan_ip}:{port}  <-- Open this on mobile phones")
    print("-" * 64)
    print(" Operating Mode: 100% Offline (Zero external cloud/CDN dependencies)")
    print(" Database:       SQLite with Write-Ahead Logging (WAL)")
    print("=" * 64)
    print(" Server is listening... Press Ctrl+C to stop.")
    print("=" * 64)

    serve(app, host='0.0.0.0', port=port, threads=6)
