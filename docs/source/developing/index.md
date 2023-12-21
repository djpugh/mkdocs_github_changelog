# Contributing to mkdocs_github_changelog

We love contributions to ``mkdocs_github_changelog``

## Issues

Please raise issues, queries or discussions [here](https://github.com/djpugh/mkdocs_github_changelog/issues).

## Contributing to the codebase

### Installation and setup

Make sure you have the prerequisites installed (for adding code):
* Python (Versions from 3.8)
* virtualenv or another virtual environment tool
* git

Create and activate a virtual environment.

Install ``mkdocs_github_changelog``:

```
# Install mkdocs_github_changelog as an editable install with the dev dependencies
pip install -e ".[dev]"
```

The codebase uses ``pre-commit``, so please use ``pre-commit install`` and ``pre-commit install-hooks`` to make sure the pre-commit hooks are installed correctly.

#### Checkout a branch and make changes

Create a branch to make  your changes in:
```
# Checkout a new branch and make your changes
git checkout -b my-branch
# Make your changes...
```

#### Run tests and linting

``mkdocs_github_changelog`` uses [``nox``](https://nox.thea.codes/en/stable/) for running tests.
```
# You can either use session tags with the -s flag
nox -s test lint
# There are also sessions: security, types, pre-commit

# or the -t lint and test tags
nox -t lint
# This includes lint, pre-commit, security (bandit and pipenv check), types

nox -t test
```

#### Build docs

If you have edited the docs (or signatures/classes), please check the docs:
```
nox -t docs
```

They will be output to ``build/docs``


#### Commit and push your changes

Commit your changes, push your branch, and create a pull request to the main [mkdocs_github_changelog repo](https://github.com/djpugh/mkdocs_github_changelog), and please include clear information in the pull request for review.