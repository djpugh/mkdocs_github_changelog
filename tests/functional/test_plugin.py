from datetime import datetime
from functools import wraps
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
import webbrowser

from click.testing import CliRunner
from fastcore.net import HTTP403ForbiddenError, HTTP404NotFoundError
from mkdocs.__main__ import build_command
from nskit.common.contextmanagers import ChDir

from mkdocs_github_changelog import get_releases

# Offline test without github call

# Online test with github call



RELEASE_1 = '## Features\n Hello World ([#2](https://www.google.com))'
RELEASE_2 = '## Features\n Hello World ([#1](https://www.google.com))'

def mock_gh_api(func):

    @patch.object(get_releases, 'GhApi')
    @patch.object(get_releases, 'paged', autospec=True)
    @wraps(func)
    def mocked_call(self, paged, GhApi):
        release1_content = MagicMock()
        release1_content.body = RELEASE_1
        release1_content.name = '0.2.0'
        release1_content.html_url = 'https://www.google.com'
        release1_content.published_at = datetime(2023, 12, 1, 13, 46).astimezone().isoformat()

        release2_content = MagicMock()
        release2_content.body = RELEASE_2
        release2_content.name = '0.1.0'
        release2_content.html_url = 'https://www.google.com'
        release2_content.published_at = datetime(2023, 11, 1, 13, 46).astimezone().isoformat()

        def paged_mock(func, organisation_or_user, repository, *args, **kwargs):
            print('Mocked', organisation_or_user, repository)
            if organisation_or_user == 'abc' and repository == 'xyz':
                return [[release1_content, release2_content]]
            else:
                raise HTTP404NotFoundError(None, None, None)

        paged.side_effect = paged_mock
        GhApi().repos = MagicMock()
        GhApi().repos.list_releases = MagicMock()
        GhApi.reset_mock()
        return func(self, paged, GhApi, release1_content, release2_content)

    return mocked_call


class OfflineTest(unittest.TestCase):

    @property
    def index_md_ok(self):
        return """# Test

## ::github-release-changelog abc/xyz

### ::github-release-changelog abc/xyz

::github-release-changelog abc/xyz
    base_level: 4
"""

    @property
    def index_md_error(self):
        return """# Test

## ::github-release-changelog abc/a123

### ::github-release-changelog abc/a123

::github-release-changelog abc/a123
    base_level: 4
"""

    @property
    def mkdocs_yml(self):
        return """
site_name: mkdocs_github_changelog_test_repo
repo_url: https://github.com/djpugh/mkdocs_github_changelog

edit_uri: blob/main/docs/source/

docs_dir: ./source
site_dir: ./html
nav:
 - index.md

theme:
  name: material

plugins:
  - search
  - mkdocs_github_changelog
"""

    @mock_gh_api
    def test_mkdocs(self, *args):
        with ChDir():
            mkdocs_config = Path('mkdocs.yml')
            mkdocs_config.write_text(self.mkdocs_yml)
            index = Path('source/index.md')
            index.parent.mkdir(parents=True, exist_ok=True)
            index.write_text(self.index_md_ok)
            runner = CliRunner(echo_stdin=True)
            resp = runner.invoke(build_command, catch_exceptions=False)
            self.assertEqual(resp.exit_code, 0, resp.exc_info)
            self.assertTrue(Path('html').exists())
            # webbrowser.open(str(Path('html', 'index.html').absolute()))
            index_html = Path('html', 'index.html')
            webbrowser.open(str(index_html.absolute()))
            contents = index_html.read_text(encoding="utf8")
            self.assertIn('<h3 id="020"><a href="https://www.google.com">0.2.0</a></h3>\n<p><em>Released at 2023-12-01T13:46:00+00:00</em>', contents)
            self.assertIn('<h4 id="020_1"><a href="https://www.google.com">0.2.0</a></h4>\n<p><em>Released at 2023-12-01T13:46:00+00:00</em>', contents)
            self.assertIn('<h1 id="020_2"><a href="https://www.google.com">0.2.0</a></h1>\n<p><em>Released at 2023-12-01T13:46:00+00:00</em>', contents)
            self.assertIn('<h3 id="010"><a href="https://www.google.com">0.1.0</a></h3>\n<p><em>Released at 2023-11-01T13:46:00+00:00</em>', contents)
            self.assertIn('<h4 id="010_1"><a href="https://www.google.com">0.1.0</a></h4>\n<p><em>Released at 2023-11-01T13:46:00+00:00</em>', contents)
            self.assertIn('<h1 id="010_2"><a href="https://www.google.com">0.1.0</a></h1>\n<p><em>Released at 2023-11-01T13:46:00+00:00</em>', contents)
            self.assertIn('<h4 id="features">Features</h4>', contents)
            self.assertIn('<h5 id="features_2">Features</h5>', contents)
            self.assertIn('<h2 id="features_4">Features</h2>', contents)

    @mock_gh_api
    def test_mkdocs_error(self, *args):
        with ChDir():
            mkdocs_config = Path('mkdocs.yml')
            mkdocs_config.write_text(self.mkdocs_yml)
            index = Path('source/index.md')
            index.parent.mkdir(parents=True, exist_ok=True)
            index.write_text(self.index_md_error)
            runner = CliRunner(echo_stdin=True)
            with self.assertRaises(HTTP404NotFoundError):
                runner.invoke(build_command, catch_exceptions=False)
            self.assertFalse(Path('html').exists())



