import glob
import json
import os
import shlex
import subprocess
import sys

import click
import yaml

__version__ = '1.2.1'


# Takes information about command and creates an argument list from it
# In addition to an argument list, a 'cleaner' string is returned to be shown to the user
# This essentially replaces 'python -m XXX' with the command parameter
def _buildCommand(module, command, options, sourceFilename, destFilename):
    # Split options string into a list of options that is space-delineated
    # shlex.split is used rather than str.split to follow common shell rules such as strings in quotes are considered
    # one argument, even with spaces
    optionsList = shlex.split(options)

    # List of arguments with the first argument being the command to run
    # This is the argument list that will be actually ran by using sys.executable to get the current Python executable
    # running this program.
    argList = [sys.executable, '-m', module] + optionsList + ['-o', destFilename, sourceFilename]

    # However, for showing the user what command was ran, we will replace the 'python -m XXX' with pyuic5 or pyrcc5 to
    # make it look cleaner
    # Create one command string by escaping each argument and joining together with spaces
    cleanArgList = [command] + argList[3:]
    commandString = ' '.join([shlex.quote(arg) for arg in cleanArgList])

    return argList, commandString


def _isOutdated(src, dst, isQRCFile):
    outdated = (not os.path.exists(dst) or
                (os.path.getmtime(src) > os.path.getmtime(dst)))

    if not outdated and isQRCFile:
        # For qrc files, we need to check each individual resources.
        # If one of them is newer than the dst file, the qrc file must be considered as outdated.
        # File paths are relative to the qrc file path
        qrcParentDir = os.path.dirname(src)

        with open(src, 'r') as f:
            lines = f.readlines()
            lines = [line for line in lines if '<file>' in line]

        cwd = os.getcwd()
        os.chdir(qrcParentDir)

        for line in lines:
            filename = line.replace('<file>', '').replace('</file>', '').strip()
            filename = os.path.abspath(filename)

            if os.path.getmtime(filename) > os.path.getmtime(dst):
                outdated = True
                break

        os.chdir(cwd)

    return outdated


@click.command(name='pyqt5ac')
@click.option('--rcc_options', 'rccOptions', default='',
              help='Additional options to pass to resource compiler [default: none]')
@click.option('--uic_options', 'uicOptions', default='',
              help='Additional options to pass to UI compiler [default: none]')
@click.option('--config', '-c', default='', type=click.Path(exists=True, file_okay=True, dir_okay=False),
              help='JSON or YAML file containing the configuration parameters')
@click.option('--force', default=False, is_flag=True, help='Compile all files regardless of last modification time')
@click.option('--init-package', 'initPackage', default=True, is_flag=True,
              help='Ensures that the folder containing the generated files is a Python subpackage '
                   '(i.e. it contains a file called __init__.py')
@click.argument('iopaths', nargs=-1, required=False)
@click.version_option(__version__)
def cli(rccOptions, uicOptions, force, config, iopaths=(), initPackage=True):
    """Compile PyQt5 UI/QRC files into Python

    IOPATHS argument is a space delineated pair of glob expressions that specify the source files to compile as the
    first item in the pair and the path of the output compiled file for the second item. Multiple pairs of source and
    destination paths are allowed in IOPATHS.

    \b
    The destination path argument supports variables that are replaced based on the
    target source file:
        * %%FILENAME%% - Filename of the source file without the extension
        * %%EXT%% - Extension excluding the period of the file (e.g. ui or qrc)
        * %%DIRNAME%% - Directory of the source file

    Files that match a given source path expression are compiled if and only if the file has been modified since the
    last compilation unless the FORCE flag is set. If the destination file does not exist, then the file is compiled.

    A JSON or YAML configuration file path can be specified using the config option. See the GitHub page for example
    config files.

    \b
    Example:
    gui
    --->example.ui
    resources
    --->test.qrc

    \b
    Command:
    pyqt5ac gui/*.ui generated/%%FILENAME%%_ui.py resources/*.qrc generated/%%FILENAME%%_rc.py

    \b
    Results in:
    generated
    --->example_ui.py
    --->test_rc.py

    Author: Addison Elliott
    """

    # iopaths is a 1D list containing pairs of the source and destination file expressions
    # So the list goes something like this:
    # [sourceFileExpr1, destFileExpr1, sourceFileExpr2, destFileExpr2, sourceFileExpr3, destFileExpr3]
    #
    # When calling the main function, it requires that ioPaths be a 2D list with 1st column source file expression and
    # second column the destination file expression.
    ioPaths = list(zip(iopaths[::2], iopaths[1::2]))

    main(rccOptions=rccOptions, uicOptions=uicOptions, force=force, config=config, ioPaths=ioPaths,
         initPackage=initPackage)


