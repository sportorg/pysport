import logging

from PyQt5.QtCore import QSizeF, QMarginsF
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication


def print_html(printer_name, html):
    app = QApplication.instance()
    if app is None:
        app = QApplication(['--platform','minimal'])
    #we need this call to correctly render images...
    app.processEvents()

    printer = QPrinter()
    if printer_name:
        printer.setPrinterName(printer_name)

    printer.setResolution(200)

    text_document = QTextDocument()

    printer.setFullPage(True)
    # printer.setPageMargins(QMarginsF(0, 0, 0, 0))
    printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)
    pt_mm = 25.4 / 72.0
    page_size = QSizeF()
    page_size.setHeight(printer.heightMM())
    page_size.setWidth(min(printer.widthMM(), 80))
    # page_size.setHeight(printer.pageRect().size().height())
    # page_size.setWidth(printer.pageRect().size().width())
    text_document.setPageSize(page_size)
    text_document.setDocumentMargin(5.0 / pt_mm)

    text_document.setHtml(html)

    text_document.print_(printer)


def print_html_webengine(printer_name, html):
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


if __name__ == '__main__':
    print_html(None, "hello, printer")

