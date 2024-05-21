import dataclasses
from pull_requests_stats import factories
from pull_requests_stats import tagging


@dataclasses.dataclass
class FakeConfig:
    autotags: list


class TestAutotag:
    def test_basics(self):
        pr = factories.PullRequestFactory(author="dependabot")
        config = FakeConfig(
            autotags={
                "has-modified-tests": {"rules": [{"path": {"matches": "tests/.*"}}]},
                "has-modified-ruby": {"rules": [{"path": {"matches": ".*\.rb"}}]},
                "made-by-dependabot": {"rules": [{"author": {"equals": "dependabot"}}]},
            }
        )

        tags = tagging.autotag(config, pr)

        assert tags == {"has-modified-tests", "made-by-dependabot"}


# FIXME: add more tests for specific behaviour, error catchers, etc.