def replaceVariables(variables_definition, string_with_variables):
    """
    Performs variable replacements into the given string
    :param variables_definition: mapping variable_name - variable value. Matching names encased into %% will be replaces
    by their respective value found in the mapping (case-sensitive)
    :param string_with_variables: String where to replace the variable names (enclosed into %%'s) with their respective
    values found in the variables_definition
    :return: the input string with its variables replaced.
    """
    for variable_name, variable_value in variables_definition.items():
        string_with_variables = string_with_variables.replace("%%{}%%".format(variable_name), variable_value)
    return string_with_variables


def main(rccOptions='', uicOptions='', force=False, config='', ioPaths=(), variables=None, initPackage=True):
    if config:
        with open(config, 'r') as fh:
            if config.endswith('.yml'):
                # Load YAML file
                configData = yaml.load(fh, Loader=yaml.FullLoader)
            else:
                click.secho('JSON usage is deprecated and will be removed in 2.0.0. Use YML configuration instead',
                            fg='yellow')
                # Assume JSON file
                configData = json.load(fh)

            # configData variable is a dictionary where the keys are the names of the configuration
            # Load the keys and use the default value if nothing is specified
            rccOptions = configData.get('rcc_options', rccOptions)
            uicOptions = configData.get('uic_options', uicOptions)
            force = configData.get('force', force)
            ioPaths = configData.get('ioPaths', ioPaths)
            variables = configData.get('variables', variables)
            initPackage = configData.get('init_package', initPackage)

    # Validate the custom variables
    if variables is None:
        variables = {}
    if 'FILENAME' in variables.keys() or 'EXT' in variables.keys() or 'DIRNAME' in variables.keys():
        raise ValueError("Custom variables cannot be called FILENAME, EXT or DIRNAME.")

    # Loop through the list of io paths
    for sourceFileExpr, destFileExpr in ioPaths:
        foundItem = False

        # Replace instances of the variables with the actual values of the available variables
        sourceFileExpr = replaceVariables(variables, sourceFileExpr)

        # Find files that match the source filename expression given
        for sourceFilename in glob.glob(sourceFileExpr, recursive=True):
            # If the filename does not exist, not sure why this would ever occur, but show a warning
            if not os.path.exists(sourceFilename):
                click.secho('Skipping target %s, file not found' % sourceFilename, fg='yellow')
                continue

            foundItem = True

            # Split the source filename into directory and basename
            # Then split the basename into filename and extension
            #
            # Ex: C:/Users/addis/Documents/PythonProjects/PATS/gui/mainWindow.ui
            #   dirname = C:/Users/addis/Documents/PythonProjects/PATS/gui
            #   basename = mainWindow.ui
            #   filename = mainWindow
            #   ext = .ui
            dirname, basename = os.path.split(sourceFilename)
            filename, ext = os.path.splitext(basename)

            # Replace instances of the variables with the actual values from the source filename
            variables.update({'FILENAME': filename, 'EXT': ext[1:], 'DIRNAME': dirname})
            destFilename = replaceVariables(variables, destFileExpr)

            # Retrieve the absolute path to the source and destination filename
            sourceFilename, destFilename = os.path.abspath(sourceFilename), os.path.abspath(destFilename)

            if ext == '.ui':
                isQRCFile = False
                module = 'PyQt5.uic.pyuic'
                command = 'pyuic5'
                options = uicOptions
            elif ext == '.qrc':
                isQRCFile = True
                module = 'PyQt5.pyrcc_main'
                command = 'pyrcc5'
                options = rccOptions
            else:
                click.secho('Unknown target %s found' % sourceFilename, fg='yellow')
                continue

            # Create all directories to the destination filename and do nothing if they already exist
            dest_file_directory = os.path.dirname(destFilename)
            os.makedirs(dest_file_directory, exist_ok=True)

            # Ensure __init__.py is present and, if it's missing, generate it
            if initPackage:
                with open(os.path.join(dest_file_directory, "__init__.py"), 'a'):
                    pass

            # If we are force compiling everything or the source file is outdated, then compile, otherwise skip!
            if force or _isOutdated(sourceFilename, destFilename, isQRCFile):
                argList, commandString = _buildCommand(module, command, options, sourceFilename, destFilename)

                commandResult = subprocess.run(argList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                if commandResult.returncode == 0:
                    click.secho(commandString, fg='green')
                else:
                    if commandResult.stderr:
                        click.secho(commandString, fg='yellow')
                        click.secho(commandResult.stderr.decode(), fg='red')
                    else:
                        click.secho(commandString, fg='yellow')
                        click.secho('Command returned with non-zero exit status %i' % commandResult.returncode,
                                    fg='red')
            else:
                click.secho('Skipping %s, up to date' % filename)

        if not foundItem:
            click.secho('No items found in %s' % sourceFileExpr)


if __name__ == '__main__':
    cli()
