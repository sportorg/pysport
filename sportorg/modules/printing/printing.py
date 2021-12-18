import logging
import sys
from multiprocessing import Process, Queue

from sportorg.gui.global_access import GlobalAccess

from PySide2.QtCore import QSizeF
from PySide2.QtGui import QTextDocument
from PySide2.QtPrintSupport import QPrinter
from PySide2.QtWidgets import QApplication

from sportorg.common.fake_std import FakeStd


class PrintProcess(Process):
    def __init__(self, queue, printer_name, html, left=5.0, top=5.0, right=5.0, bottom=5.0):
        super().__init__()
        self.printer_name = printer_name
        self.html = html
        self.margin_left = left
        self.margin_top = top
        self.margin_right = right
        self.margin_bottom = bottom
        self.queue = queue

    def set_app_printer(self, app, printer):
        self.app = app
        self.printer_name = printer
        self.mw.set_split_printer_app(app)
        self.mw.set_split_printer(printer)

    def run(self):
        #t = time.process_time()
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
                QPrinter.Millimeter,
            )

            page_size = QSizeF()
            page_size.setHeight(printer.height())
            page_size.setWidth(printer.width())
            text_document.setPageSize(page_size)
            text_document.setDocumentMargin(0.0)

            while True:
                #t = time.process_time()
                html = self.queue.get()
                #logging.debug("print_html: New task recived: {}".format(time.process_time() - t))
                text_document.setHtml(html)
                #logging.debug("print_html: text_document setHtml: {}".format(time.process_time() - t))
                text_document.print_(printer)
                #logging.debug("print_html: text_document printing done: {}".format(time.process_time() - t))
        except Exception as e:
            logging.error(str(e))


def print_html(printer_name, html, left=5.0, top=5.0, right=5.0, bottom=5.0, scale=100.0):
    logging.info('print_html: Startin printing poccess')
    thread = GlobalAccess().get_main_window().get_split_printer_thread()
    queue = GlobalAccess().get_main_window().get_split_printer_queue()
    if not queue:
        queue = Queue()
        GlobalAccess().get_main_window().set_split_printer_queue(queue)
        logging.info('print_html:  Queue has been created')
    if not thread:
        thread = PrintProcess(queue, printer_name, html, left, top, right, bottom)
        thread.start()
        GlobalAccess().get_main_window().set_split_printer_thread(thread)
        logging.info('print_html:  Process has been initialized and started has been created')

    queue.put(html)
    logging.info('print_html: Task has been put to queue')
