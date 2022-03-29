from __future__ import annotations

import uuid

from pathlib import Path
from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from cleo.testers.command_tester import CommandTester

    from poetry.config.config import Config
    from tests.types import CommandTesterFactory


@pytest.fixture
def repository_cache_dir(config: Config) -> Path:
    path = Path(config.get("cache-dir")) / "cache" / "repositories"
    path.mkdir(parents=True)
    return path


@pytest.fixture
def repository_one() -> str:
    return f"01_{uuid.uuid4()}"


@pytest.fixture
def repository_two() -> str:
    return f"02_{uuid.uuid4()}"


@pytest.fixture
def mock_caches(
    repository_cache_dir: Path, repository_one: str, repository_two: str
) -> None:
    (repository_cache_dir / repository_one).mkdir()
    (repository_cache_dir / repository_two).mkdir()


@pytest.fixture
def tester(command_tester_factory: CommandTesterFactory) -> CommandTester:
    return command_tester_factory("cache list")


def test_cache_list(
    tester: CommandTester, mock_caches: None, repository_one: str, repository_two: str
):
    tester.execute()

    expected = f"""\
{repository_one}
{repository_two}
"""

    assert tester.io.fetch_output() == expected


def test_cache_list_empty(tester: CommandTester, repository_cache_dir: Path):
    tester.execute()

    expected = """\
No caches found
"""

    assert tester.io.fetch_error() == expected
