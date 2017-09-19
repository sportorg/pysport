import traceback

import sys

from PyQt5.QtCore import QTemporaryFile
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication


def print_html(printer_name, html):
    printer = QPrinter()
    if printer_name:
        printer.setPrinterName(printer_name)

    # text_document = QTextDocument()
    # text_document.setHtml("html")
    # text_document.print_(printer)

    text_document = QWebEnginePage()
    text_document.setHtml(html)
    def callback(is_ok):
        print('printing finished:' + is_ok)
    text_document.print(printer, callback)

    # tmp = QTemporaryFile().fileName()
    # text_document.printToPdf(tmp)


def main():
    try:
        printer_name = 'Adobe PDF'
        printer = QPrinter()
        printer.setPrinterName(printer_name)
        text_document = QTextDocument()
        text_document.setHtml("hello")
        text_document.print_(printer)
    except:
        traceback.print_exc()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main()
    sys.exit(app.exec_())
