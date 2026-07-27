from __future__ import annotations

import shutil


def limited_syntax_command(base_command: list[str]) -> list[str]:
    """Wrap a syntax-only tool with local resource limits when prlimit exists."""
    limiter = shutil.which("prlimit")
    if limiter is None:
        return base_command
    return [
        limiter,
        "--as=536870912",
        "--cpu=4",
        "--fsize=1048576",
        "--nofile=64",
        "--",
        *base_command,
    ]
