**WORK IN PROGRESS**


This tool fetches pull requests from GitHub. Goals include:

- calculate the number of pull requests that have been commented or
  reviewed by a person;

- aggregate result by teams;

- show the proportion of pull requests that are reviewed by only one
  person;

- show the proportion of pull requests that are reviewed by members
  from a single team;

- etc.

**This is prototype. There is no user interface for now. It has
hard-coded filtering, see ``main.py`` and adjust as needed.**




Configuration file
==================

See `demo.config.toml`. Some options are not used (yet).


Usage
=====

0. Create a personal access token in GitHub, store it in a file, and
   reference that file in the configuration file.

1. Fetch pull requests from GitHub and store a JSON representation of
   each pull request in a ``dump/`` directory:

       $ pull_requests_stats -c config.toml fetch-from-github --outdir dump

   Obviously, this can take a while. If you need an update, you can
   regularly run the command with the ``--updated-after YYYY-MM-DD``
   option.

   Status: this part works. There is no error handling, though.

2. Load local data and calculate things:

       $ pull_requests_stats -c config.toml load-json --dir dump

   Status: this part is very much draft... If you want to try it out,
   add ``import pdb; pdb.set_trace()`` somewhere in ``load_json()``
   and play with the data. See ``models.py`` for the data structures.

   Example:

       >>> len([p for p in pull_requests if "dbaty" in {reviews_and_comments.author for reviews_and_comments in (p.reviews + p.comments)}])

3. Populate database. The idea here would be to replace step 2 above
   by a step that would load JSON data and update an SQL database.
   Then a (web?) user interface could perform predefined or custom SQL
   queries and show aggregated data, generate charts, etc.

   Status: not implemented.
