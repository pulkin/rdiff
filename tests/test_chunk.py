from rdiff.chunk import Diff, Chunk


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
