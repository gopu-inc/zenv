#!/usr/bin/env python3
"""
Zenv Language CLI Entry Point
"""

import sys
from .cli import ZenvCLI

def main():
    cli = ZenvCLI()
    sys.exit(cli.run(sys.argv[1:]))

if __name__ == "__main__":
    main()
