#!/usr/bin/env python3
"""Local development server for the z3-pyodide example.

Usage:
    python3 examples/server.py [port]

Serves the examples/ directory. No special headers required —
the demo uses async Promises, not SharedArrayBuffer.
"""

import sys
import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
from functools import partial


class CORSHandler(SimpleHTTPRequestHandler):
    """HTTP handler with CORS headers."""

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, format, *args):
        # Color the status code
        status = args[1] if len(args) > 1 else ""
        if str(status).startswith("2"):
            status_color = "\033[32m"  # green
        elif str(status).startswith("3"):
            status_color = "\033[33m"  # yellow
        else:
            status_color = "\033[31m"  # red
        reset = "\033[0m"
        sys.stderr.write(
            f"  {status_color}{args[0]}{reset} {' '.join(str(a) for a in args[1:])}\n"
        )


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    # Serve from the examples/ directory
    serve_dir = os.path.dirname(os.path.abspath(__file__))
    handler = partial(CORSHandler, directory=serve_dir)

    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"\n  z3-pyodide example server")
    print(f"  Serving {serve_dir}")
    print(f"\n  Open: \033[36mhttp://0.0.0.0:{port}\033[0m\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
