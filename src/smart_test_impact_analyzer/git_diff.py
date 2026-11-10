
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ChangedFile:
    path: str
    status: str


def get_changed_files(
    repo_path: Path,
    base_ref: str,
    head_ref: str = "HEAD",
) -> list[ChangedFile]:
    command = [
        "git",
        "diff",
        "--name-status",
        "--find-renames",
        f"{base_ref}...{head_ref}",
    ]

    result = subprocess.run(
        command,
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )

    changed_files = []

    for line in result.stdout.splitlines():
        parts = line.split("\t")

        if not parts:
            continue

        status = parts[0]

        if status.startswith(("R", "C")):
            path = parts[-1]
        elif len(parts) >= 2:
            path = parts[1]
        else:
            continue

        changed_files.append(
            ChangedFile(path=path, status=status)
        )

    return changed_files
