import sys
from app import create_app

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

app = create_app('development')

if __name__ == '__main__':
    print("=" * 60)
    print("Kitaab Bank - Development Server")
    print("URL: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
