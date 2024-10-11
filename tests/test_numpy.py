import numpy as np

from rdiff.chunk import Diff, Chunk, Signature, ChunkSignature
from rdiff.numpy import diff, get_row_col_diff, align_inflate

from .util import np_chunk_eq


def test_equal(monkeypatch):
    np.random.seed(0)
    a = np.random.randint(0, 10, size=(10, 10))

    monkeypatch.setattr(Chunk, "__eq__", np_chunk_eq)

    assert diff(a, a) == Diff(
        ratio=1,
        diffs=[
            Chunk(data_a=a, data_b=a, eq=[
                Diff(ratio=1.0, diffs=[Chunk(data_a=_i, data_b=_i, eq=True)])
                for _i in a
            ])
        ]
    )


def test_random(monkeypatch):
    np.random.seed(0)
    a = np.random.randint(0, 10, size=(10, 10))
    b = a.copy()
    b[1:, 1] = 11
    b[2:, 2] = 12
    b[3] = 13

    monkeypatch.setattr(Chunk, "__eq__", np_chunk_eq)

    assert diff(a, b) == Diff(
        ratio=0.9,
        diffs=[
            Chunk(data_a=a[:3], data_b=b[:3], eq=[
                Diff(ratio=1.0, diffs=[
                    Chunk(data_a=a[0], data_b=b[0], eq=True),
                ]),
                Diff(ratio=0.9, diffs=[
                    Chunk(data_a=a[1, :1], data_b=b[1, :1], eq=True),
                    Chunk(data_a=a[1, 1:2], data_b=b[1, 1:2], eq=False),
                    Chunk(data_a=a[1, 2:], data_b=b[1, 2:], eq=True),
                ]),
                Diff(ratio=0.8, diffs=[
                    Chunk(data_a=a[2, :1], data_b=b[2, :1], eq=True),
                    Chunk(data_a=a[2, 1:3], data_b=b[2, 1:3], eq=False),
                    Chunk(data_a=a[2, 3:], data_b=b[2, 3:], eq=True),
                ]),
            ]),
            Chunk(data_a=a[3:4], data_b=b[3:4], eq=False),
            Chunk(data_a=a[4:], data_b=b[4:], eq=[
                Diff(ratio=0.8, diffs=[
                    Chunk(data_a=_a[:1], data_b=_b[:1], eq=True),
                    Chunk(data_a=_a[1:3], data_b=_b[1:3], eq=False),
                    Chunk(data_a=_a[3:], data_b=_b[3:], eq=True),
                ])
                for _a, _b in zip(a[4:], b[4:])
            ])
        ]
    )


def test_row_col_sig_eq_0():
    np.random.seed(0)
    a = np.random.randint(0, 10, size=(10, 10))
    assert get_row_col_diff(a, a) == (
        Signature(parts=(ChunkSignature(10, 10, True),)),
        Signature(parts=(ChunkSignature(10, 10, True),)),
    )


def test_row_col_sig_eq_1():
    np.random.seed(0)
    a = np.random.randint(0, 10, size=(10, 10))
    b = a.copy()
    for i in range(10):
        b[i, i] += 1
    assert get_row_col_diff(a, b) == (
        Signature(parts=(ChunkSignature(10, 10, True),)),
        Signature(parts=(ChunkSignature(10, 10, True),)),
    )


def test_row_col_sig_row():
    np.random.seed(0)
    a = np.random.randint(0, 10, size=(10, 10))
    b = a.copy()
    b[4] += 1
    assert get_row_col_diff(a, b) == (
        Signature(parts=(
            ChunkSignature(4, 4, True),
            ChunkSignature(1, 1, False),
            ChunkSignature(5, 5, True),
        )),
        Signature(parts=(
            ChunkSignature(10, 10, True),
        )),
    )


def test_row_col_sig_col():
    np.random.seed(0)
    a = np.random.randint(0, 10, size=(10, 10))
    b = a.copy()
    b[:, 4] += 1
    assert get_row_col_diff(a, b) == (
        Signature(parts=(
            ChunkSignature(10, 10, True),
        )),
        Signature(parts=(
            ChunkSignature(4, 4, True),
            ChunkSignature(1, 1, False),
            ChunkSignature(5, 5, True),
        )),
    )


def test_row_col_sig_row_col():
    np.random.seed(0)
    a = np.random.randint(0, 10, size=(10, 10))
    b = a.copy()
    b[4] += 1
    b[:, 4] += 1
    assert get_row_col_diff(a, b) == (
        Signature(parts=(
            ChunkSignature(4, 4, True),
            ChunkSignature(1, 1, False),
            ChunkSignature(5, 5, True),
        )),
        Signature(parts=(
            ChunkSignature(4, 4, True),
            ChunkSignature(1, 1, False),
            ChunkSignature(5, 5, True),
        )),
    )


def test_align_inflate():
    a = np.arange(5)
    b = np.arange(5, 11)
    s = Signature(parts=[
        ChunkSignature(size_a=1, size_b=1, eq=True),
        ChunkSignature(size_a=2, size_b=3, eq=False),
        ChunkSignature(size_a=2, size_b=2, eq=True),
    ])
    a_, b_ = align_inflate(a, b, -1, s, 0)
    assert (a_ == np.array([0, 1, 2, -1, -1, -1, 3, 4])).all()
    assert (b_ == np.array([5, -1, -1, 6, 7, 8, 9, 10])).all()
