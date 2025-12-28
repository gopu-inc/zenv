#!/usr/bin/env python3
"""
Setup configuration pour Zenv Language
"""

from setuptools import setup, find_packages
import os

# Lire le README.md pour la description longue
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Lire les requirements
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="zenv-lang",
    version="1.0.0",
    author="gopu.inc",
    author_email="ceoseshell@gmail.com",
    description="Zenv Language - Écosystème complet avec hub web",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://zenv-hub.vercel.app",
    packages=find_packages(include=["zenv.zenv.*", "zenv.*"]),
    package_data={
        "zenv": [
            "*",
            "*.yaml", 
            "data/*",
            "templates/*",
        ]
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": ["pytest>=7.0.0", "black>=23.0.0", "flake8>=6.0.0"],
        "hub": ["gunicorn>=20.1.0", "psycopg2-binary>=2.9.0"],
        "docs": ["sphinx>=7.0.0", "furo>=2023.0.0"],
    },
    entry_points={
        "console_scripts": [
            "zenv=zenv.__main__:main",
            "znv=zenv.__main__:main",
            "zenv-python=zenv.__main__:main",
        ],
    },
    keywords=["zenv", "language", "package-manager", "hub", "transpiler"],
    project_urls={
        "Homepage": "https://zenv-hub.vercel.app",
        "Documentation": "https://zenv-hub.vercel.app/docs",
        "Source": "https://github.com/gopu-inc/zenv",
        "Tracker": "https://github.com/gopu-inc/zenv/issues",
        "Hub API": "https://zenv-hub.onrender.com/api",
    },
)
