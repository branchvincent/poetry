from __future__ import annotations

import os
import re

from copy import deepcopy
from functools import reduce
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable

from poetry.config.dict_config_source import DictConfigSource
from poetry.locations import CACHE_DIR


if TYPE_CHECKING:
    from poetry.config.config_source import ConfigSource

Validator = Callable[[str], Any]
Normalizer = Callable[[str], Any]


def boolean_validator(val: str) -> bool:
    return val in {"true", "false", "1", "0"}


def boolean_normalizer(val: str) -> bool:
    return val in ["true", "1"]


def int_normalizer(val: str) -> int:
    return int(val)


class Config:

    default_config: dict[str, Any] = {
        "cache-dir": CACHE_DIR,
        "virtualenvs": {
            "create": True,
            "in-project": None,
            "path": os.path.join("{cache-dir}", "virtualenvs"),
            "options": {"always-copy": False, "system-site-packages": False},
            "prefer-active-python": False,
        },
        "experimental": {"new-installer": True},
        "installer": {"parallel": True, "max-workers": None},
    }

    def __init__(
        self, use_environment: bool = True, base_dir: Path | None = None
    ) -> None:
        self._config = deepcopy(self.default_config)
        self._use_environment = use_environment
        self._base_dir = base_dir
        self._config_source: ConfigSource = DictConfigSource()
        self._auth_config_source: ConfigSource = DictConfigSource()

    @property
    def config(self) -> dict:
        return self._config

    @property
    def config_source(self) -> ConfigSource:
        return self._config_source

    @property
    def auth_config_source(self) -> ConfigSource:
        return self._auth_config_source

    def set_config_source(self, config_source: ConfigSource) -> Config:
        self._config_source = config_source

        return self

    def set_auth_config_source(self, config_source: ConfigSource) -> Config:
        self._auth_config_source = config_source

        return self

    def merge(self, config: dict[str, Any]) -> None:
        from poetry.utils.helpers import merge_dicts

        merge_dicts(self._config, config)

    def all(self) -> dict[str, Any]:
        def _all(config: dict, parent_key: str = "") -> dict:
            all_ = {}

            for key in config:
                value = self.get(parent_key + key)
                if isinstance(value, dict):
                    if parent_key != "":
                        current_parent = parent_key + key + "."
                    else:
                        current_parent = key + "."
                    all_[key] = _all(config[key], parent_key=current_parent)
                    continue

                all_[key] = value

            return all_

        return _all(self.config)

    def raw(self) -> dict[str, Any]:
        return self._config

    def get(self, setting_name: str, default: Any = None) -> Any:
        """
        Retrieve a setting value.
        """
        keys = setting_name.split(".")

        # Looking in the environment if the setting
        # is set via a POETRY_* environment variable
        if self._use_environment:
            env = "POETRY_" + "_".join(k.upper().replace("-", "_") for k in keys)
            env_value = os.getenv(env)
            if env_value is not None:
                _, normalizer = self._get_validator_and_normalizer(setting_name)
                return self.process(normalizer(env_value))

        value = self._config
        for key in keys:
            if key not in value:
                return self.process(default)

            value = value[key]

        return self.process(value)

    def get_repo_cache_dir(self) -> Path:
        return Path(self.get("cache-dir")) / "cache" / "repositories"

    def process(self, value: Any) -> Any:
        if not isinstance(value, str):
            return value

        return re.sub(r"{(.+?)}", lambda m: self.get(m.group(1)), value)

    @staticmethod
    def _get_validator_and_normalizer(name: str) -> tuple[Validator, Normalizer]:
        if name in {
            "virtualenvs.create",
            "virtualenvs.in-project",
            "virtualenvs.options.always-copy",
            "virtualenvs.options.system-site-packages",
            "virtualenvs.options.prefer-active-python",
            "experimental.new-installer",
            "installer.parallel",
        }:
            return boolean_validator, boolean_normalizer

        if name in {"cache-dir", "virtualenvs.path"}:
            return str, lambda val: str(Path(val))

        if name == "installer.max-workers":
            return lambda val: int(val) > 0, int_normalizer

        return lambda val: val, lambda val: val

    @classmethod
    def is_key_valid(cls, key: str) -> bool:
        try:
            value = reduce(lambda d, k: d[k], key.split("."), cls.default_config)
            is_leaf = not isinstance(value, dict)
            return is_leaf
        except KeyError:
            return False
