[![CI](https://github.com/addisonElliott/pyqt5ac/workflows/CI/badge.svg)](https://github.com/addisonElliott/pyqt5ac/actions)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyqt5ac.svg)](https://pypi.org/project/pyqt5ac/)
[![PyPI](https://img.shields.io/pypi/v/pyqt5ac.svg)](https://pypi.org/project/pyqt5ac/)
[![PyPI - License](https://img.shields.io/pypi/l/pyqt5ac.svg)](https://github.com/addisonElliott/pyqt5ac/blob/master/LICENSE)

* [PyQt5 Auto Compiler (pyqt5ac)](#pyqt5-auto-compiler-pyqt5ac)
  * [Enter <strong>pyqt5ac</strong>!](#enter-pyqt5ac)
* [Installing](#installing)
* [Getting Started](#getting-started)
  * [Running from Command Line](#running-from-command-line)
  * [Running from Python Script](#running-from-python-script)
* [Configuration Options](#configuration-options)
* [Example](#example)
  * [Option 1: YAML Config File (Recommended)](#option-1-yaml-config-file-recommended)
  * [Option 2: JSON Config File (Deprecated)](#option-2-json-config-file-deprecated)
  * [Option 3: Python Script](#option-3-python-script)
  * [Option 4: Command Line](#option-4-command-line)
  * [Resulting File Structure](#resulting-file-structure)
* [Support](#support)
* [License](#license)

PyQt5 Auto Compiler (pyqt5ac)
=============================

pyqt5ac is a Python package for automatically compiling Qt's UI and QRC files into Python files.

In PyQt5, [Qt Designer](https://www.qt.io/) is the application used to create a GUI using a drag-and-drop interface. This interface is stored in a *.ui* file and any resources such as images or icons are stored in a *.qrc* file.

These two filetypes must be compiled into Python files before they can be used in your Python program. There are a few ways to go about this currently:
1. Manually compile the files using the command line and pyuic5 for *.ui* files and pyrcc5 for *.qrc* files.
2. Compile the files each time the application is started up by calling pyuic5 and pyrcc5 within your Python script

The downside to the first method is that it can be a tedious endeavor to compile the files, especially when one is faced with a larger project with many of these files that need to be compiled. Although the second method eliminates the tediousness of compilation, these files are compiled **every** time you run your script, regardless of if anything has been changed. This can cause a hit in performance and take longer to startup your script.

### Enter **pyqt5ac**!

pyqt5ac provides a command-line interface (CLI) that searches through your files and automatically compiles any *.ui* or *.qrc* files. In addition, pyqt5ac can be called from your Python script. In both instances, **ui and resource files are only compiled if they have been updated**.

Installing
==========

pyqt5ac is currently available on [PyPi](https://pypi.python.org/pypi/pyqt5ac/). The simplest way to
install alone is using ``pip`` at a command line

    pip install pyqt5ac

which installs the latest release.  To install the latest code from the repository (usually stable, but may have
undocumented changes or bugs)

    pip install git+https://github.com/addisonElliott/pyqt5ac.git

For developers, you can clone the pyqt5ac repository and run the ``setup.py`` file. Use the following commands to get
a copy from GitHub and install all dependencies

    git clone https://github.com/addisonElliott/pyqt5ac.git
    cd pyqt5ac
    pip install .[dev]

to install in 'develop' or 'editable' mode, where changes can be made to the local working code and Python will use
the updated code.

Getting Started
===============

Running from Command Line
-------------------------

If pyqt5ac is installed via pip, the command line interface can be called like any Unix based program in the terminal

    pyqt5ac [OPTIONS] [IOPATHS]...
    
In the interface, the options have slightly different names so reference the help file of the interface for more information. The largest difference is that the ioPaths argument is instead a list of space delineated paths where the even items are the source file expression and the odd items are the destination file expression.

The help file of the interface can be run as

    pyqt5ac --help

Running from Python Script
--------------------------

The following snippet of code below demonstrates how to call pyqt5ac from your Python script

```python
import pyqt5ac

pyqt5ac.main(rccOptions='', uicOptions='--from-imports', force=False, initPackage=True, config='',
             ioPaths=[['gui/*.ui', 'generated/%%FILENAME%%_ui.py'],
                     ['resources/*.qrc', 'generated/%%FILENAME%%_rc.py']])
```

Configuration Options
=====================

All of the options that can be specified to pyqt5ac can also be placed in a configuration file (JSON or YAML). My recommendation is to use a configuration file to allow easy compilation of your software. For testing purposes, I would use the options in the command line interface to make get everything working and then transcribe that into a configuration file for repeated use.

Whether running via the command line or from a script, the arguments and options that can be given are the same. The valid options are:
* **rccOptions** - Additional options to pass to the resource compiler. See the man page of pyrcc5 for more information on options. An example of a valid option would be "-compress 1". Default is to pass no options.
* **uicOptions** - Additional options to pass to the UI compiler. See the man page of pyuic5 for more information on options. An example of a valid option would be '--from-imports'. Default is to pass no options.
* **force** - Specifies whether to force compile all of the files found. The default is false meaning only outdated files will be compiled.
* **config** - JSON or YAML configuration file that contains information about these parameters.
* **ioPaths** - This is a 2D list containing information about what source files to compile and where to place the source files. The first column is the source file global expression (meaning you can use wildcards, ** for recursive folder search, ? for options, etc to match filenames) and the second column is the destination file expression. The destination file expression recognizes 'special' variables that will be replaced with information from the source filename:
    * %%FILENAME%% - Filename of the source file without the extension
    * %%EXT%% - Extension excluding the period of the file (e.g. ui or qrc)
    * %%DIRNAME%% - Directory of the source file
* **variables** - custom variables that can be used in the definition of the paths in **ioPaths**. For example, to limit the search of files to a specific directory, one can define a variable `BASEDIR` and then use it as `%%BASEDIR%%/gui/*.ui*`
* **init_package** - If specified, an empty `__init__.py` file is also generated in every output directory if missing. Does not overwrite existing `__init__.py`. Default value is `True`.

Note that all relative paths are resolved from the configuration file location, if given through a config file, or from the current working directory otherwise.

Example
=======

Take the following file structure as an example project where any UI and QRC files need to be compiled. Assume that pyuic5 and pyrcc5 are located in /usr/bin and that '--from-imports' is desired for the UIC compiler.

```
|-- gui
|   |-- mainWindow.ui
|   |-- addDataDialog.ui
|   `-- saveDataDialog.ui
|-- resources
|   |-- images
|   |-- stylesheets
|   |-- app.qrc
|   `-- style.qrc
|-- modules
|   |-- welcome
|   |   |-- module.ui
|   |   `-- resources
|   |       |-- images
|   |       `-- module.qrc
|   `-- dataProbe
|       |-- module.ui
|       `-- resources
|           |-- images
|           `-- module.qrc
```

The sections below demonstrate how to setup pyqt5ac to compile the necessary files given the file structure above.

Option 1: YAML Config File (Recommended)
---------------------------------------

```YAML
ioPaths:
  -
    - "gui/*.ui"
    - "generated/%%FILENAME%%_ui.py"
  -
    - "resources/*.qrc"
    - "generated/%%FILENAME_%%%%EXT%%.py"
  -
    - "modules/*/*.ui"
    - "%%DIRNAME%%/generated/%%FILENAME%%_ui.py"
  -
    - "modules/*/resources/*.qrc"
    - "%%DIRNAME%%/generated/%%FILENAME%%_rc.py"

uic_options: --from-imports
init_package: True
force: False
```

Now run pyqt5ac from the command line or Python script using your config file:
```bash
pyqt5ac --config config.yml
```

or
```python
import pyqt5ac

pyqt5ac.main(config='config.yml')
```

Option 2: JSON Config File (Deprecated)
---------------------------------------

```JSON
{
  "ioPaths": [
    ["gui/*.ui", "generated/%%FILENAME%%_ui.py"],
    ["resources/*.qrc", "generated/%%FILENAME%%_rc.py"],
    ["modules/*/*.ui", "%%DIRNAME%%/generated/%%FILENAME%%_ui.py"],
    ["modules/*/resources/*.qrc", "%%DIRNAME%%/generated/%%FILENAME%%_rc.py"]
  ],
  "rcc_options": "",
  "uic_options": "--from-imports",
  "init_package": true,
  "force": false
}
```

Now run pyqt5ac from the command line or Python script using your config file:
```bash
pyqt5ac --config config.yml
```

or
```python
import pyqt5ac

pyqt5ac.main(config='config.yml')
```

Option 3: Python Script
-----------------------

```python
import pyqt5ac

pyqt5ac.main(uicOptions='--from-imports', force=False, initPackage=True, ioPaths=[
        ['gui/*.ui', 'generated/%%FILENAME%%_ui.py'],
        ['resources/*.qrc', 'generated/%%FILENAME%%_rc.py'],
        ['modules/*/*.ui', '%%DIRNAME%%/generated/%%FILENAME%%_ui.py'],
        ['modules/*/resources/*.qrc', '%%DIRNAME%%/generated/%%FILENAME%%_rc.py']
    ])
```

Option 4: Command Line
----------------------

```bash
pyqt5ac --uic_options "--from-imports" gui/*.ui generated/%%FILENAME%%_ui.py resources/*.qrc generated/%%FILENAME%%_rc.py modules/*/*.ui %%DIRNAME%%/generated/%%FILENAME%%_ui.py modules/*/resources/*.qrc %%DIRNAME%%/generated/%%FILENAME%%_rc.py
```

Resulting File Structure
------------------------

```
|-- gui
|   |-- mainWindow.ui
|   |-- addDataDialog.ui
|   `-- saveDataDialog.ui
|-- resources
|   |-- images
|   |-- stylesheets
|   |-- app.qrc
|   `-- style.qrc
|-- generated
|   |-- __init__.py_
|   |-- mainWindow_ui.py
|   |-- addDataDialog_ui.py
|   |-- saveDataDialog_ui.py
|   |-- app_rc.py
|   `-- style_rc.py
|-- modules
|   |-- welcome
|   |   |-- module.ui
|   |   |-- resources
|   |   |   |-- images
|   |   |   `-- module.qrc
|   |   `-- generated
|   |       |-- module_ui.py
|   |       `-- module_rc.py
|   `-- dataProbe
|       |-- module.ui
|       |-- resources
|       |   |-- images
|       |   `-- module.qrc
|       `-- generated
|           |-- module_ui.py
|           `-- module_rc.py
```

Support
=======

Issues and pull requests are encouraged!

Bugs can be submitted through the [issue tracker](https://github.com/addisonElliott/pyqt5ac/issues).

Pull requests are welcome too!

License
=================

pyqt5ac has an [MIT-based license](https://github.com/addisonElliott/pyqt5ac/blob/master/LICENSE).
