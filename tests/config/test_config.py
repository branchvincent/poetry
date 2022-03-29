from __future__ import annotations

import os
import re

from typing import TYPE_CHECKING
from typing import Callable
from typing import Iterator

import pytest

from flatdict import FlatDict

from poetry.config.config import Config
from poetry.config.config import boolean_normalizer
from poetry.config.config import int_normalizer


if TYPE_CHECKING:
    from pathlib import Path

KNOWN_KEYS = FlatDict(Config.default_config, delimiter=".").keys()


def get_options_based_on_normalizer(normalizer: Callable) -> Iterator[str]:
    for k in KNOWN_KEYS:
        if Config._get_validator_and_normalizer(k)[1] == normalizer:
            yield k


@pytest.mark.parametrize(
    ("name", "value"), [("installer.parallel", True), ("virtualenvs.create", True)]
)
def test_config_get_default_value(config: Config, name: str, value: bool):
    assert config.get(name) is value


def test_config_get_processes_depended_on_values(
    config: Config, config_cache_dir: Path
):
    assert str(config_cache_dir / "virtualenvs") == config.get("virtualenvs.path")


def generate_environment_variable_tests() -> Iterator[tuple[str, str, str, bool]]:
    for normalizer, values in [
        (boolean_normalizer, [("true", True), ("false", False)]),
        (int_normalizer, [("4", 4), ("2", 2)]),
    ]:
        for env_value, value in values:
            for name in get_options_based_on_normalizer(normalizer=normalizer):
                env_var = "POETRY_" + re.sub("[.-]+", "_", name).upper()
                yield name, env_var, env_value, value


@pytest.mark.parametrize(
    ("name", "env_var", "env_value", "value"),
    list(generate_environment_variable_tests()),
)
def test_config_get_from_environment_variable(
    config: Config,
    environ: Iterator[None],
    name: str,
    env_var: str,
    env_value: str,
    value: bool,
):
    os.environ[env_var] = env_value
    assert config.get(name) is value


@pytest.mark.parametrize(
    ("name", "expected"),
    [(k, True) for k in KNOWN_KEYS]
    + [(k, False) for k in {"foo", "bar", "virtualenvs", "virtualenvs.options"}],
)
def test_config_is_key_valid(config: Config, name: str, expected: bool):
    assert config.is_key_valid(name) is expected
