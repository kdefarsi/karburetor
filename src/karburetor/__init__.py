"""Karburetor — a KDE Tor client (KDE port of Carburetor)."""

import sys

_CLI_COMMANDS = {
    "start",
    "stop",
    "newid",
    "restart",
    "set",
    "unset",
    "killtor",
}


def main() -> None:
    """
    Dispatch to the CLI backend or the GUI.

    ``karburetor start --verbose`` (or any backend command) runs the tractor
    CLI; a bare ``karburetor`` starts the PySide6/Kirigami GUI.
    """
    if len(sys.argv) > 1 and sys.argv[1] in _CLI_COMMANDS:
        from karburetor.backend.tractor import main as cli_main

        cli_main()
    else:
        from karburetor.app import main as gui_main

        sys.exit(gui_main())