class OnlineTest(unittest.TestCase):

    @property
    def index_md(self):
        return """# Test

## ::github-release-changelog djpugh/fastapi_aad_auth

### ::github-release-changelog djpugh/fastapi_aad_auth

::github-release-changelog djpugh/fastapi_aad_auth
    base_level: 4
"""

    @property
    def mkdocs_yml(self):
        return """
site_name: mkdocs_github_changelog_test_repo
repo_url: https://github.com/djpugh/mkdocs_github_changelog

edit_uri: blob/main/docs/source/

docs_dir: ./source
site_dir: ./html
nav:
 - index.md

theme:
  name: material

plugins:
  - search
  - mkdocs_github_changelog
"""

    @staticmethod
    def skip_if_rate_limited():
        raise unittest.SkipTest('Rate Limited')

    def test_mkdocs(self, *args):
        with ChDir():
            mkdocs_config = Path('mkdocs.yml')
            mkdocs_config.write_text(self.mkdocs_yml)
            index = Path('source/index.md')
            index.parent.mkdir(parents=True, exist_ok=True)
            index.write_text(self.index_md)
            runner = CliRunner(echo_stdin=True)
            try:
                resp = runner.invoke(build_command, catch_exceptions=False)
            except HTTP403ForbiddenError:
                self.skip_if_rate_limited()
            self.assertEqual(resp.exit_code, 0, resp.exc_info)
            self.assertTrue(Path('html').exists())

            index_html = Path('html', 'index.html')
            webbrowser.open(str(index_html.absolute()))
            contents = index_html.read_text(encoding="utf8")
            self.assertIn('<h3 id="release-0122"><a href="https://github.com/djpugh/fastapi_aad_auth/releases/tag/0.1.22">Release 0.1.22</a></h3>', contents)
            self.assertIn('<p><em>Released at 2022-04-17T14:22:48+00:00</em>', contents)
            self.assertIn('<h4 id="release-0122_1"><a href="https://github.com/djpugh/fastapi_aad_auth/releases/tag/0.1.22">Release 0.1.22</a></h4>', contents)
            self.assertIn('<h1 id="release-0122_2"><a href="https://github.com/djpugh/fastapi_aad_auth/releases/tag/0.1.22">Release 0.1.22</a></h1>', contents)
            self.assertIn('<h4 id="features">🚀 Features</h4>', contents)

    # Include handling for env based token handling (if os.environ.GITHUB_TOKEN)
