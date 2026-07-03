import uvicorn
from api.server import app
from config import settings
from core.curl import format_curl


def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] in ("--cli", "-c"):
        from core.pipeline import Pipeline
        url = sys.argv[2] if len(sys.argv) > 2 else input("URL: ")
        p = Pipeline()
        result = p.run(url)
        if result.success:
            print(f"\nCookie: {result.cookie}")
            print()
            print(format_curl(url, result.cookie))
        else:
            print(f"Failed: {result.error}")
        return

    print(f"RS8 starting on http://{settings.HOST}:{settings.PORT}")
    print("Open http://localhost:8080 in browser")
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level="info")


if __name__ == "__main__":
    main()
