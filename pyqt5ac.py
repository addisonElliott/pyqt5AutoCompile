import glob
import json
import os
import shlex
import sys
import tempfile
from io import StringIO

import PyQt5.pyrcc_main
import PyQt5.uic
import click
import yaml

__version__ = '1.0.2'


# @contextmanager
# def capture(source=sys.stdout, destination=os.devnull):
#     sourceFileNo = source.fileno()
#     destinationFileNo = destination.fileno()
#
#     oldSource = os.dup(sourceFileNo)
#     source.flush()
#     os.dup2(destinationFileNo, source.fileno())
#
#     try:
#         yield
#     finally:
#         os.dup2(oldSource, source.fileno())
#         pass

# with os.fdopen(os.dup(sourceFileNo), 'wb') as copied:
#     source.flush()
#
#     try:
#         os.dup2(destinationFileNo, source.fileno())
#     except ValueError:
#         with open(destination, 'wb') as fh:
#             os.dup2(fh.fileno(), sourceFileNo)
#
#     try:
#         yield
#     finally:
#         source.flush()
#         destination.flush()
#         print('sss')
#         os.dup2(copied.fileno(), source.fileno())
#         pass

# stdout_fd = fileno(stdout)
# # copy stdout_fd before it is overwritten
# #NOTE: `copied` is inheritable on Windows when duplicating a standard stream
# with os.fdopen(os.dup(stdout_fd), 'wb') as copied:
#     stdout.flush()  # flush library buffers that dup2 knows nothing about
#     try:
#         os.dup2(fileno(to), stdout_fd)  # $ exec >&to
#     except ValueError:  # filename
#         with open(to, 'wb') as to_file:
#             os.dup2(to_file.fileno(), stdout_fd)  # $ exec > to
#     try:
#         yield stdout # allow code to be run with the redirected stdout
#     finally:
#         # restore stdout to its previous value
#         #NOTE: dup2 makes stdout_fd inheritable unconditionally
#         stdout.flush()
#         os.dup2(copied.fileno(), stdout_fd)  # $ exec >&copied


# Takes command, options, source and destination folders and creates a command from it
# Escapes the src/dst and removes any additional whitespace
def _buildCommand(command, options, sourceFilename, destFilename):
    """Build PyQt5 command line string based on the command, options and arguments

    String follows the syntax:
        <command> <options> -o destFilename sourceFilename
    """

    # Construct command string
    commandString = '%s %s -o %s %s' % (
        shlex.quote(command), options, shlex.quote(destFilename), shlex.quote(sourceFilename))

    # Split command string by spaces
    args = shlex.split(commandString)

    # Remove any blank arguments meaning there were double spaces in the command string and then rejoin the args
    return ' '.join([arg for arg in args if arg])


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
@click.argument('iopaths', nargs=-1, required=False)
@click.version_option(__version__)
def cli(rccOptions, uicOptions, force, config, iopaths=()):
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

    main(rccOptions, uicOptions, force, config, ioPaths)


def main(rccOptions='', uicOptions='', force=False, config='', ioPaths=()):
    if config:
        with open(config, 'r') as fh:
            if config.endswith('.yml'):
                # Load YAML file
                configData = yaml.load(fh)
            else:
                # Assume JSON file
                configData = json.load(fh)

            # configData variable is a dictionary where the keys are the names of the configuration
            # Load the keys and use the default value if nothing is specified
            rccOptions = configData.get('rcc_options', rccOptions)
            uicOptions = configData.get('uic_options', uicOptions)
            force = configData.get('force', force)
            ioPaths = configData.get('ioPaths', ioPaths)

    # Loop through the list of io paths
    for sourceFileExpr, destFileExpr in ioPaths:
        foundItem = False

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
            destFilename = destFileExpr.replace('%%FILENAME%%', filename) \
                .replace('%%EXT%%', ext[1:]) \
                .replace('%%DIRNAME%%', dirname)

            # Retrieve the absolute path to the source and destination filename
            sourceFilename, destFilename = os.path.abspath(sourceFilename), os.path.abspath(destFilename)

            if ext == '.ui':
                isQRCFile = False
                options = uicOptions
            elif ext == '.qrc':
                isQRCFile = True
                options = rccOptions
            else:
                click.secho('Unknown target %s found' % sourceFilename, fg='yellow')
                continue

            # Create all directories to the destination filename and do nothing if they already exist
            os.makedirs(os.path.dirname(destFilename), exist_ok=True)

            # If we are force compiling everything or the source file is outdated, then compile, otherwise skip!
            if force or _isOutdated(sourceFilename, destFilename, isQRCFile):
                if isQRCFile:
                    # old_stderr = sys.stderr
                    # sys.stderr = mystdout = StringIO()

                    # TODO Pull from stderr the value and do stuff
                    # with tempfile.TemporaryFile() as fp:
                    # with open('C:/Users/adellio/Desktop/test.txt', 'w') as fp:
                        # with capture(sys.stderr, fp):
                        fp = open('C:/Users/adellio/Desktop/test.txt', 'w')

                        sys.stderr.write('testingdddd11\n')
                        print('xxx', sys.stderr.fileno())

                        old_stderr = os.dup(sys.stderr.fileno())

                        print(old_stderr)

                        # sys.stderr.flush()

                        print(fp.fileno())

                        print(os.dup2(fp.fileno(), sys.stderr.fileno()))
                        prev = sys.stderr
                        sys.stderr = os.fdopen(fp.fileno(), 'w')

                        print(fp.fileno(), sys.stderr.fileno(), old_stderr)

                        # result = PyQt5.pyrcc_main.processResourceFile([sourceFilename], destFilename, False)
                        sys.stderr.write('test\n')
                        fp.write('dkdkdk')

                        # fp.flush()
                        # fp.close()
                        # sys.stderr.flush()
                        # os.dup2(sys.stderr.fileno(), old_stderr)
                        print(os.dup2(old_stderr, sys.stderr.fileno()))
                        sys.stderr = prev
                        os.close(old_stderr)

                        print(sys.stderr.fileno(), old_stderr)

                        # raise ValueError('testing')
                        print('ok')
                        sys.stderr.write('testingdddd\n')
                        print('ok2')

                # print(result)

                    # sys.stderr = old_stderr
                    # print('Value extracted: ', mystdout.getvalue())

                    # # examine mystdout.getvalue()

                    # TODO Setup globals already
                else:
                    # TODO Pass options here
                    # TODO Handle errors here
                    with open(destFilename, 'w') as fh:
                        PyQt5.uic.compileUi(sourceFilename, fh)

                    # TODO Do try/catch for this because it will throw errors for issues

                #     if e.output:
                #         click.secho(commandString, fg='yellow')
                #         click.secho(e.output.decode(sys.stdout.encoding), fg='red')
                #     else:
                #         click.secho(commandString, fg='red')
                # except OSError as e:
                #     click.secho(commandString, fg='yellow')
                #     click.secho(str(e), fg='red')
                # else:
                #     click.secho(commandString, fg='green')
            else:
                click.secho('Skipping %s, up to date' % filename)

        if not foundItem:
            click.secho('No items found in %s' % sourceFileExpr)


if __name__ == '__main__':
    cli()
