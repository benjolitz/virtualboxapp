#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import (setup, find_packages)
# Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path


here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='virtualboxapp',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    version='0.0.2',

    description='Tool for setup/run/teardown of \
seamless-mode single applications',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/benjolitz/virtualboxapp',

    # Author details
    author='Ben Jolitz',
    author_email='ben.jolitz+virtualboxapp@gmail.com',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Databases',

        # Pick your license as you wish (should match 'license' above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

    # What does your project relate to?
    keywords='virtualbox seamless vm run',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),

    install_requires=['vbox==9.9.9', 'six'],
    dependency_links=[
        'git+https://github.com/benjolitz/vbox.git#egg=vbox-9.9.9',
    ],

    # To provide executable scripts, use entry points in preference to the
    # 'scripts' keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'runvboxapp=virtualboxapp:main'
        ],
    },
)
