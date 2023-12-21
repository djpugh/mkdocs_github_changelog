import unittest
from unittest.mock import patch

from markdown import Markdown
from markdown.blockparser import BlockParser
from nskit.common.contextmanagers import Env

from mkdocs_github_changelog import extension

from mkdocs_github_changelog.extension import GithubReleaseChangelogProcessor


class ProccesorTestCase(unittest.TestCase):

    def test_regexp_matching(self):

        test_map = {
            '::github-release-changelog abc/def':  {'heading': '', 'org': 'abc', 'repo': 'def'},
            '## ::github-release-changelog abc-0123/def.xyz': {'heading': '## ', 'org': 'abc-0123', 'repo': 'def.xyz'},
            '### ::github-release-changelog abc-0123/def.xyz_123': {'heading': '### ', 'org': 'abc-0123', 'repo': 'def.xyz_123'}
        }
        for test_string, expected in test_map.items():
            with self.subTest(test=test_string):
                result = GithubReleaseChangelogProcessor.regex.match(test_string).groupdict()
                self.assertEqual(result, expected)

    def test_regexp_non_matching(self):

        test_strings = [
            '::github-release-changelog',
            '::github-release-changelog abc*21/@12'
            '::: github-release-changelog',
            '::github-release-changelog abcder'
        ]
        for test_string in test_strings:
            with self.subTest(test=test_string):
                result = GithubReleaseChangelogProcessor.regex.match(test_string)
                self.assertIsNone(result)

    # Patch get_releases_as_markdown to return the release info
    @patch.object(extension, 'get_releases_as_markdown')
    def test_process_block_simple(self, get_releases_as_markdown):
        releases = '# 0.1.0\n\n## Features\n Hello World ([#1](https://www.google.com))'
        get_releases_as_markdown.return_value = [releases]
        processor = GithubReleaseChangelogProcessor(BlockParser(Markdown()), {})
        result = processor._process_block('abc', 'def', '')
        self.assertEqual(result, releases)
        get_releases_as_markdown.assert_called_once_with(
            organisation_or_user='abc',
            repository='def',
            token=None,
            release_template=None,
            github_api_url=None,
            match=None,
            autoprocess=True
        )

    # Patch get_releases_as_markdown to return the release info
    @patch.object(extension, 'get_releases_as_markdown')
    def test_process_block_with_global_config(self, get_releases_as_markdown):
        releases = '# 0.1.0\n\n## Features\n Hello World ([#1](https://www.google.com))'
        get_releases_as_markdown.return_value = [releases]
        processor = GithubReleaseChangelogProcessor(BlockParser(Markdown()), {'release_template': 'xyz', 'github_api_url': None, 'token': '789', 'match':'*.*.*', 'autoprocess': False})
        result = processor._process_block('abc', 'def', '')
        self.assertEqual(result, releases)
        get_releases_as_markdown.assert_called_once_with(
            organisation_or_user='abc',
            repository='def',
            token='789',
            release_template='xyz',
            github_api_url=None,
            match='*.*.*',
            autoprocess=False
        )

    # Patch get_releases_as_markdown to return the release info
    @patch.object(extension, 'get_releases_as_markdown')
    def test_process_block_with_local_config(self, get_releases_as_markdown):
        releases = '# 0.1.0\n\n## Features\n Hello World ([#1](https://www.google.com))'
        get_releases_as_markdown.return_value = [releases]
        processor = GithubReleaseChangelogProcessor(BlockParser(Markdown()), {'release_template': 'xyz', 'github_api_url': None, 'token': '789'})
        result = processor._process_block('abc', 'def', 'token: 567\nrelease_template: ghi\ngithub_api_url: https://microsoft.com\nbase_indent: 3\nmatch: a.b.c\nautoprocess: false')
        get_releases_as_markdown.assert_called_once_with(
            organisation_or_user='abc',
            repository='def',
            token=567,
            release_template='ghi',
            github_api_url='https://microsoft.com',
            match='a.b.c',
            autoprocess=False
        )
        self.assertEqual(result, '#### 0.1.0\n\n##### Features\n Hello World ([#1](https://www.google.com))')


    @patch.object(extension, 'get_releases_as_markdown')
    def test_process_block_with_env(self, get_releases_as_markdown):
        with Env(override={'GITHUB_TOKEN': 'abcdef'}):
            releases = '# 0.1.0\n\n## Features\n Hello World ([#1](https://www.google.com))'
            get_releases_as_markdown.return_value = [releases]
            processor = GithubReleaseChangelogProcessor(BlockParser(Markdown()), {'release_template': 'xyz', 'github_api_url': None, 'token': '789'})
            result = processor._process_block('abc', 'def', 'token: !ENV GITHUB_TOKEN\nrelease_template: ghi\ngithub_api_url: https://microsoft.com\nbase_indent: 3\nmatch: a.b.c')
            get_releases_as_markdown.assert_called_once_with(
                organisation_or_user='abc',
                repository='def',
                token='abcdef',
                release_template='ghi',
                github_api_url='https://microsoft.com',
                match='a.b.c',
                autoprocess=True
            )
            self.assertEqual(result, '#### 0.1.0\n\n##### Features\n Hello World ([#1](https://www.google.com))')


    # Patch get_releases_as_markdown to return the release info
    @patch.object(extension, 'get_releases_as_markdown')
    def test_process_block_with_heading_level(self, get_releases_as_markdown):
        releases = '# 0.1.0\n\n## Features\n Hello World ([#1](https://www.google.com))'
        get_releases_as_markdown.return_value = [releases]
        processor = GithubReleaseChangelogProcessor(BlockParser(Markdown()), {})
        result = processor._process_block('abc', 'def', '', 3)
        get_releases_as_markdown.assert_called_once_with(
            organisation_or_user='abc',
            repository='def',
            token=None,
            release_template=None,
            github_api_url=None,
            match=None,
            autoprocess=True
        )
        self.assertEqual(result, '#### 0.1.0\n\n##### Features\n Hello World ([#1](https://www.google.com))')

    def test_test_matching(self):
        test_strings = [
            '::github-release-changelog abc/def\n    github_api_url: 123',
            '## ::github-release-changelog abc-0123/def.xyz',
            '### ::github-release-changelog abc-0123/def.xyz_123',
        ]
        processor = GithubReleaseChangelogProcessor(BlockParser(Markdown()), {})
        for test_string in test_strings:
            with self.subTest(test_string=test_string):
                self.assertTrue(processor.test(None, test_string))

    def test_test_not_matching(self):
        test_strings = [
            '::github-release-changelog',
            '::github-release-changelog abc*21/@12'
            '::: github-release-changelog',
            '::github-release-changelog abcder'
            ':: github-release-changelog abc/def\n    github_api_url: 123',
        ]
        processor = GithubReleaseChangelogProcessor(BlockParser(Markdown()), {})
        for test_string in test_strings:
            with self.subTest(test_string=test_string):
                self.assertFalse(processor.test(None, test_string))

    @patch.object(extension, 'get_releases_as_markdown')
    def test_run_matching_block(self, get_releases_as_markdown):
        releases = '# 0.1.0\n\n## Features\n Hello World ([#1](https://www.google.com))'
        get_releases_as_markdown.return_value = [releases]
        blocks = ['::github-release-changelog abc/def', 'b']
        processor = GithubReleaseChangelogProcessor(BlockParser(Markdown()), {})
        processor.run(None, blocks)
        self.assertEqual(blocks, [releases, 'b'])

    def test_run_no_matching_block(self):
        blocks = ['a', 'b']
        processor = GithubReleaseChangelogProcessor(BlockParser(Markdown()), {})
        processor.run(None, blocks)
        self.assertEqual(blocks, ['a', 'b'])

