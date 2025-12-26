#!/usr/bin/env python3
"""
Setup configuration for Zenv Transpiler
Package installer and configuration for zenv -> Python transpiler
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

# Version check
if sys.version_info < (3, 6):
    print("Zenv Transpiler requires Python 3.6 or higher")
    sys.exit(1)

# ---------- README extraction ----------
def read_file(filename: str) -> str:
    """Read the contents of a file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def get_long_description() -> str:
    """Get the long description from README.md"""
    base_dir = Path(__file__).parent
    readme_path = base_dir / 'README.md'
    if readme_path.exists():
        return read_file(str(readme_path))
    return "Zenv Transpiler - A .zv/.zenv to Python transpiler"

# ---------- Version extraction ----------
def find_version() -> str:
    """Extract version from __init__.py"""
    base_dir = Path(__file__).parent
    init_path = base_dir / 'zenv_transpiler' / '__init__.py'
    
    if init_path.exists():
        content = read_file(str(init_path))
        version_match = re.search(
            r"^__version__\s*=\s*['\"]([^'\"]*)['\"]",
            content, 
            re.M
        )
        if version_match:
            return version_match.group(1)
    
    # Fallback version
    return "1.0.0"

# ---------- Custom test command ----------
class PyTest(TestCommand):
    """Custom test command to run pytest"""
    user_options = [
        ('test-path=', None, 'Test path to run'),
        ('test-match=', None, 'Test matching pattern'),
        ('cov', None, 'Enable coverage reporting'),
        ('cov-report=', None, 'Coverage report type'),
        ('cov-config=', None, 'Coverage config file'),
    ]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.test_path = 'tests'
        self.test_match = None
        self.cov = False
        self.cov_report = 'term'
        self.cov_config = '.coveragerc'

    def finalize_options(self):
        TestCommand.finalize_options(self)

    def run_tests(self):
        # Import here because outside the eggs aren't loaded
        import pytest
        import shlex
        
        params = []
        if self.test_match:
            params.extend(['-k', self.test_match])
        
        if self.cov:
            params.extend([
                '--cov', 'zenv_transpiler',
                '--cov-report', self.cov_report,
                '--cov-config', self.cov_config
            ])
        
        params.append(self.test_path)
        sys.exit(pytest.main(params))

# ---------- Package data discovery ----------
def get_package_data() -> Dict[str, List[str]]:
    """Get non-Python files to include in package"""
    return {
        'zenv_transpiler': [
            '*.py',
            '*.txt',
            '*.md',
            '*',
        ],
    }

# ---------- Entry points ----------
def get_entry_points() -> Dict[str, List[str]]:
    """Get console scripts and GUI entry points"""
    return {
        'console_scripts': [
            'zenv=zenv_transpiler.cli:main',
            'zenv-transpile=zenv_transpiler.cli:main',
            'zv=zenv_transpiler.cli:main',
        ],
        'gui_scripts': [],
    }

# ---------- Classifiers ----------
CLASSIFIERS = [
    # Development status
    'Development Status :: 4 - Beta',
    
    # Intended audience
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Compilers',
    'Topic :: Software Development :: Code Generators',
    
    # License
    'License :: OSI Approved :: MIT License',
    
    # Supported Python versions
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    
    # Operating systems
    'Operating System :: OS Independent',
    'Operating System :: POSIX',
    'Operating System :: Unix',
    'Operating System :: MacOS',
    'Operating System :: Microsoft :: Windows',
    
    # Typing
    'Typing :: Typed',
]

# ---------- Keywords ----------
KEYWORDS = [
    'transpiler',
    'compiler',
    'python',
    'zenv',
    'zv',
    'language',
    'dsl',
    'code-generation',
    'syntax',
    'translator',
]

# ---------- Project URLs ----------
PROJECT_URLS = {
    'Documentation': 'https://github.com/gopu-inc/zenv#readme',
    'Source Code': 'https://github.com/gopu-inc/zenv',
    'Bug Tracker': 'https://github.com/gopu-inc/zenv/issues',
    'Changelog': 'https://github.com/gopu-inc/zenv/releases',
}

