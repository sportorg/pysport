import sys
import logging
from multiprocessing import Process

from PyQt5.QtCore import QSizeF
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication

from sportorg.core.fake_std import FakeStd


class PrintProcess(Process):
    def __init__(self, printer_name, html, left=5.0, top=5.0, right=5.0, bottom=5.0):
        super().__init__()
        self.printer_name = printer_name
        self.html = html
        self.margin_left = left
        self.margin_top = top
        self.margin_right = right
        self.margin_bottom = bottom

    def run(self):
        try:
            sys.stdout = FakeStd()
            sys.stderr = FakeStd()
            app = QApplication.instance()
            if app is None:
                app = QApplication(['--platform', 'minimal'])
            # we need this call to correctly render images...
            app.processEvents()

            printer = QPrinter()
            if self.printer_name:
                printer.setPrinterName(self.printer_name)

            # printer.setResolution(96)

            text_document = QTextDocument()

            printer.setFullPage(True)
            printer.setPageMargins(
                self.margin_left,
                self.margin_top,
                self.margin_right,
                self.margin_bottom,
                QPrinter.Millimeter
            )

            page_size = QSizeF()
            page_size.setHeight(printer.height())
            page_size.setWidth(printer.width())
            text_document.setPageSize(page_size)
            text_document.setDocumentMargin(0.0)

            text_document.setHtml(self.html)
            text_document.print_(printer)
        except Exception as e:
            logging.error(str(e))


def print_html(printer_name, html, left=5.0, top=5.0, right=5.0, bottom=5.0):
    thread = PrintProcess(printer_name, html, left, top, right, bottom)
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
