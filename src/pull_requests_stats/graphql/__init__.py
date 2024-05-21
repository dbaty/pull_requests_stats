import pathlib


def get(name: str) -> str:
    return (pathlib.Path(__file__).parent / f"{name}.graphql").read_text()
