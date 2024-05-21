import re
import typing as T

from . import configuration
from . import models


class AutoTagException(Exception):
    pass


def autotag(config: configuration.Config, pr: models.PullRequest) -> set[str]:
    tags = set()
    for tag, tag_config in config.autotags.items():
        if _tag_matches(pr, tag_config["rules"]):
            try:
                tags.add(tag)
            except AutoTagException as exc:
                raise ValueError(f"Error in autotag {tag}: {exc}")
    return tags


def _tag_matches(pr: models.PullRequest, rules: list[dict]) -> bool:
    for rule in rules:
        matches = True
        for attribute, expr in rule.items():
            matches &= AttributeRule(attribute, pr).apply(expr)
            if not matches:
                break
        if matches:
            return True

    return False


class AttributeRule:
    def __init__(self, attribute: str, pr: models.PullRequest):
        self.attribute = attribute
        if self.attribute == "path":
            self.pr_values = pr.files
        elif self.attribute == "author":
            self.pr_values = [pr.author]
        else:
            raise AutoTagException(f"unknown attribute '{attribute}'")

    def apply(self, expr: dict) -> bool:
        if len(expr) != 1:
            raise AutoTagException("malformed '{self.attribute}' rule")

        comparator_name, rule_value = list(expr.items())[0]
        comparator = getattr(self, comparator_name)
        if not comparator:
            raise AutoTagException(f'unknown comparator "{comparator}"')

        for pr_value in self.pr_values:
            if comparator(pr_value, rule_value):
                return True
        return False

    def matches(cls, pr_value: T.Any, rule_value: T.Any):
        if not isinstance(rule_value, str):
            raise AutoTagException(f'expected pattern, got "{rule_value}" instead')
        pattern = rule_value
        return bool(re.match(pattern, pr_value))

    def equals(cls, pr_value: T.Any, value: T.Any):
        if not isinstance(value, str):
            raise AutoTagException(f'expected string, got "{value}" instead')
        return pr_value == value
