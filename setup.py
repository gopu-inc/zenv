#!/usr/bin/env python3
"""
Setup configuration minimal pour Zenv Language
"""

from setuptools import setup, find_packages
import os

# Lire le README.md pour la description longue
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "Zenv Language - Écosystème complet avec hub web"

setup(
    name="zenv-lang",
    version="1.0.0",
    author="gopu.inc",
    author_email="ceoseshell@gmail.com",
    description="Zenv Language - Écosystème complet avec hub web zenv-hub.vercel.app",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://zenv-hub.vercel.app",
    
    # Trouver automatiquement les packages
    packages=find_packages(),
    
    # Dépendance unique
    install_requires=[
        "requests>=2.28.0",
    ],
    
    # Entry points pour les commandes CLI
    entry_points={
        "console_scripts": [
            "zenv=zenv.__main__:main",
            "znv=zenv.__main__:main",
        ],
    },
    
    # Classifiers pour PyPI
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
    
    # Metadata additionnelle
    keywords=["zenv", "language", "package-manager", "hub", "python", "env", "environnementvirtuel"],
    project_urls={
        "Homepage": "https://zenv-hub.vercel.app",
        "Source": "https://github.com/gopu-inc/zenv",
        "Bug Reports": "https://github.com/gopu-inc/zenv/issues",
        "Hub API": "https://zenv-hub.onrender.com/api",
    },
)
