from setuptools import setup, find_packages
import pathlib

# Lire le README pour la description longue
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="zenv-lang",
    version="0.1.0",
    description="Écosystème Zenv - Runtime, CLI et Package Manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="gopu.inc",
    author_email="ceoseshell@gmail.com",
    url="https://github.com/gopu-inc/zenv",
    project_urls={
        "Documentation": "https://zenv-hub.vercel.app",
        "Source": "https://github.com/gopu-inc/zenv",
        "Tracker": "https://github.com/gopu-inc/zenv/issues",
    },
    license="MIT",
    packages=find_packages(exclude=("tests", "examples")),
    include_package_data=True,  # <-- active MANIFEST.in
    install_requires=[
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "black", "flake8"],
        "docs": ["sphinx", "furo"],
    },
    entry_points={
        "console_scripts": [
            "zenv=zenv.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
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
    keywords="zenv transpiler cli package-manager language",
)
