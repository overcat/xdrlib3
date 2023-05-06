# xdrlib3

A forked version of `xdrlib`, a module for encoding and decoding XDR (External Data Representation) data in Python. `xdrlib` is planned to be removed in Python 3.13 and later versions, therefore this fork has been created to add type hints and maintain compatibility with future versions of Python.

## Installation
You can install `xdrlib3` using pip:

```bash
pip install xdrlib3
```

## Usage
`xdrlib3` has the same functions and methods as `xdrlib`. Here's an example of how to use it:

```python
import xdrlib3

packer = xdrlib3.Packer()
packer.pack_int(16)
packed_data = packer.get_buffer()

unpacker = xdrlib3.Unpacker(packed_data)
unpacked_data = unpacker.unpack_int()
```

## License

`xdrlib3` is a fork of `xdrlib`, so please refer to [the LICENSE file](https://github.com/python/cpython/blob/024ac542d738f56b36bdeb3517a10e93da5acab9/LICENSE) for the original code's licensing agreement, while other parts of the code are released under the MIT license.
