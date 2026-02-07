#!/usr/bin/env python3
"""
Evermemos - Entry Point

Run the Evermemos memory system demo.
Usage:
    python main.py          # Run full demo
    python main.py --test   # Run quick test
    python main.py --api    # Start API server (if implemented)
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.demo import run_demo, run_quick_test


def main():
    """Main entry point."""
    args = sys.argv[1:]
    
    if "--test" in args:
        success = run_quick_test()
        sys.exit(0 if success else 1)
    elif "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)
    else:
        run_demo()


if __name__ == "__main__":
    main()
