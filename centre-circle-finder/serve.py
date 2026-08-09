#!/usr/bin/env python3
"""Dev server for Centre Circle Finder.

`python3 -m http.server` sends no cache headers, so browsers — phones
especially — hold on to index.html. Because the asset URLs carry the ?v=N
cache-buster *inside* index.html, a stale index keeps requesting stale CSS and
JS, and you end up staring at a build from several edits ago wondering why
nothing changed. This sends no-store on everything instead.

    python3 serve.py [port]
"""

import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8123
    handler = partial(NoCacheHandler, directory=str(ROOT))
    # 0.0.0.0 so a phone on the same Wi-Fi can reach it
    print(f"Centre Circle Finder on http://localhost:{port}  (no-store; Ctrl-C to stop)")
    HTTPServer(("0.0.0.0", port), handler).serve_forever()
