from __future__ import annotations

from poetry.console.commands.command import Command


class CacheListCommand(Command):

    name = "cache list"
    description = "List Poetry's caches."

    def handle(self) -> int | None:
        cache_dir = self.poetry.config.get_repo_cache_dir()

        if cache_dir.exists():
            caches = sorted(cache_dir.iterdir())
            if caches:
                for cache in caches:
                    self.line(f"<info>{cache.name}</>")
                return 0

        self.line_error("<warning>No caches found</>")
        return None
