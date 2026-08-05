import unittest

from mkdocs.config.base import ValidationError
from mkdocs.config.defaults import MkDocsConfig
from nskit.common.contextmanagers import ChDir, Env

from mkdocs_github_changelog.plugin import (
    GithubReleaseChangelogExtension,
    MkdocsGithubChangelogPlugin,
)


class MkdocsGithubChangelogPluginTestCase(unittest.TestCase):

    def test_config_defaults(self):
        plugin = MkdocsGithubChangelogPlugin()
        resp = plugin.load_config({})
        self.assertEqual(plugin.config, {'token': None, 'github_api_url': None, 'release_template': None, 'autoprocess': True, 'include_prereleases': False, 'enabled': True, 'match': None})
        self.assertEqual(resp, ([], []))

    def test_config_overriden_ok(self):
        plugin = MkdocsGithubChangelogPlugin()
        resp = plugin.load_config({'token': 'abc', 'github_api_url': 'https://api.github.com', 'release_template': '123', 'autoprocess': False, 'include_prereleases': False, 'match': 'a.b.c', 'enabled': False})
        self.assertEqual(plugin.config, {'token': 'abc', 'github_api_url': 'https://api.github.com', 'release_template': '123', 'autoprocess': False, 'include_prereleases': False, 'match': 'a.b.c', 'enabled': False})
        self.assertEqual(resp, ([], []))

    def test_config_overriden_bad(self):
        # mkdocs.config.base.Config._validate breaks out of its loop on the
        # first ValidationError, so only the first failing option in schema
        # order is ever reported, however many are invalid.
        plugin = MkdocsGithubChangelogPlugin()
        resp = plugin.load_config({'token': ['x', 'y'], 'github_api_url': 'the quick brown fox', 'release_template': ['a', 'b'], 'autoprocess': 'a', 'match': ['x', 'y'], 'enabled': 'x'})
        self.assertEqual(len(resp[0]), 1)
        self.assertEqual(resp[0][0][0], 'token')
        self.assertIsInstance(resp[0][0][1], ValidationError)

    def test_config_each_option_validated(self):
        # Because validation is fail-fast, each option has to be exercised on
        # its own to show it is actually validated and not merely unreached.
        for key, value in (
            ('token', ['x', 'y']),
            ('github_api_url', 'the quick brown fox'),
            ('release_template', ['a', 'b']),
            ('match', ['x', 'y']),
            ('autoprocess', 'a'),
            ('include_prereleases', 'a'),
            ('enabled', 'x'),
        ):
            with self.subTest(key=key):
                resp = MkdocsGithubChangelogPlugin().load_config({key: value})
                self.assertEqual([k for k, _ in resp[0]], [key])
                self.assertIsInstance(resp[0][0][1], ValidationError)

    def test_on_config(self):
        plugin = MkdocsGithubChangelogPlugin()
        config = MkDocsConfig()
        plugin.load_config({})
        plugin.on_config(config)
        self.assertIsInstance(config.markdown_extensions[-1], GithubReleaseChangelogExtension)
        ext = config.markdown_extensions[-1]
        self.assertEqual(ext._config, {'token': None, 'github_api_url': None, 'release_template': None, 'autoprocess': True, 'include_prereleases': False, 'match': None, 'enabled': True})

    def test_on_config_from_env(self):
        with Env(override={'GITHUB_TEST_TOKEN': 'abc'}):
            with ChDir():
                plugin = MkdocsGithubChangelogPlugin()
                config = MkDocsConfig()
                # Load the env var
                config_file = 'mkdocs.yml'
                with open(config_file, 'w') as f:
                    f.write('plugins:\n- mkdocs_github_changelog:\n    token: !ENV GITHUB_TEST_TOKEN')
                with open(config_file) as f:
                    config.load_file(f)
                plugin.load_config(config.plugins[0]['mkdocs_github_changelog'])
                plugin.on_config(config)
                self.assertIsInstance(config.markdown_extensions[-1], GithubReleaseChangelogExtension)
                ext = config.markdown_extensions[-1]
                self.assertEqual(ext._config, {'token': 'abc', 'github_api_url': None, 'release_template': None, 'autoprocess': True, 'include_prereleases': False, 'match': None, 'enabled': True})
