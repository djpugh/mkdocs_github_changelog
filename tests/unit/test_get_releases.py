from datetime import datetime
from functools import wraps
import json
import unittest
from unittest.mock import call, DEFAULT, MagicMock, patch

from fastcore.net import HTTP404NotFoundError
from jinja2 import Environment
from nskit.common.contextmanagers import Env, TestExtension

from mkdocs_github_changelog import get_releases

from mkdocs_github_changelog.get_releases import (
    _EnvironmentFactory,
    autoprocess_github_links,
    get_releases_as_markdown,
    RELEASE_TEMPLATE,
)

RELEASE_1 = '## Features\n Hello World (#2)'
RELEASE_2 = '## Features\n Hello World (#1)'

def mock_gh_api(func):

    @patch.object(get_releases, 'GhApi')
    @patch.object(get_releases, 'paged', autospec=True)
    @wraps(func)
    def mocked_call(self, paged, GhApi):
        release1_content = MagicMock()
        release1_content.body = RELEASE_1
        release1_content.name = '0.2.0'
        release1_content.html_url = 'https://www.google.com/releases/0.2.0'
        release1_content.published_at = datetime(2023, 12, 1, 13, 46).astimezone().isoformat()
        release1_content.processed = False

        release2_content = MagicMock()
        release2_content.body = RELEASE_2
        release2_content.name = '0.1.0'
        release2_content.html_url = 'https://www.google.com/releases/0.2.0'
        release2_content.published_at = datetime(2023, 11, 1, 13, 46).astimezone().isoformat()
        release2_content.processed = False

        def paged_mock(func, organisation_or_user, repository, *args, **kwargs):
            if organisation_or_user == 'abc' and repository == 'def':
                return [[release1_content, release2_content]]
            else:
                raise HTTP404NotFoundError(None, None, None)

        paged.side_effect = paged_mock
        GhApi().repos = MagicMock()
        GhApi().repos.list_releases = MagicMock()
        GhApi.reset_mock()
        return func(self, paged, GhApi, release1_content, release2_content)

    return mocked_call


