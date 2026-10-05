"""Minimal NBT (gzipped, big-endian) reader/writer for structure templates."""
import gzip
import struct

END, BYTE, SHORT, INT, LONG, FLOAT, DOUBLE, BYTE_ARRAY, STRING, LIST, COMPOUND, INT_ARRAY, LONG_ARRAY = range(13)


class Tag:
    """Explicitly typed value, for when Python's type isn't enough (e.g. a list of ints vs. an int array)."""
    def __init__(self, type_id, value, elem_type=None):
        self.type, self.value, self.elem = type_id, value, elem_type

    def __repr__(self):
        return f'Tag({self.type}, {self.value!r})'


def _read(buf, pos, t):
    if t == BYTE:
        return struct.unpack_from('>b', buf, pos)[0], pos + 1
    if t == SHORT:
        return struct.unpack_from('>h', buf, pos)[0], pos + 2
    if t == INT:
        return struct.unpack_from('>i', buf, pos)[0], pos + 4
    if t == LONG:
        return struct.unpack_from('>q', buf, pos)[0], pos + 8
    if t == FLOAT:
        return struct.unpack_from('>f', buf, pos)[0], pos + 4
    if t == DOUBLE:
        return struct.unpack_from('>d', buf, pos)[0], pos + 8
    if t == STRING:
        n = struct.unpack_from('>H', buf, pos)[0]
        return buf[pos + 2:pos + 2 + n].decode('utf-8'), pos + 2 + n
    if t in (BYTE_ARRAY, INT_ARRAY, LONG_ARRAY):
        n = struct.unpack_from('>i', buf, pos)[0]
        size, fmt = {BYTE_ARRAY: (1, 'b'), INT_ARRAY: (4, 'i'), LONG_ARRAY: (8, 'q')}[t]
        return list(struct.unpack_from(f'>{n}{fmt}', buf, pos + 4)), pos + 4 + n * size
    if t == LIST:
        et, n = struct.unpack_from('>bi', buf, pos)
        pos += 5
        out = []
        for _ in range(n):
            v, pos = _read(buf, pos, et)
            out.append(v)
        return out, pos
    if t == COMPOUND:
        out = {}
        while True:
            ct = buf[pos]
            pos += 1
            if ct == END:
                return out, pos
            name, pos = _read(buf, pos, STRING)
            out[name], pos = _read(buf, pos, ct)
    raise ValueError(t)


def load(path):
    buf = gzip.open(path).read()
    assert buf[0] == COMPOUND
    _, pos = _read(buf, 1, STRING)
    return _read(buf, pos, COMPOUND)[0]


def _type_of(v):
    if isinstance(v, Tag): return v.type
    if isinstance(v, bool): return BYTE
    if isinstance(v, int): return INT
    if isinstance(v, float): return DOUBLE
    if isinstance(v, str): return STRING
    if isinstance(v, list): return LIST
    if isinstance(v, dict): return COMPOUND
    raise TypeError(type(v))


def _write(out, v, t):
    if isinstance(v, Tag):
        v = v.value
    if t == BYTE: out += struct.pack('>b', int(v))
    elif t == SHORT: out += struct.pack('>h', v)
    elif t == INT: out += struct.pack('>i', v)
    elif t == LONG: out += struct.pack('>q', v)
    elif t == FLOAT: out += struct.pack('>f', v)
    elif t == DOUBLE: out += struct.pack('>d', v)
    elif t == STRING:
        b = v.encode('utf-8')
        out += struct.pack('>H', len(b)) + b
    elif t == INT_ARRAY: out += struct.pack(f'>i{len(v)}i', len(v), *v)
    elif t == LIST:
        et = _type_of(v[0]) if v else END
        out += struct.pack('>bi', et, len(v))
        for x in v:
            _write(out, x, et)
    elif t == COMPOUND:
        for k, x in v.items():
            ct = _type_of(x)
            out += bytes([ct])
            _write(out, k, STRING)
            _write(out, x, ct)
        out += bytes([END])
    else:
        raise ValueError(t)


def save(path, root):
    out = bytearray([COMPOUND])
    _write(out, '', STRING)
    _write(out, root, COMPOUND)
    with gzip.open(path, 'wb') as f:
        f.write(bytes(out))
