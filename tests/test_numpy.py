import numpy as np

from rdiff.chunk import Diff, Chunk
from rdiff.numpy import diff

from .util import np_chunk_eq


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