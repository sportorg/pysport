import argparse
import re
import sys


CONVENTIONAL_COMMIT_PATTERN = r"^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test){1}(\([\w\-\.]+\))?(!)?: ([\w ])+([\s\S]*)"


def check_pr_title(title: str, pattern: str) -> bool:
    if re.match(pattern, title):
        return True
    else:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check if a PR title matches a regex pattern."
    )
    parser.add_argument("pr_title", type=str, help="Pull request title")
    parser.add_argument(
        "--pattern",
        type=str,
        default=CONVENTIONAL_COMMIT_PATTERN,
        help="Regex pattern to match PR title",
    )
    args = parser.parse_args()

    pr_title = args.pr_title
    regex_pattern = args.pattern

    is_matched = check_pr_title(pr_title, regex_pattern)
    if not is_matched:
        print(
            f"PR '{pr_title}' title does not match the required pattern: {regex_pattern}"
        )
        sys.exit(1)
    else:
        print(f"PR '{pr_title}' title matches the required pattern: {regex_pattern}")


if __name__ == "__main__":
    main()
