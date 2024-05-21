import dataclasses
import pathlib

try:
    import tomllib
except ImportError:  # `tomllib` appeared in Python 3.11
    import tomli as tomllib


@dataclasses.dataclass
class Config:
    owner: str
    repository: str
    authentication_token: str
    autotags: dict
    logins_to_ignore: list[str]

    @classmethod
    def from_path(cls, path: pathlib.Path) -> "Config":
        with path.open("rb") as fp:
            configuration = tomllib.load(fp)
        authentication_token = (
            pathlib.Path(configuration["github"]["token_path"]).read_text().strip()
        )
        return cls(
            owner=configuration["github"]["owner"],
            repository=configuration["github"]["repository"],
            authentication_token=authentication_token,
            logins_to_ignore=configuration["team"]["logins_to_ignore"],
            autotags=configuration["autotags"],
        )
