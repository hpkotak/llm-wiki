import sys


def count_tokens(text: str) -> int:
    return len(text.split())


if __name__ == "__main__":
    print(count_tokens(open(sys.argv[1], encoding="utf-8").read()))
