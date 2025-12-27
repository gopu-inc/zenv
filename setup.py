# setup.py
from setuptools import setup, find_packages

setup(
    name="zenv-ecosystem",
    version="1.0.0",
    description="Écosystème complet Zenv - Runtime, CLI et Package Manager",
    author="Votre Nom",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "PyJWT>=2.6.0",
        "bcrypt>=4.0.0",
        "flask>=2.3.0",
        "flask-cors>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "zenv=zenv.cli:main",      # CLI comme pip
            "znv=znv.__main__:main",   # Runtime comme python
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
)
