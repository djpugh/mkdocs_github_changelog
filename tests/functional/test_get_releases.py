from datetime import date
from functools import wraps
from pathlib import Path
import unittest

from fastcore.net import HTTP403ForbiddenError

from mkdocs_github_changelog.get_releases import get_releases_as_markdown


class GetReleasesFunctionalTestCase(unittest.TestCase):

    @staticmethod
    def skip_if_rate_limited():
        raise unittest.SkipTest('Rate Limited')

    def test_get_releases_as_markdown(self):
        try:
            releases = get_releases_as_markdown('djpugh', 'fastapi_aad_auth')
        except HTTP403ForbiddenError:
            self.skip_if_rate_limited()
        self.assertGreater(len(releases), 23)
        self.assertIn('Adding AADSTS90009 info', '\n\n'.join(releases))
        self.assertIn('Adding AADSTS90009 info', releases[-23])
        self.assertIn('# [0.1.21](https://github.com/djpugh/fastapi_aad_auth/releases/tag/0.1.21)', releases[-23])
