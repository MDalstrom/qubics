import socket
import ctypes
from bridge.types import World, ChunkContainer, World_p, WorldMethods
from typing import Dict, Tuple
from .handshake import serialize_handshake, deserialize_handshake


class Network:
    def __init__(self, world_handle: WorldMethods, host: str = 'localhost', listen_port: int = 18488):
        self.world_handle = world_handle
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if listen_port:
            self.sock.bind((host, listen_port))
            self.sock.listen()
        self.peers: list[socket.socket] = []
        self.is_closed = False
        self.server_authority: Dict[int, str] = {}

    def __del__(self):
        self.is_closed = True
        for peer_sock in self.peers:
            peer_sock.close()
        self.sock.close()

    def connect(self, host: str, port: int):
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.connect((host, port))

        handshake_size_bytes = self.recv_bytes(peer_socket, 4)
        handshake_size = int.from_bytes(handshake_size_bytes, 'little')
        handshake_data = self.recv_bytes(peer_socket, handshake_size)
        self.server_authority = deserialize_handshake(handshake_data)

        self.peers.append(peer_socket)

    def poll_new_connections(self):
        while not self.is_closed:
            conn, addr = self.sock.accept()
            authority = self.world_handle.descriptors_authority
            handshake_data = serialize_handshake(authority)
            conn.sendall(len(handshake_data).to_bytes(4, 'little'))
            conn.sendall(handshake_data)
            self.peers.append(conn)

    def send_world(self, world: World):
        active_peers = [p for p in self.peers if p.fileno() != -1]
        for conn in active_peers:
            try:
                self.send_world_to_peer(conn, world)
            except (BrokenPipeError, ConnectionResetError):
                if conn in self.peers:
                    self.peers.remove(conn)
                conn.close()

    def recv_and_update_world(self):
        active_peers = [p for p in self.peers if p.fileno() != -1]
        for conn in active_peers:
            try:
                self.recv_and_update_world_from_peer(conn, self.world_handle.handle, self.world_handle)
            except (BrokenPipeError, ConnectionResetError, ConnectionError) as e:
                if conn in self.peers:
                    self.peers.remove(conn)
                conn.close()

    def send_world_to_peer(self, conn: socket.socket, world: World):
        conn.sendall(world.containers_count.to_bytes(8, 'little'))
        for i in range(world.containers_count):
            container = world.containers[i]
            archetype_ids = self.get_archetype_ids(container, self.world_handle)
            conn.sendall(len(archetype_ids).to_bytes(8, 'little'))
            for component_id in archetype_ids:
                conn.sendall(component_id.to_bytes(8, 'little'))

            conn.sendall(container.chunks_count.to_bytes(8, 'little'))
            for k in range(container.chunks_count):
                chunk = container.chunks[k]
                conn.sendall(chunk.entities_count.to_bytes(8, 'little'))
                for l in range(container.archetype.length):
                    stride = container.archetype.descriptors[l].contents.stride
                    data_size = stride * chunk.entities_count
                    conn.sendall(data_size.to_bytes(8, 'little'))
                    if data_size > 0:
                        buffer_data = ctypes.string_at(chunk.buffers[l], data_size)
                        conn.sendall(buffer_data)

    def recv_and_update_world_from_peer(self, conn: socket.socket, world_p: World_p, world_handle: WorldMethods):
        world = ctypes.cast(world_p, ctypes.POINTER(World)).contents
        name_to_type_map = {t.__name__: t for t in world_handle.descriptors_authority.keys()}
        archetype_map: Dict[Tuple[str, ...], ChunkContainer] = {
            self.get_archetype_names(c, world_handle): c for c in world.containers[:world.containers_count]
        }

        containers_count_bytes = self.recv_bytes(conn, 8)
        if not containers_count_bytes:
            return
        containers_count = int.from_bytes(containers_count_bytes, 'little')

        for _ in range(containers_count):
            archetype_len = int.from_bytes(self.recv_bytes(conn, 8), 'little')
            server_ids = [int.from_bytes(self.recv_bytes(conn, 8), 'little') for _ in range(archetype_len)]
            names = [self.server_authority[server_id] for server_id in server_ids]
            archetype_names_tuple = tuple(sorted(names))
            local_container = archetype_map.get(archetype_names_tuple)
            incoming_chunks_count = int.from_bytes(self.recv_bytes(conn, 8), 'little')

            if local_container is None:
                self.handle_new_container(conn, world_handle, name_to_type_map, archetype_names_tuple, archetype_len, incoming_chunks_count)
            else:
                self.update_existing_container(conn, local_container, incoming_chunks_count)

    def handle_new_container(self, conn, world_handle, name_to_type_map, archetype_names_tuple, archetype_len, incoming_chunks_count):
        try:
            types = [name_to_type_map[name] for name in archetype_names_tuple]
        except KeyError:
            types = None
        
        for _ in range(incoming_chunks_count):
            entities_count = int.from_bytes(self.recv_bytes(conn, 8), 'little')
            received_buffers = [self.recv_bytes(conn, int.from_bytes(self.recv_bytes(conn, 8), 'little')) for _ in range(archetype_len)]

            if not types or entities_count == 0:
                continue

            new_entities = [world_handle.create_entity(types) for _ in range(entities_count)]
            if not new_entities:
                continue

            chunk_p = new_entities[0].chunk
            archetype = chunk_p.contents.container.contents.archetype
            for i, comp_type in enumerate(types):
                for j in range(archetype.length):
                    desc_p = archetype.descriptors[j]
                    if world_handle.get_component_type(desc_p) == comp_type:
                        dest_ptr = chunk_p.contents.buffers[j]
                        source_buffer = received_buffers[i]
                        ctypes.memmove(dest_ptr, source_buffer, len(source_buffer))
                        break
    
    def update_existing_container(self, conn, local_container, incoming_chunks_count):
        update_chunk_count = min(incoming_chunks_count, local_container.chunks_count)
        for i in range(update_chunk_count):
            entities_count = int.from_bytes(self.recv_bytes(conn, 8), 'little')
            local_chunk = local_container.chunks[i]
            local_chunk.entities_count = entities_count

            for j in range(local_container.archetype.length):
                data_size = int.from_bytes(self.recv_bytes(conn, 8), 'little')
                data_buffer = self.recv_bytes(conn, data_size)
                if data_size > 0:
                    ctypes.memmove(local_chunk.buffers[j], data_buffer, data_size)

        # Discard extra chunks
        if incoming_chunks_count > update_chunk_count:
            for _ in range(incoming_chunks_count - update_chunk_count):
                self.recv_bytes(conn, 8) # entities_count
                for _ in range(local_container.archetype.length):
                    data_size = int.from_bytes(self.recv_bytes(conn, 8), 'little')
                    self.recv_bytes(conn, data_size)

    @staticmethod
    def recv_bytes(sock: socket.socket, size: int) -> bytes:
        if size == 0:
            return b''
        data = bytearray(size)
        view = memoryview(data)
        while size > 0:
            n = sock.recv_into(view, size)
            if n == 0:
                raise ConnectionError("Socket connection broken")
            view = view[n:]
            size -= n
        return bytes(data)

    @staticmethod
    def get_archetype_names(container: ChunkContainer, world_handle: WorldMethods) -> Tuple[str, ...]:
        archetype = container.archetype
        types = [world_handle.get_component_type(archetype.descriptors[j]) for j in range(archetype.length)]
        return tuple(sorted([t.__name__ for t in types if t is not None]))

    @staticmethod
    def get_archetype_ids(container: ChunkContainer, world_handle: WorldMethods) -> Tuple[int, ...]:
        archetype = container.archetype
        type_to_id = world_handle.descriptors_authority
        ids = []
        for j in range(archetype.length):
            descriptor = archetype.descriptors[j]
            descriptor_addr = ctypes.addressof(descriptor.contents)
            for comp_type, desc in type_to_id.items():
                if ctypes.addressof(desc.contents) == descriptor_addr:
                    ids.append(descriptor_addr)
                    break
        return tuple(sorted(ids))
