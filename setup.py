#!/usr/bin/env python3
"""
Setup for Zenv Transpiler
"""

from setuptools import setup, find_packages
import os

# Informations de base
NAME = "zenv-transpiler"
VERSION = "1.2.0"
AUTHOR = "Mauricio"
EMAIL = "ceoseshell@gmail.com"
DESCRIPTION = "A .zv/.zenv to Python transpiler"
URL = "https://github.com/gopu-inc/zenv"
DISCORD = "https://discord.gg/qWx5DszrC"

# Lire le README pour la description longue
def read_readme():
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return DESCRIPTION

setup(
    # Informations de base
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    description=DESCRIPTION,
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    
    # URLs
    url=URL,
    project_urls={
        "Source Code": URL,
        "Discord": DISCORD,
        "Bug Tracker": f"{URL}/issues",
    },
    
    # Packages
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    include_package_data=True,
    
    # Dépendances
    python_requires=">=3.6",
    install_requires=[
        "colorama>=0.4.6",
    ],
    
    # Scripts CLI
    entry_points={
        "console_scripts": [
            "zenv=zenv_transpiler.cli:main",
            "zv=zenv_transpiler.cli:main",
        ],
    },
    
    # Classificateurs PyPI
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Compilers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    
    # Licence
    license="MIT",
    
    # Mots-clés
    keywords="transpiler, compiler, python, zenv, zv, dsl, code-generation",
)
