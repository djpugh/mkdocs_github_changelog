"""mkdocs_github_changelog.

mkdocs extension to autogenerate changelog from github.
"""
import logging
from typing import Any, MutableMapping


def __get_version() -> str:
    """Get version information or return default if unable to do so."""
    # Default
    default_version = '0+unknown'
    version = default_version
    # Development installation only
    try:
        # Look here for setuptools scm to update the version - for development environments only
        from setuptools_scm import get_version  # type: ignore
        try:
            version = get_version(root='../../', version_scheme='no-guess-dev', relative_to=__file__)
        except LookupError:
            pass
    except ImportError:
        pass
    # Development installation without setuptools_scm or installed package
    # try loading from file
    if version == default_version:
        try:
            from mkdocs_github_changelog._version import __version__  # noqa: F401
        except ImportError:
            pass
    # Development installation without setuptools_scm
    if version == default_version:
        # Use the metadata
        import sys
        if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
            from importlib.metadata import PackageNotFoundError
            from importlib.metadata import version as parse_version
        else:
            from importlib_metadata import PackageNotFoundError  # type: ignore
            from importlib_metadata import version as parse_version  # type: ignore
        try:
            version = parse_version("mkdocs_github_changelog")
        except PackageNotFoundError:
            # package is not installed
            pass
    return version


__version__ = __get_version()


class _PluginLogger(logging.LoggerAdapter):
    """A logger adapter to prefix messages with the originating package name."""

    def __init__(self, prefix: str, logger: logging.Logger):
        """Initialize the object.

        Arguments:
            prefix: The string to insert in front of every message.
            logger: The logger instance.
        """
        super().__init__(logger, {})
        self.prefix = prefix

    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> tuple[str, Any]:
        """Process the message.

        Arguments:
            msg: The message:
            kwargs: Remaining arguments.

        Returns:
            The processed message.
        """
        return f"{self.prefix}: {msg}", kwargs


logger = _PluginLogger('mkdocs_github_changelog', logging.getLogger("mkdocs.plugins.mkdocs_github_changelog"))
