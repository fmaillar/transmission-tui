"""Command-line entry point."""

from .location import TransmissionTUI


def main() -> None:
    TransmissionTUI().run()


if __name__ == "__main__":
    main()
