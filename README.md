# mkdocs_github_changelog


mkdocs extension to autogenerate changelog from github


## Introduction


## Contributing

To see the contribution guidelines, see [docs/source/developing/index.md](docs/source/developing/index.md).

## Setting up for development

Create a virtual environment.
Install the package using ``pip install -e .[dev]``


Then add code to the package as appropriate - submodules can be created under ``src/mkdocs_github_changelog``
Tests can be added to the tests folder



### CI

There are a set of CI checks:

* lint: ``nox -t lint``
* test: ``nox -t test``
* build: ``nox -t build``

specific subfolders can be passed to the test tag in nox: ``nox -t test -- <subfolder1> <subfolder2>``




## Versioning

It is important to track and version code, and to aid that with the python packages and models, ``setuptools_scm`` is used.
This links the version reported at ``__version__`` to the git tag (+ commit hash if appropriate), to reduce the amount of
places that need editing when changing versions.

For describing versions we are using semantic versioning ``<major>.<minor>.<patch>``. Increment the:

* ``<major>`` version when you make incompatible API changes,
* ``<minor>`` version when you add functionality in a backwards-compatible manner, and
* ``<patch>`` version when you make backwards-compatible bug fixes.

There are also codes for pre-releases and other descriptions (see https://semver.org/)

To create a version, use ``git tag <major>.<minor>.<patch>`` and then make sure to push that tag with ``git push origin <major>.<minor>.<patch>``,
or an equivalent tagging tool (e.g. Github releases).





------------

Repo created from nskit.recipes.python.package:PackageRecipe (version 0.0.post1.dev14+g7e85d99.d20231220) using ``nskit``.

