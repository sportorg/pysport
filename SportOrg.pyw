#!/usr/bin/env python3
import sys


def report_fatal(error) -> None:
    """Explain an unusable installation before there is a main window."""
    message = (
        "SportOrg cannot create the directory it needs to store data in:\n\n"
        "{}\n{}\n\n"
        "Move the program to a location you can write to, or install it "
        "with an installer."
    ).format(error.path, error.reason)

    print(message, file=sys.stderr)

    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
    except ModuleNotFoundError:
        try:
            from PySide2.QtWidgets import QApplication, QMessageBox
        except ModuleNotFoundError:
            return

    app = QApplication.instance() or QApplication(sys.argv)  # noqa: F841
    QMessageBox.critical(None, "SportOrg", message)


def main() -> None:
    from sportorg.startup import PathsError, init

    try:
        init()
    except PathsError as error:
        report_fatal(error)
        raise SystemExit(1)

    # Imported only after init(): importing this module builds the whole GUI.
    from sportorg.gui.main import Application

    Application().run()


if __name__ == '__main__':
    main()
