import os
import yaml

_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_CONFIG_DIR, "config.yaml")
_PROJECT_ROOT = os.path.dirname(_CONFIG_DIR)


def load_config() -> dict:
    """加载全局配置文件"""
    with open(_CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


_config = load_config()


def get_current_env() -> str:
    return os.environ.get("API_TEST_ENV", _config.get("current_env", "test"))


def get_base_url() -> str:
    env = get_current_env()
    return _config["environments"][env]["base_url"]


def get_timeout() -> int:
    env = get_current_env()
    return _config["environments"][env].get("timeout", _config["request"]["timeout"])


def get_request_config() -> dict:
    return _config.get("request", {})


def get_project_root() -> str:
    return _PROJECT_ROOT