class GetReleasesTestCase(unittest.TestCase):

    @mock_gh_api
    def test_get_releases_as_markdown_error(self, paged, GhApi, *args):
        with self.assertRaises(HTTP404NotFoundError):
            get_releases_as_markdown('x', 'y')
        GhApi.assert_called_once_with(token=None, gh_host=None)
        paged.assert_called_once_with(GhApi().repos.list_releases, 'x', 'y', per_page=100)

    @mock_gh_api
    def test_get_releases_as_markdown_ok(self, paged, GhApi, release1, release2):
        response = get_releases_as_markdown('abc', 'def')
        GhApi.assert_called_once_with(token=None, gh_host=None)
        paged.assert_called_once_with(GhApi().repos.list_releases, 'abc', 'def', per_page=100)
        self.assertIn('# [0.2.0]', response[0])
        self.assertIn('# Features\n Hello World ([#2](https://www.google.com/issues/2))', response[0])
        self.assertIn('*Released at 2023-12-01T13:46', response[0])
        self.assertIn('# [0.1.0]', response[1])
        self.assertIn('# Features\n Hello World ([#1](https://www.google.com/issues/1))', response[1])
        self.assertIn('*Released at 2023-11-01T13:46', response[1])
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0], _EnvironmentFactory().environment.from_string(RELEASE_TEMPLATE).render(release=release1))
        self.assertEqual(response[1], _EnvironmentFactory().environment.from_string(RELEASE_TEMPLATE).render(release=release2))

    @mock_gh_api
    def test_get_releases_as_markdown_custom_template(self, paged, GhApi, release1, release2):
        custom_template = 'Hi {{release.name}}\n{{release.body}}'
        response = get_releases_as_markdown('abc', 'def', release_template=custom_template)
        GhApi.assert_called_once_with(token=None, gh_host=None)
        paged.assert_called_once_with(GhApi().repos.list_releases, 'abc', 'def', per_page=100)
        self.assertIn('Hi 0.2.0\n', response[0])
        self.assertNotIn('# [0.2.0]', response[0])
        self.assertIn('# Features\n Hello World ([#2](https://www.google.com/issues/2))', response[0])
        self.assertNotIn('*Released at 2023-12-01T13:46', response[0])
        self.assertIn('Hi 0.1.0\n', response[1])
        self.assertNotIn('# [0.1.0]', response[1])
        self.assertIn('# Features\n Hello World ([#1](https://www.google.com/issues/1))', response[1])
        self.assertNotIn('*Released at 2023-11-01T13:46', response[1])
        self.assertEqual(len(response), 2)
        self.assertNotEqual(response[0], _EnvironmentFactory().environment.from_string(RELEASE_TEMPLATE).render(release=release1))
        self.assertNotEqual(response[1], _EnvironmentFactory().environment.from_string(RELEASE_TEMPLATE).render(release=release2))
        self.assertEqual(response[0], _EnvironmentFactory().environment.from_string(custom_template).render(release=release1))
        self.assertEqual(response[1], _EnvironmentFactory().environment.from_string(custom_template).render(release=release2))

    @mock_gh_api
    def test_get_releases_as_markdown_match(self, paged, GhApi, release1, release2):
        response = get_releases_as_markdown('abc', 'def', match='[0-9]+.1.[0-9]+')
        GhApi.assert_called_once_with(token=None, gh_host=None)
        paged.assert_called_once_with(GhApi().repos.list_releases, 'abc', 'def', per_page=100)
        self.assertNotIn('# [0.2.0]', response[0])
        self.assertNotIn('# Features\n Hello World ([#2](https://www.google.com/issues/2))', response[0])
        self.assertNotIn('*Released at 2023-12-01T13:46', response[0])
        self.assertIn('# [0.1.0]', response[0])
        self.assertIn('# Features\n Hello World ([#1](https://www.google.com/issues/1))', response[0])
        self.assertIn('*Released at 2023-11-01T13:46', response[0])
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0], _EnvironmentFactory().environment.from_string(RELEASE_TEMPLATE).render(release=release2))

    @mock_gh_api
    def test_get_releases_as_markdown_no_autoprocess(self, paged, GhApi, release1, release2):
        response = get_releases_as_markdown('abc', 'def', autoprocess=False)
        GhApi.assert_called_once_with(token=None, gh_host=None)
        paged.assert_called_once_with(GhApi().repos.list_releases, 'abc', 'def', per_page=100)
        self.assertIn('# [0.2.0]', response[0])
        self.assertIn('# Features\n Hello World (#2)', response[0])
        self.assertIn('*Released at 2023-12-01T13:46', response[0])
        self.assertIn('# [0.1.0]', response[1])
        self.assertIn('# Features\n Hello World (#1)', response[1])
        self.assertIn('*Released at 2023-11-01T13:46', response[1])
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0], _EnvironmentFactory().environment.from_string(RELEASE_TEMPLATE).render(release=release1))
        self.assertEqual(response[1], _EnvironmentFactory().environment.from_string(RELEASE_TEMPLATE).render(release=release2))



class AutprocessGithubLinksTestCase(unittest.TestCase):

    def test_issues(self):
        release = MagicMock()
        release.body = 'Fix #2, #3, (#4) #as'
        release.name = '0.2.0'
        release.html_url = 'https://www.google.com/releases/0.2.0'
        release.published_at = datetime(2023, 12, 1, 13, 46).astimezone().isoformat()
        release.processed = False
        self.assertFalse(release.processed)
        autoprocess_github_links(release)
        self.assertTrue(release.processed)
        self.assertEqual(release.body, 'Fix [#2](https://www.google.com/issues/2), [#3](https://www.google.com/issues/3), ([#4](https://www.google.com/issues/4)) #as')

    def test_usernames(self):
        release = MagicMock()
        release.body = 'Fix @xyz @abc13, (@#as)'
        release.name = '0.2.0'
        release.html_url = 'https://www.google.com/org/repo/releases/0.2.0'
        release.published_at = datetime(2023, 12, 1, 13, 46).astimezone().isoformat()
        release.processed = False
        self.assertFalse(release.processed)
        autoprocess_github_links(release)
        self.assertTrue(release.processed)
        self.assertEqual(release.body, 'Fix [@xyz](https://www.google.com/xyz) [@abc13](https://www.google.com/abc13), (@#as)')

    def test_both(self):
        release = MagicMock()
        release.body = 'Fix #12 @xyz @abc13, (@#as, #1)'
        release.name = '0.2.0'
        release.html_url = 'https://www.google.com/org/repo/releases/0.2.0'
        release.published_at = datetime(2023, 12, 1, 13, 46).astimezone().isoformat()
        release.processed = False
        self.assertFalse(release.processed)
        autoprocess_github_links(release)
        self.assertTrue(release.processed)
        self.assertEqual(release.body, 'Fix [#12](https://www.google.com/org/repo/issues/12) [@xyz](https://www.google.com/xyz) [@abc13](https://www.google.com/abc13), (@#as, [#1](https://www.google.com/org/repo/issues/1))')


