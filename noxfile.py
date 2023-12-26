import os
from pathlib import Path
from platform import platform, python_version
import sys

if sys.version_info.major <=3 and sys.version_info.minor < 11:
    import tomli as tomllib  # pyright: ignore [reportMissingImports]
else:
    import tomllib

import nox

ON_CI = any([os.environ.get('ON_CI', '0') == '1'])
STRICT_TYPES = False


def install_dependencies(session, required=True, optional=[], pyproject_toml='pyproject.toml'):
    with open(pyproject_toml, 'rb') as f:
        config = tomllib.load(f)
    dependencies = []
    if required:
        dependencies += config['project']['dependencies']
    for option in optional:
        dependencies += config['project']['optional-dependencies'].get(option, [])
    session.install(*dependencies)


@nox.session(name='pre-commit', python=None if ON_CI else False, reuse_venv=True, tags=['lint'])
def pre_commit(session):
    if ON_CI:
        session.install('pre-commit')
    session.run('pre-commit', 'run', '--all-files', env={'SKIP': 'lint,types,security'})


@nox.session(reuse_venv=True, tags=['lint'])
def lint(session):
    install_dependencies(session, required=False, optional=['dev','dev-lint'])
    session.run('flake8', 'src/')


@nox.session(reuse_venv=True, tags=['lint'])
def security(session):
    install_dependencies(session, required=False, optional=['dev', 'dev-security'])
    Path('reports').mkdir(exist_ok=True)
    session.run('pipenv', 'lock')
    session.run('pipenv', 'check')
    session.run('bandit', '-r', 'src')
    session.run('bandit', '-r', 'src', '--format', 'xml', '--output', 'reports/security-results.xml')


@nox.session(python=None if ON_CI else False, tags=['lint'])
def types(session):
    Path('reports').mkdir(exist_ok=True)
    if ON_CI:
        session.install('.[dev,dev-types]')
    args = ('mypy', 'src/', '--linecoverage-report', 'reports', '--junit-xml', 'reports/mypy.xml', '--cobertura-xml-report', 'reports')
    if (STRICT_TYPES and (not session.posargs or 'warn-only' not in session.posargs)) or (not STRICT_TYPES and session.posargs and 'strict' in session.posargs):
        # set default behaviour using the STRICT_TYPES variable, and then use either strict or warn-only in the command line args to turn off
        session.run(*args)
    else:
        try:
            session.run(*args)
        except nox.command.CommandFailed:
            session.warn('mypy failed, but warn-only set')


@nox.session(reuse_venv=True, tags=['test'])
def test(session):
    Path('reports').mkdir(exist_ok=True)
    if session.posargs:
        test_folder = [f'tests/{u}' for u in session.posargs]
    else:
        test_folder = ['tests']
    session.install('.[dev,dev-test]')
    for folder in test_folder:
        args = []
        args.append('-rs')
        args.append(folder)
        print(f'Test session: {folder}')
        env_name = f'py-{python_version()}-os-{platform()}'
        session.run(
            'pytest',
            # These args are for running pytest in parallel using pytest-xdist
            # '-n',
            # 'logical',
            '--log-level=WARNING',
            '--cov=mkdocs_github_changelog',
            '--cov-report',
            'xml:reports/coverage.xml',
            '--cov-report',
            'html:reports/htmlcov',
            '--junitxml',
            f'reports/{env_name}-test.xml',
            *args)


@nox.session(reuse_venv=True, tags=['docs'])
def docs(session):
    session.install('.[dev,dev-docs]')
    # We need to do some git wrangling for branches etc.
    # We are going to:
    #   * fetch all,
    #   * checkout gh-pages,
    #   * branch to gh-pages-dev-{HOSTNAME},
    #   * use that for the mike build and serve,
    #   * Delete the branch after serving complete
    docs_file = 'docs/mkdocs.yml'
    session.run('git', 'fetch', '--all', external=True)
    branch_name = f'gh-pages-dev-{os.uname().nodename}'
    version = 'dev'
    session.run('git', 'branch', '-D', branch_name, external=True, success_codes=[0, 1])
    session.run('git', 'branch', '--no-track', '-f', branch_name, 'origin/gh-pages', external=True)
    try:
        session.run('mike', 'deploy', '-u', version, 'latest', '--config-file', docs_file, '-b', branch_name)
        session.run('mike', 'set-default', 'latest', '--config-file', docs_file, '-b', branch_name)
        if not ON_CI:
            # We want to put the whole branch as an artifact so we output it here
            session.run('mike', 'serve', '--config-file', docs_file, '-b', branch_name)

    finally:
        if not ON_CI:
            # Delete the branch once complete when testing locally
            session.run('git', 'branch', '-D', branch_name, external=True)
        # You might want to output this to your CI/CD tool to e.g. capture the artifacts.
        # elif 'GITHUB_OUTPUT' in os.environ:
        #    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        #        print(f'branch_name={branch_name}', file=fh)


@nox.session(reuse_venv=True, tags=['build'])
def build(session):
    install_dependencies(session, required=False, optional=['dev','dev-build'])
    session.run('python', '-m', 'build')


@nox.session(reuse_venv=True, tags=['license'])
def licenses(session):
    session.install('licensecheck')
    session.run('licensecheck', '--using', 'PEP631:github;azure_devops;dev;dev-test;dev-lint;dev-types;dev-security;dev-docs;dev-build', '--format', 'json', '--file', 'licenses-dev.json')
    session.run('licensecheck', '--using', 'PEP631:github;azure_devops', '--format', 'json', '--file', 'licenses.json')
    session.run('licensecheck', '--using', 'PEP631:github;azure_devops', '--format', 'ansi')