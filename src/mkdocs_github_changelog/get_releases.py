"""Get releases from Github and convert to markdown."""
from __future__ import annotations

from datetime import datetime
import inspect
import json
import os
import re
import sys

if sys.version_info.major >= 3 and sys.version_info.minor >= 10:
    from importlib.metadata import entry_points
else:
    from backports.entry_points_selectable import entry_points

if sys.version_info.major >= 3 and sys.version_info.minor < 11:
    from dateutil.parser import parse


from ghapi.all import GhApi, paged
from jinja2 import Environment

from mkdocs_github_changelog import logger

RELEASE_TEMPLATE = "# [{{release.name}}]({{release.html_url}})\n*Released at {{release.published_at.isoformat()}}*\n\n{{release.body}}"


def _supports_sync() -> bool:
    """Whether the installed ghapi accepts the ``sync`` constructor flag."""
    return 'sync' in inspect.signature(GhApi.__init__).parameters


def _make_api(token: str | None, github_api_url: str | None) -> GhApi:
    """Build a GhApi that returns results rather than coroutines.

    ghapi 2.0 made operation calls asynchronous by default, so ``paged(...)``
    yields an async generator and iterating it raises ``'async_generator' object
    is not iterable``. The same release added a ``sync`` flag selecting a
    synchronous transport.

    The flag does not exist on ghapi 1.x, which accepts arbitrary keyword
    arguments without necessarily ignoring them, so it is passed only when the
    installed signature declares it.
    """
    kwargs = {'token': token, 'gh_host': github_api_url}
    if _supports_sync():
        kwargs['sync'] = True
    return GhApi(**kwargs)


class _EnvironmentFactory():
    """Jinja2 Environment Factory to allow for extension/customisation.

    Adapted from https://djpugh.github.io/nskit.
    """

    def __init__(self):
        """Initialise the factory."""
        self._environment = None

    @property
    def environment(self) -> Environment:
        """Handle caching the environment object so it is lazily initialised."""
        if self._environment is None:
            self._environment = self.get_environment()
            self.add_extensions(self._environment)
        return self._environment

    def add_extensions(self, environment: Environment):
        """Add Extensions to the environment object."""
        # Assuming no risk of extension clash
        extensions = []
        # Load from JSON
        for ext in json.loads(os.environ.get('MKDOCS_GITHUB_CHANGELOG_JINJA_EXTENSIONS', '[]')):
            extensions.append(ext)
        for extension in list(set(extensions)):
            environment.add_extension(extension)

    def get_environment(self) -> Environment:
        """Get the environment object based on the env var."""
        selected_method = os.environ.get('MKDOCS_GITHUB_CHANGELOG_JINJA_ENVIRONMENT_FACTORY', None)
        if selected_method is None or selected_method.lower() == 'default':
            # This is our simple implementation
            selected_method = 'default'
        for ep in entry_points().select(group='mkdocs_github_changelog.jinja_environment_factory', name=selected_method):
            return ep.load()()

    @staticmethod
    def default_environment():
        """Get the default environment object."""
        return Environment()  # nosec B701


JINJA_ENVIRONMENT_FACTORY = _EnvironmentFactory()


def autoprocess_github_links(release):
    """We process the release to convert #xy and @abc links."""
    if not getattr(release, 'processed', False):
        base_url = release.html_url.split('releases')[0]
        # We also want to parse this to get the
        root_url = '/'.join(base_url.split('/')[:-3])
        user_re = r'@[a-zA-Z\d-]+'
        issue_re = r'#[\d]+'

        def github_user_link(match_obj):
            user_name = match_obj.string[match_obj.start(): match_obj.end()]
            user_link = user_name.replace('@', root_url+'/')
            return f'[{user_name}]({user_link})'

        def github_issue_link(match_obj):
            issue_key = match_obj.string[match_obj.start(): match_obj.end()]
            issue_link = issue_key.replace('#', base_url+'issues/')
            return f'[{issue_key}]({issue_link})'

        release.body = re.sub(user_re, github_user_link, release.body)
        release.body = re.sub(issue_re, github_issue_link, release.body)
        release.processed = True
    return release


def _coerce_published_at(release) -> datetime | None:
    """Return a release's ``published_at`` as a datetime, or None if it has none.

    The value is checked by type rather than by Python version. An unpublished
    release has no timestamp at all: the API returns ``null``, which ghapi
    surfaces as an empty ``AttrDict`` rather than ``None``, so neither a
    ``datetime`` nor ``str`` check matches and there is nothing to parse.

    The version branch below is only about *how* to parse a string:
    ``fromisoformat`` cannot handle the trailing ``Z`` of a GitHub timestamp
    before 3.11, so dateutil is used there.
    """
    value = getattr(release, 'published_at', None)
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        if sys.version_info.major >= 3 and sys.version_info.minor < 11:
            return parse(value)
        return datetime.fromisoformat(value)
    return None


def _process_releases(
    releases,
    match: str | None = None,
    autoprocess: bool = True,
    include_prereleases: bool = False,
):
    selected_releases = []
    for release in releases:
        # Drafts are unpublished, so they have no published_at and an empty
        # name; they render as a broken, dateless entry and do not belong in a
        # changelog. Skipping them also avoids failing the whole build on the
        # missing timestamp.
        if getattr(release, 'draft', False):
            logger.debug(f'Skipping draft release {release.html_url}')
            continue
        # A prerelease is published, so it renders fine, but it is usually noise
        # in a changelog -- excluded unless asked for.
        if not include_prereleases and getattr(release, 'prerelease', False):
            logger.debug(f'Skipping prerelease {release.html_url}')
            continue
        published_at = _coerce_published_at(release)
        if published_at is None:
            # Defensive: a published release should always carry a timestamp, so
            # warn rather than fail the build if one somehow does not.
            logger.warning(f'Skipping release with no published_at: {release.html_url}')
            continue
        release.published_at = published_at
        if autoprocess is None or autoprocess:
            autoprocess_github_links(release)
        if (match and re.match(match, release.name) is not None) or not match:
            selected_releases.append(release)
    return selected_releases


def get_releases_as_markdown(
    organisation_or_user: str,
    repository: str,
    token: str | None = None,
    release_template: str | None = RELEASE_TEMPLATE,
    github_api_url: str | None = None,
    match: str | None = None,
    autoprocess: bool | None = True,
    include_prereleases: bool | None = False
):
    """Get the releases from github as a list of rendered markdown strings."""
    if github_api_url is not None:
        github_api_url = github_api_url.rstrip('/')
    logger.info('Getting releases from github')
    api = _make_api(token, github_api_url)
    releases = []
    for page in paged(api.repos.list_releases, organisation_or_user, repository, per_page=100):
        releases += page
    logger.info(f'Processing releases from github, {len(releases)} found')
    jinja_environment = JINJA_ENVIRONMENT_FACTORY.environment
    selected_releases = _process_releases(
        releases,
        match=match,
        autoprocess=autoprocess,
        include_prereleases=include_prereleases,
    )
    if release_template is None:
        release_template = RELEASE_TEMPLATE
    logger.info(f'Rendering releases from github, {len(releases)} selected')
    return [jinja_environment.from_string(release_template).render(release=release) for release in selected_releases]