# ---------- Dependencies ----------
INSTALL_REQUIRES = [
    # Core dependencies
    'colorama>=0.4.6',  # For colored terminal output
]

# Optional dependencies for additional features
EXTRAS_REQUIRE = {
    'dev': [
        'pytest>=7.0.0',
        'pytest-cov>=4.0.0',
        'black>=22.0.0',
        'mypy>=0.990',
        'flake8>=6.0.0',
        'pre-commit>=3.0.0',
        'twine>=4.0.0',
        'build>=0.10.0',
    ],
    'format': [
        'black>=22.0.0',
        'yapf>=0.32.0',
    ],
    'test': [
        'pytest>=7.0.0',
        'pytest-cov>=4.0.0',
        'pytest-xdist>=3.0.0',
    ],
    'docs': [
        'sphinx>=5.0.0',
        'sphinx-rtd-theme>=1.0.0',
        'myst-parser>=1.0.0',
    ],
}

# Test dependencies (minimal set)
TESTS_REQUIRE = [
    'pytest>=7.0.0',
]

# ---------- Setup configuration ----------
setup(
    # Basic information
    name='zenv-transpiler',
    version=find_version(),
    author='GOPU.inc',
    author_email='ceoseshell@gmail.com',
    maintainer='gopu.inc',
    maintainer_email='ceoseshell@gmail.com',
    
    # Description
    description='A .zv/.zenv to Python transpiler with advanced features',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    
    # URLs
    url='https://github.com/username/zenv',
    project_urls=PROJECT_URLS,
    
    # Package discovery
    packages=find_packages(
        include=['zenv_transpiler', 'zenv_transpiler.*'],
        exclude=['tests', 'tests.*', 'examples', 'examples.*'],
    ),
    package_dir={'zenv_transpiler': 'zenv_transpiler'},
    package_data=get_package_data(),
    include_package_data=True,
    zip_safe=False,
    
    # Dependencies
    python_requires='>=3.6',
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    tests_require=TESTS_REQUIRE,
    
    # Entry points
    entry_points=get_entry_points(),
    
    # Classifiers
    classifiers=CLASSIFIERS,
    keywords=KEYWORDS,
    
    # License
    license='MIT',
    
    # Platforms
    platforms=['any'],
    
    # Custom commands
    cmdclass={
        'test': PyTest,
    },
    
    # Options
    options={
        'bdist_wheel': {
            'universal': True,
        },
        'egg_info': {
            'tag_build': '',
            'tag_date': False,
        },
    },
    
    # Scripts (alternative to entry_points)
    scripts=[],
    
    # Data files
    data_files=[
        ('share/doc/zenv-transpiler', [
            'README.md',
            'LICENSE',
            'CHANGELOG.md',
            'CONTRIBUTING.md',
        ]),
        ('share/zenv-transpiler/examples', [
            'examples/hello.zv',
            'examples/lists.zv',
            'examples/functions.zv',
        ]),
    ],
    
    # Additional metadata
    provides=['zenv_transpiler'],
    obsoletes=['old-zenv-transpiler'],
    
    # Contact
    contact='Your Name',
    contact_email='ceoseshell@gmail.com',
    
    # Support
    support='ceoseshell@gmail.com',
    
    # Download URL
    download_url='https://github.com/gopu-inc/zenv/releases',
)

# ---------- Post-install message ----------
if 'install' in sys.argv:
    print("\n" + "="*60)
    print("Zenv Transpiler installed successfully!")
    print("="*60)
    print("\nTo use the transpiler:")
    print("  $ zenv file.zv                    # Transpile and display")
    print("  $ zenv file.zv -o output.py      # Transpile to file")
    print("  $ zenv file.zv --run             # Transpile and run")
    print("  $ zenv --interactive             # Interactive mode")
    print("\nExamples are available in:")
    print("  /usr/local/share/zenv-transpiler/examples/")
    print("  or")
    print("  ~/.local/share/zenv-transpiler/examples/")
    print("="*60 + "\n")