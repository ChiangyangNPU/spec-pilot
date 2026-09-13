#!/usr/bin/env python3
"""启动脚本：python todo.py <子命令> ..."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from todo.cli import main

if __name__ == "__main__":
    sys.exit(main())
