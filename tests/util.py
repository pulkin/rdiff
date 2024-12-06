import numpy as np

from rdiff.chunk import Chunk


def np_chunk_eq(a: Chunk, b: Chunk) -> bool:
    return (a.data_a == b.data_a).all() and (a.data_b == b.data_b).all() and a.eq == b.eq


def np_chunk_eq_aligned(a: Chunk, b: Chunk) -> bool:
     return (a.data_a == b.data_a).all() and (a.data_b == b.data_b).all() and (str(a.eq) == str(b.eq))
