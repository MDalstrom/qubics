from typing_extensions import Buffer
from typing import Callable, Any
from threading import Thread
import socket

def mk_server(ip, port) -> Callable[[Any], Callable[[Buffer, int], None]]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((ip, port))
    sock.listen()
   
    def serve(cancel) -> Callable[[Buffer, int], None]:
        def _loop():
            while not cancel:
                connection, _ = sock.accept()
            return 

        thread = Thread(target=_loop)
        thread.start()
        return sock.sendall

    return serve


