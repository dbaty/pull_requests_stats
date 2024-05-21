import pathlib


def get(name: str) -> str:
    return (pathlib.Path(__file__).parent / f"{name}.sql").read_text()
