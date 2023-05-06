"""Implements (a subset of) Sun XDR -- eXternal Data Representation.

See: RFC 1014

Adapted from xdrlib.py in the Python standard library, 
you can find the LICENSE file here: https://github.com/python/cpython/blob/024ac542d738f56b36bdeb3517a10e93da5acab9/LICENSE
"""
import struct
from functools import wraps
from io import BytesIO
from typing import Callable, List, Union, TypeVar, Sequence

__all__ = ["Error", "Packer", "Unpacker", "ConversionError"]

T = TypeVar("T")


# exceptions
class Error(Exception):
    """Exception class for this module. Use:

    except xdrlib.Error as var:
        # var has the Error instance for the exception

    Public ivars:
        msg -- contains the message

    """

    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __repr__(self) -> str:
        return repr(self.msg)

    def __str__(self) -> str:
        return str(self.msg)


class ConversionError(Error):
    pass


def raise_conversion_error(function):
    """Wrap any raised struct.errors in a ConversionError."""

    @wraps(function)
    def result(self, value):
        try:
            return function(self, value)
        except struct.error as e:
            raise ConversionError(e.args[0]) from None

    return result


class Packer:
    """Pack various data representations into a buffer."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.__buf = BytesIO()

    def get_buffer(self) -> bytes:
        return self.__buf.getvalue()

    # backwards compatibility
    get_buf = get_buffer

    @raise_conversion_error
    def pack_uint(self, x: int) -> None:
        self.__buf.write(struct.pack(">L", x))

    @raise_conversion_error
    def pack_int(self, x: int) -> None:
        self.__buf.write(struct.pack(">l", x))

    pack_enum = pack_int

    def pack_bool(self, x: bool) -> None:
        if x:
            self.__buf.write(b"\0\0\0\1")
        else:
            self.__buf.write(b"\0\0\0\0")

    def pack_uhyper(self, x: int) -> None:
        try:
            self.pack_uint(x >> 32 & 0xFFFFFFFF)
        except (TypeError, struct.error) as e:
            raise ConversionError(e.args[0]) from None
        try:
            self.pack_uint(x & 0xFFFFFFFF)
        except (TypeError, struct.error) as e:
            raise ConversionError(e.args[0]) from None

    pack_hyper = pack_uhyper

    @raise_conversion_error
    def pack_float(self, x: float) -> None:
        self.__buf.write(struct.pack(">f", x))

    @raise_conversion_error
    def pack_double(self, x: float) -> None:
        self.__buf.write(struct.pack(">d", x))

    def pack_fstring(self, n: int, s: bytes) -> None:
        if n < 0:
            raise ValueError("fstring size must be nonnegative")
        data = s[:n]
        n = ((n + 3) // 4) * 4
        data = data + (n - len(data)) * b"\0"
        self.__buf.write(data)

    pack_fopaque = pack_fstring

    def pack_string(self, s: bytes) -> None:
        n = len(s)
        self.pack_uint(n)
        self.pack_fstring(n, s)

    pack_opaque = pack_string
    pack_bytes = pack_string

    def pack_list(self, list: Sequence[T], pack_item: Callable[[T], None]) -> None:
        for item in list:
            self.pack_uint(1)
            pack_item(item)
        self.pack_uint(0)

    def pack_farray(
        self, n: int, list: Sequence[T], pack_item: Callable[[T], None]
    ) -> None:
        if len(list) != n:
            raise ValueError("wrong array size")
        for item in list:
            pack_item(item)

    def pack_array(self, list: Sequence[T], pack_item: Callable[[T], None]) -> None:
        n = len(list)
        self.pack_uint(n)
        self.pack_farray(n, list, pack_item)


class Unpacker:
    """Unpacks various data representations from the given buffer."""

    def __init__(self, data: Union[bytes, bytearray]) -> None:
        self.reset(data)

    def reset(self, data: Union[bytes, bytearray]) -> None:
        self.__buf = data
        self.__pos = 0

    def get_position(self) -> int:
        return self.__pos

    def set_position(self, position: int) -> None:
        self.__pos = position

    def get_buffer(self) -> bytes:
        return self.__buf

    def done(self) -> None:
        if self.__pos < len(self.__buf):
            raise Error("unextracted data remains")

    def unpack_uint(self) -> int:
        i = self.__pos
        self.__pos = j = i + 4
        data = self.__buf[i:j]
        if len(data) < 4:
            raise EOFError
        return struct.unpack(">L", data)[0]

    def unpack_int(self) -> int:
        i = self.__pos
        self.__pos = j = i + 4
        data = self.__buf[i:j]
        if len(data) < 4:
            raise EOFError
        return struct.unpack(">l", data)[0]

    unpack_enum = unpack_int

    def unpack_bool(self) -> bool:
        return bool(self.unpack_int())

    def unpack_uhyper(self) -> int:
        hi = self.unpack_uint()
        lo = self.unpack_uint()
        return int(hi) << 32 | lo

    def unpack_hyper(self) -> int:
        x = self.unpack_uhyper()
        if x >= 0x8000000000000000:
            x = x - 0x10000000000000000
        return x

    def unpack_float(self) -> float:
        i = self.__pos
        self.__pos = j = i + 4
        data = self.__buf[i:j]
        if len(data) < 4:
            raise EOFError
        return struct.unpack(">f", data)[0]

    def unpack_double(self) -> float:
        i = self.__pos
        self.__pos = j = i + 8
        data = self.__buf[i:j]
        if len(data) < 8:
            raise EOFError
        return struct.unpack(">d", data)[0]

    def unpack_fstring(self, n: int) -> bytes:
        if n < 0:
            raise ValueError("fstring size must be nonnegative")
        i = self.__pos
        j = i + (n + 3) // 4 * 4
        if j > len(self.__buf):
            raise EOFError
        self.__pos = j
        return self.__buf[i : i + n]

    unpack_fopaque = unpack_fstring

    def unpack_string(self) -> bytes:
        n = self.unpack_uint()
        return self.unpack_fstring(n)

    unpack_opaque = unpack_string
    unpack_bytes = unpack_string

    def unpack_list(self, unpack_item: Callable[[], T]) -> List[T]:
        list = []
        while 1:
            x = self.unpack_uint()
            if x == 0:
                break
            if x != 1:
                raise ConversionError("0 or 1 expected, got %r" % (x,))
            item = unpack_item()
            list.append(item)
        return list

    def unpack_farray(self, n: int, unpack_item: Callable[[], T]) -> List[T]:
        list = []
        for i in range(n):
            list.append(unpack_item())
        return list

    def unpack_array(self, unpack_item: Callable[[], T]) -> List[T]:
        n = self.unpack_uint()
        return self.unpack_farray(n, unpack_item)
