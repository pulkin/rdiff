import numpy as np
import pytest

from rdiff.chunk import Diff, Chunk, Signature, ChunkSignature
from rdiff.numpy import diff, get_row_col_diff, align_inflate, diff_aligned_2d

from .util import np_chunk_eq


@pytest.fixture
def a():
    np.random.seed(0)
    return np.random.randint(0, 10, size=(10, 10))


@pytest.fixture
def a1(a):
    return a + np.eye(10, dtype=a.dtype)


def test_equal(monkeypatch, a):
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


def test_random(monkeypatch, a):
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


def test_row_col_sig_eq_0(a):
    assert get_row_col_diff(a, a) == (
        Signature(parts=(ChunkSignature(10, 10, True),)),
        Signature(parts=(ChunkSignature(10, 10, True),)),
    )


def test_row_col_sig_eq_1(a, a1):
    assert get_row_col_diff(a, a1) == (
        Signature(parts=(ChunkSignature(10, 10, True),)),
        Signature(parts=(ChunkSignature(10, 10, True),)),
    )


def test_row_col_sig_row(a):
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


def test_row_col_sig_col(a):
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


def test_row_col_sig_row_col(a):
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


@pytest.mark.parametrize("col_diff_sig", [None, Signature(parts=[ChunkSignature(10, 10, True)])])
def test_diff_aligned_2d_same_0(a, a1, col_diff_sig):
    a_, b_, eq = diff_aligned_2d(a, a1, 0, col_diff_sig=col_diff_sig)
    assert (a_ == a).all()
    assert (b_ == a1).all()
    assert (eq == (a == a1)).all()


def test_diff_aligned_2d_same_1(a):
    a_, b_, eq = diff_aligned_2d(
        a, a, 0,
        col_diff_sig=Signature(parts=[
            ChunkSignature(3, 3, True),
            ChunkSignature(1, 1, False),
            ChunkSignature(6, 6, True),
        ])
    )

    at = np.insert(a, 4, 0, axis=1)
    bt = np.insert(a, 3, 0, axis=1)
    mask = at == bt
    mask[:, 3:5] = False

    assert (a_ == at).all()
    assert (b_ == bt).all()
    assert (eq == mask).all()


def test_diff_aligned_2d_new_row(a, a1):
    at = np.insert(a, 4, 0, axis=0)
    bt = np.insert(a1, 4, 0, axis=0)
    mask = at == bt
    mask[4, :] = False

    a_, b_, eq = diff_aligned_2d(a, bt, 0)
    assert (a_ == at).all()
    assert (b_ == bt).all()
    assert (eq == mask).all()


def test_diff_aligned_2d_new_col(a, a1):
    at = np.insert(a, 4, 0, axis=1)
    bt = np.insert(a1, 4, 0, axis=1)
    mask = at == bt
    mask[:, 4] = False

    a_, b_, eq = diff_aligned_2d(a, bt, 0)
    assert (a_ == at).all()
    assert (b_ == bt).all()
    assert (eq == mask).all()


def test_diff_aligned_2d_new_row_col(a, a1):
    at = np.insert(np.insert(a, 4, 0, axis=0), 8, 0, axis=1)
    bt = np.insert(np.insert(a1, 4, 0, axis=0), 8, 0, axis=1)
    mask = at == bt
    mask[4, :] = mask[:, 8] = False

    a_, b_, eq = diff_aligned_2d(a, bt, 0)
    assert (a_ == at).all()
    assert (b_ == bt).all()
    assert (eq == mask).all()


def test_diff_aligned_2d_mix_0(a, a1):
    a = np.insert(np.insert(a, 4, 42, axis=0), 8, 42, axis=1)
    a1 = np.insert(np.insert(a1, 4, 89, axis=0), 8, 89, axis=1)

    at = np.insert(np.insert(a, 5, 0, axis=0), 9, 0, axis=1)
    bt = np.insert(np.insert(a1, 4, 0, axis=0), 8, 0, axis=1)
    mask = at == bt
    mask[4:6, :] = mask[:, 8:10] = False

    a_, b_, eq = diff_aligned_2d(a, a1, 0)
    assert (a_ == at).all()
    assert (b_ == bt).all()
    assert (eq == mask).all()


@pytest.mark.parametrize("dtype", [np.float32, np.float64, np.str_, np.bytes_, np.object_])
def test_dtype(a, a1, dtype):
    a = a.astype(dtype)
    a1 = a1.astype(dtype)

    a_, b_, eq = diff_aligned_2d(a, a1, 0)
    assert (a_ == a).all()
    assert (b_ == a1).all()
    assert (eq == (a == a1)).all()
