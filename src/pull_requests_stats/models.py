import dataclasses
import datetime

from . import configuration
from . import utils


LOGIN_GHOST = "ghost"  # a user who deleted their GitHub account


@dataclasses.dataclass
class Action:
    author: str
    timestamp: datetime.datetime


@dataclasses.dataclass
class PullRequest:
    number: str
    url: str
    author: str
    created_at: datetime.datetime
    closed_at: datetime.datetime | None
    updated_at: datetime.datetime
    comments: list[Action]
    reviews: list[Action]
    files: set[str]
    tags: set[str]

    @classmethod
    def from_api(cls, d: dict, config: configuration.Config):
        from . import tagging

        comments, reviews = cls._comments_and_reviews_from_api(d, config)
        pr = cls(
            number=d["number"],
            url=d["permalink"],
            author=get_login(d["author"]),
            created_at=utils.from_github_formatted_datetime(d["createdAt"]),
            closed_at=utils.from_github_formatted_datetime(d["closedAt"]),
            updated_at=utils.from_github_formatted_datetime(d["updatedAt"]),
            comments=comments,
            reviews=reviews,
            files={node["path"] for node in (d["files"] or {}).get("nodes", ())},
            tags=[],  # populated below
        )
        pr.tags = tagging.autotag(config, pr)
        return pr

    @classmethod
    def _comments_and_reviews_from_api(
        cls, d: dict, config: configuration.Config
    ) -> tuple[list[Action], list[Action]]:
        pull_request_author = get_login(d["author"])
        reviews = []
        for review in sorted(
            (r for r in d["reviews"]["nodes"] if r["submittedAt"]),
            key=lambda r: r["submittedAt"],
            reverse=True,
        ):
            review_author = get_login(review["author"])
            if review_author in config.logins_to_ignore:
                continue
            if review_author == pull_request_author:
                continue
            if review_author in {r.author for r in reviews}:
                continue
            reviews.append(
                Action(
                    author=review_author,
                    timestamp=utils.from_github_formatted_datetime(
                        review["submittedAt"]
                    ),
                )
            )

        comments = []
        for comment in sorted(
            (c for c in d["comments"]["nodes"] if c["publishedAt"]),
            key=lambda c: c["publishedAt"],
            reverse=True,
        ):
            comment_author = get_login(comment["author"])
            if comment_author in config.logins_to_ignore:
                continue
            if not comment_author:
                continue
            if comment_author == pull_request_author:
                continue
            # Ignore comments from persons who also have reviewed.
            if comment_author in {r.author for r in reviews}:
                continue
            if comment_author in {c.author for c in comments}:
                continue
            comments.append(
                Action(
                    author=comment_author,
                    timestamp=utils.from_github_formatted_datetime(
                        comment["publishedAt"]
                    ),
                )
            )
        return comments, reviews


@dataclasses.dataclass
class Team:
    name: str


@dataclasses.dataclass
class TeamMembership:
    login: str
    team: Team
    timespan: tuple[datetime.datetime, datetime.datetime | None]


def get_login(author: dict | None) -> str:
    if not author:
        return LOGIN_GHOST
    return author["login"]
