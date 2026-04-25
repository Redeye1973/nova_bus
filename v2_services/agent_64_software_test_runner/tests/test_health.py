from pathlib import Path


def test_output_root_placeholder():
    p = Path(r"L:\! 2 Nova v2  OUTPUT !\Z New NOva 1st test")
    assert isinstance(p, Path)
