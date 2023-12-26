import unittest

from markdown import Markdown

from mkdocs_github_changelog.extension import (
    GithubReleaseChangelogExtension,
    GithubReleaseChangelogProcessor,
)


class GithubReleaseChangelogExtensionTestCase(unittest.TestCase):

    def test_init(self):
        ext = GithubReleaseChangelogExtension({'a': 1})
        self.assertEqual(ext._config, {'a': 1})

    def test_extendMarkdown(self):
        md = Markdown()
        ext = GithubReleaseChangelogExtension({'a': 1})
        ext.extendMarkdown(md)
        self.assertTrue(any([isinstance(proc, GithubReleaseChangelogProcessor) for proc in md.parser.blockprocessors]))
