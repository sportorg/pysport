import logging

import sys
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication


def print_html(printer_name, html):
    printer = QPrinter()
    if printer_name:
        printer.setPrinterName(printer_name)

    # printer.setOutputFormat(QPrinter.PdfFormat)
    # printer.setResolution(printer.HighResolution)
    printer.setResolution(200)

    text_document = QWebEnginePage()

    def callback(is_ok):
        if is_ok:
            print('printing finished')
        else:
            print('printing error')

    def print_exec():
        text_document.print(printer, callback)

    text_document.loadFinished.connect(print_exec)
    text_document.setHtml(html)


def main():
    try:
        printer_name = 'Adobe PDF'
        printer = QPrinter()
        printer.setPrinterName(printer_name)
        text_document = QTextDocument()
        text_document.setHtml("hello")
        text_document.print_(printer)
    except Exception as e:
        logging.exception(e)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main()
    sys.exit(app.exec_())
