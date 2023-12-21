
mkdocs extension to autogenerate changelogs from github releases.

An ``mkdocs`` equivalent     to [sphinx_github_changelog](https://github.com/ewjoachim/sphinx-github-changelog).

## Why?
Easy releasing is key for rapid and robust software development. We use tag based releases, but want an easy way to generate the changelog automatically, enter [release drafter](https://github.com/release-drafter/release-drafter) and GitHub Releases.

[Release drafter](https://github.com/release-drafter/release-drafter) allows you to generate draft releases from your pull requests, and then use the release to generate the tag automatically, and include the release changelog in the release body. Assuming you've got good pull release hygiene, you can cut a new release by editing the draft GitHub Release and then pressing "Publish Release".

``mkdocs_github_changelog`` can then be used to generate the changelog in the ``mkdocs`` documentation automatically and without needing another commit.

## Using mkdocs_github_changelog

### Configuration

In the ``mkdocs.yml`` file, add the plugin and any configuration options to override the defaults:

```yaml

plugins:
    ...
    - mkdocs_github_changelog:
        token: !ENV GITHUB_TOKEN
        # Github token (needs repo scope for private repos, and may be worth setting for public repos due to rate limiting).
        github_api_url: <url>
        # URL for github api endpoint if not standard github.com (This is not tested on github enterprise server).
        release_template: <jinja2 str>
        # Jinja2 template string to override the default.
        match: '[0-9+].[0-9+].[0-9]+'
        # Regex string for matching the rleease name.
        autoprocess: True
        # Autoprocess the body for user and issue/pull request links
        enabled: True
        # Enable or disable the plugin.
```

!!! info

    The Github token can also be set through the ``GITHUB_TOKEN`` or ``GITHUB_JWT_TOKEN`` environment values (the client used for the api is [``ghapi``](https://ghapi.fast.ai/))

Then in the file you want to implement the changelog (e.g. ``changelog.md``):

```
markdown

::github-release-changelog <org>\<repo>
    base_indent: 2
    token: !ENV GITHUB_TOKEN
    github_api_url: <url>
    release_template: <jinja2 str>
    match: '[0-9+].[0-9+].[0-9]+'
    autoprocess: true
```

All of the options are optional when configuring, and the indent level can be set by using ``#`` in front of the ``::github-release-changelog`` line like normal markdown headings, but the ``base_indent`` option will override this.

The remaining optins can override/set the value specifically for that command (if you have multiple changelogs).

### Link autoprocesing

The body is autoprocessed to convert ``@<username>`` and ``#<issue>`` to github links into the repo unless the ``autoprocess`` config is set to false in the global or local config.

### Setting the template

The ``release_template`` option sets a ``jinja2`` template string to format the [``github`` ``release`` object (from the array of releases)](https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28#list-releases).

The default template should be good, but if you have specific needs, you can create a custom template and define it in either the global or local config. The release object is passed in as ``release``:

```
"# [{{release.name}}]({{release.html_url}})\n*Released at {{release.published_at.isoformat()}}*\n\n{{release.body}}"
```

#### Jinja Environment Customisation

If you need specific extensions in the jinja environment, you can add them in using a json encoded list on the ``MKDOCS_GITHUB_CHANGELOG_JINJA_EXTENSIONS`` environment variables.


You can also customise the jinja2 environment initialisation through the ``[project.entry-points."mkdocs_github_changelog.jinja_environment_factory"]`` entrypoint, and then setting the ``MKDOCS_GITHUB_CHANGELOG_JINJA_ENVIRONMENT_FACTORY`` environment variable to the name of the entrypoint.