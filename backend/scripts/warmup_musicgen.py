from transformers import pipeline


def main() -> None:
    pipeline("text-to-audio", "facebook/musicgen-small")


if __name__ == "__main__":
    main()
