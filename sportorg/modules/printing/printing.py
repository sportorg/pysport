import logging
from multiprocessing import Process

from PyQt5.QtCore import QSizeF
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication


class PrintProcess(Process):
    def __init__(self, printer_name, html):
        super().__init__()
        self.printer_name = printer_name
        self.html = html

    def run(self):
        app = QApplication.instance()
        if app is None:
            app = QApplication(['--platform', 'minimal'])
        # we need this call to correctly render images...
        app.processEvents()

        printer = QPrinter()
        if self.printer_name:
            printer.setPrinterName(self.printer_name)

        printer.setResolution(96)

        text_document = QTextDocument()

        printer.setFullPage(True)
        printer.setPageMargins(5, 5, 5, 5, QPrinter.Millimeter)

        page_size = QSizeF()
        page_size.setHeight(printer.height())
        page_size.setWidth(printer.width())
        text_document.setPageSize(page_size)
        text_document.setDocumentMargin(0.0)

        text_document.setHtml(self.html)
        text_document.print_(printer)


def print_html(printer_name, html):
    thread = PrintProcess(printer_name, html)
    thread.start()
    logging.info('printing poccess started')


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
    print_html('Adobe PDF', "hello, printer")