class EnvironmentFactoryTestCase(unittest.TestCase):

    def test_init(self):
        factory = _EnvironmentFactory()
        self.assertIsNone(factory._environment)

    def test_add_extensions(self):
        # Use a magic mock to check add_extension called as expected

        with Env(override={'MKDOCS_GITHUB_CHANGELOG_JINJA_EXTENSIONS': json.dumps(["a", "b", "c"]) }):
            # We create a factory and check it here
            factory = _EnvironmentFactory()
            environment = MagicMock()
            factory.add_extensions(environment)
            environment.add_extension.assert_has_calls([call('a'), call('b'), call('c')], any_order=True)
            self.assertEqual(environment.add_extension.call_count, 3)

    def test_add_extensions_default(self):
        # Use a magic mock to check add_extension not called
        factory = _EnvironmentFactory()
        environment = MagicMock()
        factory.add_extensions(environment)
        environment.add_extension.assert_not_called()

    def test_get_environment(self):
        # Create Extensions for this
        environment1 = MagicMock()
        def test_extension1():
            return environment1

        environment2 = MagicMock()
        def test_extension_2():
            return environment2

        with TestExtension('test1', 'mkdocs_github_changelog.jinja_environment_factory', test_extension1):
            with TestExtension('test2', 'mkdocs_github_changelog.jinja_environment_factory', test_extension_2):
                factory = _EnvironmentFactory()
                with Env(override={'MKDOCS_GITHUB_CHANGELOG_JINJA_ENVIRONMENT_FACTORY': 'test1'}):
                    self.assertEqual(factory.get_environment(), environment1)
                    self.assertNotEqual(factory.get_environment(), environment2)

    def test_get_environment_default(self):
        # Create Extensions for this
        environment1 = MagicMock()
        def test_extension1():
            return environment1

        environment2 = MagicMock()
        def test_extension_2():
            return environment2

        with TestExtension('test1', 'mkdocs_github_changelog.jinja_environment_factory', test_extension1):
            with TestExtension('test2', 'mkdocs_github_changelog.jinja_environment_factory', test_extension_2):
                factory = _EnvironmentFactory()
                with Env(override={'MKDOCS_GITHUB_CHANGELOG_JINJA_ENVIRONMENT_FACTORY': 'default'}):
                    self.assertNotEqual(factory.get_environment(), environment1)
                    self.assertNotEqual(factory.get_environment(), environment2)
                    self.assertIsInstance(factory.get_environment(), Environment)

    def test_get_environment_none(self):
        # Create Extensions for this
        environment1 = MagicMock()
        def test_extension1():
            return environment1

        environment2 = MagicMock()
        def test_extension_2():
            return environment2

        with TestExtension('test1', 'mkdocs_github_changelog.jinja_environment_factory', test_extension1):
            with TestExtension('test2', 'mkdocs_github_changelog.jinja_environment_factory', test_extension_2):
                factory = _EnvironmentFactory()
                with Env(remove=['NSKIT_MIXER_ENVIRONMENT_FACTORY']):
                    self.assertNotEqual(factory.get_environment(), environment1)
                    self.assertNotEqual(factory.get_environment(), environment2)
                    self.assertIsInstance(factory.get_environment(), Environment)

    def test_environment_exists(self):
        factory = _EnvironmentFactory()
        self.assertIsNone(factory._environment)
        factory._environment = 'a'
        self.assertEqual(factory.environment, 'a')

    @patch.multiple(_EnvironmentFactory, get_environment=DEFAULT, add_extensions=DEFAULT)
    def test_environment_not_exists(self, get_environment, add_extensions):
        factory = _EnvironmentFactory()
        self.assertIsNone(factory._environment)
        get_environment.return_value =  'a'
        self.assertEqual(factory.environment, 'a')
        self.assertEqual(factory._environment, 'a')
        get_environment.assert_called_once_with()
        add_extensions.assert_called_once_with('a')

    def test_default_environment(self):
        # Check loader is correct
        environment = _EnvironmentFactory.default_environment()
        self.assertIsInstance(environment, Environment)
