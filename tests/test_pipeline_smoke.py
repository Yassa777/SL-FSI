from __future__ import annotations

from slfsi.cli import build_parser


def test_cli_commands_present() -> None:
    parser = build_parser()
    commands = [
        "version",
        "show-config",
        "build-panel",
        "download-external",
        "fetch-historical",
        "train-hmm",
        "validate",
        "leading-indicators",
        "mercado",
        "combine",
        "theory",
        "analyze",
    ]
    for command in commands:
        args = parser.parse_args([command])
        assert args.command == command
