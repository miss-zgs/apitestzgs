"""
一键执行入口
用法:
    python run.py                    # 运行全部用例
    python run.py -k test_yaml      # 按关键词筛选
    python run.py --env dev          # 指定环境
"""
import os
import sys

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

import pytest


def main():
    args = sys.argv[1:]

    # 支持 --env 参数切换环境
    if "--env" in args:
        env_index = args.index("--env")
        if env_index + 1 < len(args):
            os.environ["API_TEST_ENV"] = args[env_index + 1]
            args = args[:env_index] + args[env_index + 2:]

    # 默认参数
    default_args = [
        "-v",
        "-s",
        "--tb=short",
    ]

    exit_code = pytest.main(default_args + args)
    sys.exit(exit_code)


if __name__ == "__main__":
    
    main()
    
