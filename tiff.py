"""The float TIFF `exportImage` answers, decoded.

Assumes what hoydedata.no sends and nothing else: uncompressed, single band,
32-bit float, tiled, never striped. Absent tiles (TileOffsets 0) are no
coverage and must read as NaN rather than as zeros, because sea level is
already exactly 0.0.

tufteseid's `vat-cache/fetch_dem.py` holds the other copy of this reader. One
float-TIFF endpoint, one set of quirks: a fix learned here is carried there by
hand.
"""

import struct

import numpy as np

_TYPE_FMT = {1: "B", 3: "H", 4: "I", 11: "f", 12: "d"}
_TYPE_SIZE = {"B": 1, "H": 2, "I": 4, "f": 4, "d": 8}


def read_tiff_f32(buf: bytes) -> np.ndarray:
    """Tiled uncompressed float32 TIFF -> (H, W) float32, absent tiles NaN."""
    if buf[:2] == b"II":
        en = "<"
    elif buf[:2] == b"MM":
        en = ">"
    else:
        raise ValueError(f"not a TIFF: {buf[:200]!r}")

    _magic, ifd = struct.unpack(en + "HI", buf[2:8])
    tags = {}
    (n,) = struct.unpack(en + "H", buf[ifd : ifd + 2])
    for i in range(n):
        p = ifd + 2 + i * 12
        tag, typ, cnt = struct.unpack(en + "HHI", buf[p : p + 8])
        fmt = _TYPE_FMT.get(typ)
        if fmt is None:
            continue
        size = _TYPE_SIZE[fmt] * cnt
        if size <= 4:
            raw = buf[p + 8 : p + 8 + size]
        else:
            (off,) = struct.unpack(en + "I", buf[p + 8 : p + 12])
            raw = buf[off : off + size]
        if len(raw) < size:
            continue
        tags[tag] = struct.unpack(en + fmt * cnt, raw)

    width, height = tags[256][0], tags[257][0]
    if tags.get(259, [1])[0] != 1:
        raise ValueError("compressed TIFF; exportImage never sends one")
    tile_w, tile_h = tags.get(322, [None])[0], tags.get(323, [None])[0]
    if tile_w is None:
        raise ValueError("striped TIFF; exportImage never sends one")

    offsets, counts = tags.get(324, ()), tags.get(325, ())
    out = np.full((height, width), np.nan, np.float32)
    across = (width + tile_w - 1) // tile_w
    for k, (off, cnt) in enumerate(zip(offsets, counts)):
        if off == 0 or cnt == 0:
            continue
        tile = np.frombuffer(
            buf[off : off + cnt], dtype=en + "f4", count=tile_w * tile_h
        ).reshape(tile_h, tile_w)
        row, col = (k // across) * tile_h, (k % across) * tile_w
        h = min(tile_h, height - row)
        w = min(tile_w, width - col)
        out[row : row + h, col : col + w] = tile[:h, :w]
    return out
