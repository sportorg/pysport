import subprocess
from pathlib import Path


def main() -> None:
    res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    Path("version").write_text(res.stdout.strip(), encoding="utf-8")


if __name__ == "__main__":
    main()
