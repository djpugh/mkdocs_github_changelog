"""Defines the extension for processing a markdown block to get the github release information.

Uses a Markdown [block processor](https://python-markdown.github.io/extensions/api/#blockprocessors)
that looks for on '::github-release-changelog <org_or_user>/<repo>'.

The specifics can be configured with YAML configuration in the block, and include !ENV flags:

```yaml
::github-changelog <org_or_user>/<repo>
    # Set the Github token - Needed for private repos, can be set globally as well.
    token: !ENV GITHUB_TOKEN

    # Set the base indent to work from - optional, can use the heading of the block instead.
    base_indent: 2

    # Set the release template to process the release into as an Jinja2 template (optional) (the github api response is passed in as release)
    release_template: "{{release.title}}"

    # Set the github API url for e.g. self-hosted enterprise - optional (and not tested on those)
    github_api_url: https://api.github.com

```
"""

from __future__ import annotations

import re
from typing import Any, MutableSequence, TYPE_CHECKING
from xml.etree.ElementTree import Element  # nosec: B405

from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from mkdocs.utils.yaml import get_yaml_loader, yaml_load

from mkdocs_github_changelog.get_releases import get_releases_as_markdown

if TYPE_CHECKING:
    from markdown import Markdown
    from markdown.blockparser import BlockParser


class GithubReleaseChangelogProcessor(BlockProcessor):
    """Changelog Markdown block processor."""

    regex = re.compile(r"^(?P<heading>#{1,6} *|)::github-release-changelog ?(?P<org>[a-zA-Z0-9-]+?)\/(?P<repo>.+?) *$", flags=re.MULTILINE)

    def __init__(
        self,
        parser: BlockParser,
        config: dict,
    ) -> None:
        """Initialize the processor."""
        super().__init__(parser=parser)
        self._config = config

    def test(self, parent: Element, block: str) -> bool:  # noqa: U100
        """Match the extension instructions."""
        return bool(self.regex.search(block))

    def run(self, parent: Element, blocks: MutableSequence[str]) -> None:
        """Run code on the matched blocks to get the markdown."""
        block = blocks.pop(0)
        match = self.regex.search(block)

        if match:
            if match.start() > 0:
                self.parser.parseBlocks(parent, [block[: match.start()]])
            # removes the first line
            block = block[match.end() :]

        block, the_rest = self.detab(block)
        if the_rest:
            # This block contained unindented line(s) after the first indented
            # line. Insert these lines as the first block of the master blocks
            # list for future processing.
            blocks.insert(0, the_rest)

        if match:
            heading_level = match["heading"].count("#")
            # We are going to process the markdown from the releases and then
            # insert it back into the blocks to be processed as markdown
            block = self._process_block(match.groupdict()['org'], match.groupdict()['repo'], block, heading_level)
            blocks.insert(0, block)
        return False

    def _process_block(
        self,
        org: str,
        repo: str,
        yaml_block: str,
        heading_level: int = 0,
    ) -> str:
        """Process a block."""
        config = yaml_load(yaml_block, loader=get_yaml_loader()) or {}
        if heading_level is None:
            heading_level = 0
        base_indent = config.get('base_indent', heading_level)
        token = config.get('token', self._config.get('token', None))
        github_api_url = config.get('github_api_url', self._config.get('github_api_url', None))
        release_template = config.get('release_template', self._config.get('release_template', None))
        match = config.get('match', self._config.get('match', None))
        autoprocess = config.get('autoprocess', self._config.get('autoprocess', True))
        block = '\n\n'.join(get_releases_as_markdown(
            organisation_or_user=org,
            repository=repo,
            token=token,
            release_template=release_template,
            github_api_url=github_api_url,
            match=match,
            autoprocess=autoprocess
            ))
        # We need to decrease/increase the base indent level
        if base_indent > 0:
            block = block.replace('# ', ('#'*base_indent)+'# ')
        return block


class GithubReleaseChangelogExtension(Extension):
    """The Markdown extension."""

    def __init__(self, config: dict, **kwargs: Any) -> None:
        """Initialize the object."""
        super().__init__(**kwargs)
        self._config = config

    def extendMarkdown(self, md: Markdown) -> None:
        """Register the extension.

        Add an instance of [`GithubReleaseChangelogProcessor`][mkdocs_github_changelog.extension.GithubReleaseChangelogProcessor]
        to the Markdown parser.
        """
        md.parser.blockprocessors.register(
            GithubReleaseChangelogProcessor(md.parser, self._config),
            "github_release_changelog",
            priority=75,  # Right before markdown.blockprocessors.HashHeaderProcessor
        )
