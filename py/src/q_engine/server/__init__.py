from q_engine.ecs.c_bindings import WorldHandle
from q_engine.server.protocol import NetworkServer
from typing import Callable
from socket import socket as Socket
import socket
import select


def mk_socket(net_server: NetworkServer) -> Callable[[WorldHandle], None]:
    sock = Socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(False)
    sock.bind(('0.0.0.0', 8080))
    sock.listen(5)
    print("[Server] Listening on 0.0.0.0:8080")
    
    state = {
        'clients': [],
        'handshakes_sent': set(),
        'net_server': net_server,
    }
    
    def broadcast(message: bytes):
        for client_sock in state['clients'][:]:
            try:
                client_sock.sendall(len(message).to_bytes(4, 'little') + message)
            except Exception as e:
                print(f"[Server] Broadcast failed: {e}")
                state['clients'].remove(client_sock)
                client_sock.close()
    
    def transmit(world: WorldHandle):
        try:
            readable, _, _ = select.select([sock] + state['clients'], [], [], 0.001)
            
            for s in readable:
                if s is sock:
                    try:
                        client_sock, addr = sock.accept()
                        client_sock.setblocking(False)
                        state['clients'].append(client_sock)
                        print(f"[Server] Client connected: {addr}")
                        
                        handshake = state['net_server'].build_handshake()
                        try:
                            client_sock.sendall(len(handshake).to_bytes(4, 'little') + handshake)
                            print(f"[Server] Sent handshake: {len(handshake)} bytes")
                        except Exception as e:
                            print(f"[Server] Send failed: {e}")
                            state['clients'].remove(client_sock)
                            client_sock.close()
                    except Exception as e:
                        print(f"[Server] Accept failed: {e}")
                else:
                    try:
                        data = s.recv(4096)
                        if data:
                            print(f"[Server] Received {len(data)} bytes from client")
                        else:
                            state['clients'].remove(s)
                            s.close()
                            print("[Server] Client disconnected")
                    except BlockingIOError:
                        pass
                    except Exception as e:
                        if s in state['clients']:
                            state['clients'].remove(s)
                        try:
                            s.close()
                        except:
                            pass
                        print(f"[Server] Client error: {e}")
        except Exception as e:
            print(f"[Server] Select error: {e}")
    
    transmit.broadcast = broadcast
    return transmit

