"""This module contains the MkDocs plugin.

It creates a Markdown extension ([`GithubReleaseChangelogExtension`][mkdocs_github_changelog.extension.GithubReleaseChangelogExtension]),
and adds it to `mkdocs` during the [`on_config` event hook](https://www.mkdocs.org/user-guide/plugins/#on_config).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mkdocs.config import Config
from mkdocs.config import config_options as opt
from mkdocs.plugins import BasePlugin

from mkdocs_github_changelog.extension import GithubReleaseChangelogExtension

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig


class PluginConfig(Config):
    """Configuration options for `mkdocs_github_changelog` in `mkdocs.yml`."""
    token = opt.Optional(opt.Type(str))
    """Github token (needs repo scope for private repos, and may be worth setting for public repos due to rate limiting)."""
    github_api_url = opt.Optional(opt.URL())
    """URL for github api endpoint if not standard github.com (This is not tested on github enterprise server)."""
    release_template = opt.Optional(opt.Type(str))
    """Jinja2 template string to override the default."""
    match = opt.Optional(opt.Type(str))
    """Regex string for matching the rleease name."""
    autoprocess = opt.Type(bool, default=True)
    """Autoprocess the release bodies for issue and username links."""
    enabled = opt.Type(bool, default=True)
    """Enable or disable the plugin."""


class MkdocsGithubChangelogPlugin(BasePlugin[PluginConfig]):
    """`mkdocs` plugin to provide the changelog from github releases."""

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        """Initialises the extension if the plugin is enabled."""
        if self.config.enabled:
            github_release_changelog_extension = GithubReleaseChangelogExtension(self.config)
            config.markdown_extensions.append(github_release_changelog_extension)  # type: ignore[arg-type]
        return config
