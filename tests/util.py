import numpy as np

from rdiff.chunk import Chunk


def np_chunk_eq(a: Chunk, b: Chunk) -> bool:
    return (a.data_a == b.data_a).all() and (a.data_b == b.data_b).all() and a.eq == b.eq


def np_chunk_eq_aligned(a: Chunk, b: Chunk) -> bool:
    def np2tuple(i):
        if not isinstance(i, (list, tuple)):
            return i
        return type(i)([
            j.tolist()
            if isinstance(j, np.ndarray)
            else j
            for j in i
        ])

    return (a.data_a == b.data_a).all() and (a.data_b == b.data_b).all() and np2tuple(a.eq) == np2tuple(b.eq)
