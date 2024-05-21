"""FIXME
"""

import argparse
import collections
import dataclasses
import datetime
import json
import pathlib
import requests
import sys
import time

from . import configuration
from . import graphql
from . import sql
from . import models
from . import utils


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return json.JSONEncoder.default(self, obj)


def main() -> None:
    args = parse_args().__dict__
    callback = args.pop("callback")
    config = configuration.Config.from_path(args.pop("config"))
    callback(config, **args)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        metavar="PATH",
        required=True,
        type=pathlib.Path,
    )

    subparsers = parser.add_subparsers()

    # fetch-from-github
    parser_fetch_from_github = subparsers.add_parser(
        "fetch-from-github",
        help="Fetch data from GitHub and store it in intermediary JSON files",
    )
    parser_fetch_from_github.add_argument(
        "--outdir",
        dest="outdir",
        type=pathlib.Path,
        required=True,
        help="Path of directory where to store data",
    )
    parser_fetch_from_github.add_argument(
        "--updated-after",
        dest="updated_after",
        type=datetime.datetime.fromisoformat,
        required=False,
        default="1970-01-01T00:00:00",
        help="Fetch pull requests that have been updated after the given ISO-formatted timestamp. By default, fetch all data.",
    )
    parser_fetch_from_github.set_defaults(callback=fetch_from_github)

    parser_load_json = subparsers.add_parser(
        "load-json",
        help="Load data from JSON files",
    )
    parser_load_json.add_argument(
        "--dir",
        dest="json_dir",
        type=pathlib.Path,
        required=True,
        help="Path of directory from where data is loaded",
    )
    parser_load_json.set_defaults(callback=load_json)

    # init-database
    parser_init_database = subparsers.add_parser(
        "init-database", help="Initialize the SQLite database."
    )
    parser_init_database.set_defaults(callback=init_database)

    # populate-database
    parser_populate_database = subparsers.add_parser(
        "populate-database", help="Populate the SQLite database."
    )
    parser_populate_database.set_defaults(callback=populate_database)

    return parser.parse_args(sys.argv[1:])


def fetch_from_github(
    config: configuration.Config,
    updated_after: datetime.datetime,
    outdir: pathlib.Path,
) -> list[models.PullRequest]:
    """Fetch pull request data from GitHub and export to a JSON file."""
    if outdir.exists():
        if not outdir.is_dir():
            sys.exit("Output directory `{outdir}` is a file, should be a directory.")
    else:
        outdir.mkdir(parents=True)

    after_cursor = None
    n_pull_requests = 0
    while 1:
        response = requests.post(
            "https://api.github.com/graphql",
            json={
                "query": graphql.get("get_pull_requests"),
                "variables": {
                    "repositoryOwner": config.owner,
                    "repositoryName": config.repository,
                    "afterCursor": after_cursor,
                },
            },
            headers={
                "Authorization": f"Bearer {config.authentication_token}",
            },
        )
        if response.status_code != 200:
            sys.exit(f"Got {response.status_code} HTTP response")
        data = response.json()["data"]["repository"]["pullRequests"]
        pull_requests = data["nodes"]
        for pull_request in pull_requests:
            filename = f"{pull_request['number']}.json"
            with open(outdir / filename, "w") as fp:
                json.dump(pull_request, fp)
        after_cursor = data["pageInfo"]["endCursor"]
        n_pull_requests += len(pull_requests)
        print(f"\rGot {n_pull_requests} pull requests...", end="")
        if (
            not data["pageInfo"]["hasNextPage"]
            or not pull_requests
            or updated_after
            > utils.from_github_formatted_datetime(pull_requests[0]["updatedAt"])
        ):
            print()  # final '\n' because the previous `print` does not have one.
            break
        time.sleep(0.1)


def load_json(config: configuration.Config, json_dir: pathlib.Path):
    pull_requests = []
    for path in json_dir.iterdir():
        if path.suffix == ".json":
            with path.open() as fp:
                pr = models.PullRequest.from_api(json.load(fp), config)
                pull_requests.append(pr)

    __import__("pdb").set_trace()
    cutoff = datetime.datetime(2024, 1, 1)
    print(f"/!\ Cutoff = {cutoff}")
    backend_prs = [
        pr
        for pr in pull_requests
        if "backend" in pr.tags and "dependabot" not in pr.tags
        # FIXME: DEBUG ONLY
        if pr.created_at > cutoff
    ]
    prs_by_bucket = collections.defaultdict(list)
    for pr in backend_prs:
        bucket = utils.get_week_start(pr.created_at)
        prs_by_bucket[bucket].append(pr)

    counts = [len(prs) for _bucket, prs in sorted(prs_by_bucket.items())]
    more_than_one_reviewer = [
        len([pr for pr in prs if len(pr.comments + pr.reviews) >= 2]) / len(prs) * 100
        for _bucket, prs in sorted(prs_by_bucket.items())
    ]

    x_values = [bucket.isoformat() for bucket in sorted(prs_by_bucket)]
    import plotly.subplots
    import plotly.graph_objects

    fig = plotly.subplots.make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        plotly.graph_objects.Bar(
            x=x_values,
            y=counts,
            name="Nombre de pull requests par semaine",
            marker={
                "color": "cornsilk",
            },
        ),
        secondary_y=False,
    )
    fig.add_trace(
        plotly.graph_objects.Line(
            x=x_values,
            y=more_than_one_reviewer,
            name="Proportion de PR avec plus d'une relecture",
            marker={
                "color": "cornflowerblue",
            },
        ),
        secondary_y=True,
    )
    fig.write_image("chart.svg")


def init_database(config: configuration.Config):
    queries = sql.get("setup")


def populate_database():
    pass


if __name__ == "__main__":
    main()
