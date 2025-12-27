from setuptools import setup, find_packages

setup(
    name="zenv",
    version="0.1.0",
    description="Écosystème Zenv - Runtime, CLI et Package Manager",
    author="gopu.inc",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "znv=znv.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
)
