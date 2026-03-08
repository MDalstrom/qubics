import ctypes


def serialize_handshake(authority: dict[type, int]):
    bf = bytearray()

    bf.extend(len(authority).to_bytes())
    for t, ptr in authority.items():
        bf.extend(len(t.__name__).to_bytes())
        bf.extend(t.__name__.encode('utf-8'))
        ptr_addr = ctypes.addressof(ptr.contents) if hasattr(ptr, 'contents') else ptr
        bf.extend(ptr_addr.to_bytes(8, 'little'))

    return bf

def deserialize_handshake(bf: bytearray) -> dict[int, str]:
    result = {}

    offset = 0

    count = bf[offset]
    offset += 1

    for i in range(count):
        name_length = bf[offset]
        offset += 1

        name = bf[offset:offset + name_length].decode('utf-8')
        offset += name_length

        ptr = int.from_bytes(bf[offset:offset + 8], 'little')
        offset += 8
         
        result[ptr] = name

    return result
