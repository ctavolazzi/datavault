#!/usr/bin/env python3
import webbrowser
import threading
import time
from server import app

def open_browser(port):
    """Open browser after giving the server time to start."""
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{port}')

def main():
    port = 5000

    # Only open browser if this is the main process (not the reloader)
    if threading.current_thread() is threading.main_thread():
        browser_thread = threading.Thread(target=open_browser, args=(port,))
        browser_thread.daemon = True
        browser_thread.start()

    # Start Flask app
    app.run(port=port, debug=True)

if __name__ == '__main__':
    main()