#!/usr/bin/env python3
"""
启动脚本 - 方便测试
"""
import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import main

if __name__ == "__main__":
    sys.exit(main())