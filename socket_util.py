from struct import pack, unpack


def readall(socket, length):
    raw_bytes = b''
    read = 0
    while read < length:
        leftover = length - read
        buffer_size = 4096 if leftover > 4096 else leftover
        read_bytes = socket.recv(buffer_size)
        if not read_bytes:  # len == 0 implies orderly shutdown
            raise ConnectionAbortedError("Socket has closed communication!")
        raw_bytes += read_bytes
        read += len(read_bytes)
    return raw_bytes


def read_u8(socket):
    raw_bytes = socket.recv(1)
    if not raw_bytes:  # len == 0 implies orderly shutdown
        raise ConnectionAbortedError("Socket has closed communication!")
    (u8,) = unpack(">B", raw_bytes)
    return u8


def read_u16(socket):
    raw_bytes = socket.recv(2)
    if not raw_bytes:  # len == 0 implies orderly shutdown
        raise ConnectionAbortedError("Socket has closed communication!")
    (u16,) = unpack(">H", raw_bytes)
    return u16


def read_u32(socket):
    raw_bytes = socket.recv(4)
    if not raw_bytes:  # len == 0 implies orderly shutdown
        raise ConnectionAbortedError("Socket has closed communication!")
    (u32,) = unpack(">I", raw_bytes)
    return u32


def read_u64(socket):
    raw_bytes = socket.recv(8)
    if not raw_bytes:  # len == 0 implies orderly shutdown
        raise ConnectionAbortedError("Socket has closed communication!")
    (u64,) = unpack(">Q", raw_bytes)
    return u64


def send_u8(socket, u8):
    raw_bytes = pack(">B", u8)
    socket.sendall(raw_bytes)


def send_u16(socket, u16):
    raw_bytes = pack(">H", u16)
    socket.sendall(raw_bytes)


def send_u32(socket, u32):
    raw_bytes = pack(">I", u32)
    socket.sendall(raw_bytes)


def send_u64(socket, u64):
    raw_bytes = pack(">Q", u64)
    socket.sendall(raw_bytes)
