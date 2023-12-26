"""Get releases from Github and convert to markdown."""
from __future__ import annotations

from datetime import datetime
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

RELEASE_TEMPLATE = "# [{{release.name}}]({{release.html_url}})\n*Released at {{release.published_at.isoformat()}}*\n\n{{release.body}}"


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
        user_re = '@[a-zA-Z0-9-]+'
        issue_re = '#[0-9]+'

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


def get_releases_as_markdown(organisation_or_user: str, repository: str, token: str | None = None, release_template: str | None = RELEASE_TEMPLATE, github_api_url: str | None = None, match: str | None = None, autoprocess: bool | None = True):
    """Get the releases from github as a list of rendered markdown strings."""
    if github_api_url is not None:
        github_api_url = github_api_url.rstrip('/')
    api = GhApi(token=token, gh_host=github_api_url)
    releases = []
    for page in paged(api.repos.list_releases, organisation_or_user, repository, per_page=100):
        releases += page
    jinja_environment = JINJA_ENVIRONMENT_FACTORY.environment
    selected_releases = []
    for release in releases:
        # Convert the published_at to datetime object
        if not isinstance(release.published_at, datetime):
            if sys.version_info.major >= 3 and sys.version_info.minor < 11:
                release.published_at = parse(release.published_at)
            else:
                release.published_at = datetime.fromisoformat(release.published_at)
        if autoprocess is None or autoprocess:
            autoprocess_github_links(release)
        if (match and re.match(match, release.name) is not None) or not match:
            selected_releases.append(release)
    if release_template is None:
        release_template = RELEASE_TEMPLATE
    return [jinja_environment.from_string(release_template).render(release=release) for release in selected_releases]
