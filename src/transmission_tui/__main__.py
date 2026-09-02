"""Command-line entry point."""

from .trackers import TransmissionTUI


def main() -> None:
    TransmissionTUI().run()


if __name__ == "__main__":
    main()
