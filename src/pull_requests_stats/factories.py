import datetime

from . import models


def PullRequestFactory(author="jdoe"):
    return models.PullRequest(
        number=1,
        url="https://example.com/pull/1",
        author=author,
        created_at=datetime.datetime(2024, 1, 4, 12, 0),
        updated_at=datetime.datetime(2024, 1, 5, 18, 0),
        closed_at=None,
        comments=[],
        reviews=[],
        files=["src/foo.py", "tests/test_foo.py"],
        tags=[],
    )
