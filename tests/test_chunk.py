from sdiff.chunk import Diff, Chunk, Item


def test_diff():
    diff = Diff(
        ratio=0,
        diffs=[
            Chunk("hello", "hi", False),
            Chunk("world", "world", True),
        ]
    )
    assert diff.get_a() == "helloworld"
    assert diff.get_b() == "hiworld"


def test_important():
    diff_345 = Diff(ratio=2 / 3, diffs=[
        Chunk(data_a=[3], data_b=[3], eq=True),
        Chunk(data_a=[4], data_b=[9], eq=False),
        Chunk(data_a=[5], data_b=[5], eq=True),
    ])
    diff = Diff(
        ratio=5. / 6,
        diffs=[
            Chunk(data_a=[[0, 1, 2]], data_b=[[0, 1, 2]], eq=True),
            Chunk(data_a=[[3, 4, 5]], data_b=[[3, 9, 5]], eq=[diff_345]),
            Chunk(data_a=[[6, 7, 8]], data_b=[[6, 7, 8]], eq=True),
            Chunk(data_a=[[9, 10, 11]], data_b=[[19, 20, 21]], eq=False),
            Chunk(data_a=[[12, 13, 14], [15, 16, 17]], data_b=[[12, 13, 14], [15, 16, 17]], eq=True),
        ]
    )
    assert list(diff.iter_important()) == [
        1,
        Item(a=[3, 4, 5], b=[3, 9, 5], ix_a=1, ix_b=1, diff=diff_345),
        1,
        Item(a=[9, 10, 11], b=None, ix_a=3, ix_b=None),
        Item(a=None, b=[19, 20, 21], ix_a=None, ix_b=3),
        2,
    ]
    assert list(diff.iter_important(context_size=1)) == [
        Item(a=[0, 1, 2], b=[0, 1, 2], ix_a=0, ix_b=0),
        Item(a=[3, 4, 5], b=[3, 9, 5], ix_a=1, ix_b=1, diff=diff_345),
        Item(a=[6, 7, 8], b=[6, 7, 8], ix_a=2, ix_b=2),
        Item(a=[9, 10, 11], b=None, ix_a=3, ix_b=None),
        Item(a=None, b=[19, 20, 21], ix_a=None, ix_b=3),
        Item(a=[12, 13, 14], b=[12, 13, 14], ix_a=4, ix_b=4),
        1,
    ]
