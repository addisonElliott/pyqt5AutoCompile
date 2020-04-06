import os
import re

from setuptools import setup

currentPath = os.path.abspath(os.path.dirname(__file__))


def find_version(filename):
    with open(filename, 'r') as fh:
        # Read first 2048 bytes, __version__ string will be within that
        data = fh.read(2048)

        match = re.search(r'^__version__ = [\'"]([\w\d.\-]*)[\'"]$', data, re.M)

        if match:
            return match.group(1)

    raise RuntimeError('Unable to find version string.')


# Get the long description from the README file
with open(os.path.join(currentPath, 'README.md'), 'r') as f:
    longDescription = f.read()

longDescription = '\n' + longDescription

REQUIREMENTS = {
    'core': [
        'PyQt5',
        'click',
        'pyyaml',
    ],
    'test': [
        'pytest',
        'pytest-cov',
    ],
    'dev': [
        # 'requirement-for-development-purposes-only',
    ],
    'doc': [
    ],
}


setup(name='pyqt5ac',
      version=find_version('pyqt5ac.py'),
      description='Python module to automatically compile UI and RC files in PyQt5 to Python files',
      long_description=longDescription,
      long_description_content_type='text/markdown',
      author='Addison Elliott',
      author_email='addison.elliott@gmail.com',
      url='https://github.com/addisonElliott/pyqt5ac',
      license='MIT License',
      install_requires=REQUIREMENTS['core'],
      extras_require={
        **REQUIREMENTS,
        # The 'dev' extra is the union of 'test' and 'doc', with an option
        # to have explicit development dependencies listed.
        'dev': [req
                for extra in ['dev', 'test', 'doc']
                for req in REQUIREMENTS.get(extra, [])],
        # The 'all' extra is the union of all requirements.
        'all': [req for reqs in REQUIREMENTS.values() for req in reqs],
      },
      python_requires='>=3',
      py_modules=['pyqt5ac'],
      entry_points={
          'console_scripts': ['pyqt5ac = pyqt5ac:cli']
      },
      keywords='pyqt pyqt5 qt qt5 qt auto compile generate ui rc pyuic5 pyrcc5 resource designer creator automatic',
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Topic :: Scientific/Engineering',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8'
      ],
      project_urls={
          'Source': 'https://github.com/addisonElliott/pyqt5ac',
          'Tracker': 'https://github.com/addisonElliott/pyqt5ac/issues',
      }
)
