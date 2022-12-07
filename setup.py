# Copyright (C) Matrisk GmbH 2022

from setuptools import setup, find_packages

# installation requirements
install_requires = [
    'pystra',
    'matplotlib',
    'ipywidgets<8'
]

setup(
    name = 'nrpmint',
    version = '0.2.0',
    author = 'Paul-Remo Wagner',
    author_email = 'wagner@matrisk.com',
    install_requires = install_requires,
    python_requires='>=3.8',
    packages = find_packages(exclude=['tests*'])
)
