import threading
import time
import webbrowser

import uvicorn

from app.main import app


HOST = "127.0.0.1"
PORT = 8000

APP_URL = f"http://{HOST}:{PORT}"


def open_browser():
    time.sleep(1.5)
    webbrowser.open(APP_URL)


def main():
    browser_thread = threading.Thread(
        target=open_browser,
        daemon=True,
    )

    browser_thread.start()

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()