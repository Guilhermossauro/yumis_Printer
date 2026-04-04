from __future__ import annotations

import socket


def get_local_ip_address() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        return sock.getsockname()[0]
    except OSError:
        try:
            hostname_ip = socket.gethostbyname(socket.gethostname())
            if hostname_ip and not hostname_ip.startswith("127."):
                return hostname_ip
        except OSError:
            pass
        return "127.0.0.1"
    finally:
        sock.close()