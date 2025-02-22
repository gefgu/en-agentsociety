import socket
from contextlib import closing
from typing import Union

__all__ = ["find_free_port"]


def find_free_port(num_ports: int = 1) -> Union[int, list[int]]:
    ports: list[int] = []
    sockets = []

    for _ in range(num_ports):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ports.append(s.getsockname()[1])
        sockets.append(s)
    for s in sockets:
        s.close()
    if num_ports == 1:
        return ports[0]
    else:
        return ports
