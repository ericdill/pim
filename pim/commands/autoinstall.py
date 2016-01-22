import os
import getpass
import subprocess
import click
import time
from click import echo
from clint.textui import indent, puts, prompt, progress
from ..utils import write, retrieve, success, error, info, requirements, spinner
from .install import _install
import depfinder


@click.command('autoinstall', short_help='add to requirements', options_metavar='<options>')
@click.option('--globally', '-g', is_flag=True, help='autoinstall into your environment using pip.')
@click.option('--auto', '-a', is_flag=True, help='Automatically update your project requirements from your source code')
@click.option('--optional', '-o', is_flag=True, help='Add optional dependencies to requirements.txt')
def autoinstall(globally, auto, optional):
    """
    This should just wrap install
    """
    required = requirements.load()
    # find the package name
    def _find_package_name(setuppy_file):
        class NameFinder(ast.NodeVisitor):
            def visit_keyword(self, node):
                if node.arg == 'name':
                    self.name = node.value.s # stash the motor name and be done with it
                else:
                    self.generic_visit(node) # keep visiting nodes

        with open(setuppy_file, 'r') as f:
            code = f.read()
        tree = ast.parse(code)
        visitor = NameFinder()
        visitor.visit(tree)
        return visitor.name

    setuppy_path = _find_setuppy()
    package_name = _find_package_name(setuppy_path)
    path_to_source = os.path.join(os.path.split(setuppy_path)[0], package_name)
    deps = depfinder.simple_import_search(path_to_source)
    echo('Required Libraries')
    for dep in deps['required']:
        echo('  - %s' % dep)
    echo('')
    echo('Optional Libraries (Found inside function/class/try-except)')
    for dep in deps['optional']:
        echo('  - %s' % dep)

    requirements = set(deps['required'])
    if optional:
        echo('')
        echo('Adding all optional libraries to requirements.txt You might '
             'consider carefully reviewing these optional dependencies')
        requirements = requirements.union(set(deps['optional']))

    _install(requirements, globally)




def _find_setuppy(path='.', checked_folders=None):
    """
    Assume we are somewhere in the source tree for the project that the user
    is trying to autoupdate the deps.  Start looking recursively in `path` for
    setup.py.  If setup.py is not found, move up to the parent folder and
    recursively search in that directory. Repeat until setup.py is found

    Parameters
    ----------
    path : str
        The path, relative or absolute, to the directory where we should start
        looking for the setup.py files
    checked_folders : collection
        A collection of folders that have already been visited, so that we
        can skip folders that have already been checked

    Returns
    -------
    str
        path to setup.py file for this project.
    """
    path = os.path.abspath(path)
    if checked_folders is None:
        checked_folders = set()
    for folder, sibling_folders, files in os.walk(path):
        for file in files:
            if folder in checked_folders:
                continue
            if file == 'setup.py':
                return os.path.join(folder, file)
            else:
                checked_folders.add(os.path.join(folder, file))
    return find_setuppy(os.path.split(path)[0], checked_folders)