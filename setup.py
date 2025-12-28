from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="zenv-lang",
    version="1.0.0",
    author="gopu.inc",
    author_email="contact@zenv.dev",
    description="Zenv Language - Écosystème complet de développement",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gopu-inc/zenv-lang",
    packages=find_packages(where="python"),
    package_dir={"": "python"},
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
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.28.0",
        "PyJWT>=2.6.0",
        "bcrypt>=4.0.0",
        "flask>=2.3.0",
        "flask-cors>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "zenv=zenv.__main__:main",
            "znv=zenv.__main__:main",
            "zenv-py=zenv.__main__:main",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "hub": [
            "gunicorn>=20.1.0",
            "psycopg2-binary>=2.9.0",
        ]
    },
    project_urls={
        "Bug Reports": "https://github.com/gopu-inc/zenv-lang/issues",
        "Source": "https://github.com/gopu-inc/zenv-lang",
        "Documentation": "https://zenv-hub.vercel.app",
        "Hub": "https://zenv-hub.vercel.app",
    },
)
