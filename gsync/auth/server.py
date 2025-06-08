"""Module for starting an HTTP server to receive authcode by OAuth callback."""

import threading
import queue
import typing
import socket
from urllib.parse import urlparse, ParseResult, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler


authcode_queue: queue.Queue = queue.Queue()


class NoPortAvailableException(Exception):
    """No port is available."""


class AuthFlowRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            authcode_queue.put(query["code"])
            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                b'<p style="color:green">code received, you can close this tab now.</p>\n'
            )
            self.wfile.flush()
            threading.Thread(target=self.server.shutdown).start()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"waiting for auth code...\n")


def launch_server(port: int) -> tuple[threading.Thread, typing.Callable[[], str]]:
    """Launch HTTP server in a new thread."""

    address = ("localhost", port)
    server = HTTPServer(address, AuthFlowRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    return (server_thread, lambda: authcode_queue.get())


def select_redirect_uri(redirect_uris: list[str]) -> ParseResult | None:
    """Check for available port and select one redirect uri from given list."""
    uri = None
    for i, redirect_uri in enumerate(redirect_uris):
        parsed_url = urlparse(redirect_uri)
        if parsed_url.scheme != "http" or parsed_url.hostname != "localhost":
            continue
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("localhost", parsed_url.port))
            uri = parsed_url
            break
        except OSError as e:
            if i != len(redirect_uris) - 1:
                pass
            else:
                raise NoPortAvailableException() from e
        finally:
            sock.close()
    return uri
