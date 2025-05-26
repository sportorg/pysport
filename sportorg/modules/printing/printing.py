import logging
import sys
import time
from multiprocessing import Process, Queue

try:
    from PySide6.QtCore import QMarginsF, QSizeF
    from PySide6.QtGui import QPageLayout, QTextDocument
    from PySide6.QtPrintSupport import QPrinter
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError:
    from PySide2.QtCore import QMarginsF, QSizeF
    from PySide2.QtGui import QPageLayout, QTextDocument
    from PySide2.QtPrintSupport import QPrinter
    from PySide2.QtWidgets import QApplication

from sportorg.common.fake_std import FakeStd
from sportorg.gui.global_access import GlobalAccess


class PrintProcess(Process):
    def __init__(
        self, queue, printer_name, html, left=5.0, top=5.0, right=5.0, bottom=5.0
    ):
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
        t = time.process_time()
        try:
            sys.stdout = FakeStd()
            sys.stderr = FakeStd()
            logging.debug("print_html: RUN")
            app = QApplication.instance()
            if app is None:
                app = QApplication(["--platform", "minimal"])
                # we need this call to correctly render images...
            app.processEvents()

            logging.debug(
                "print_html: App instance is ready done: {}".format(
                    time.process_time() - t
                )
            )

            printer = QPrinter()
            if self.printer_name:
                printer.setPrinterName(self.printer_name)

            logging.debug(
                "print_html: got Printer done: {}".format(time.process_time() - t)
            )

            # printer.setResolution(96)

            text_document = QTextDocument()

            printer.setFullPage(True)
            printer.setPageMargins(
                QMarginsF(
                    self.margin_left,
                    self.margin_top,
                    self.margin_right,
                    self.margin_bottom,
                ),
                QPageLayout.Unit.Millimeter,
            )

            page_size = QSizeF()
            page_size.setHeight(printer.height())
            page_size.setWidth(printer.width())
            text_document.setPageSize(page_size)
            text_document.setDocumentMargin(0.0)

            while True:
                t = time.process_time()
                html = self.queue.get()
                if html == "CLOSE_SPLIT_PRN":
                    app.quit()
                    logging.debug(
                        "print_html: printing thread termination: {}".format(
                            time.process_time() - t
                        )
                    )
                    break

                logging.debug(
                    "print_html: New task received: {}".format(time.process_time() - t)
                )

                text_document.setHtml(html)

                logging.debug(
                    "print_html: text_document setHtml: {}".format(
                        time.process_time() - t
                    )
                )

                text_document.print_(printer)

                # without this timeout virtual printer (e.g. Adobe PDF) doesn't print task, having more than 1 split
                time.sleep(0.25)

                logging.debug(
                    "print_html: text_document printing done: {}".format(
                        time.process_time() - t
                    )
                )
        except Exception as e:
            logging.error(str(e))


def print_html(
    printer_name, html, left=5.0, top=5.0, right=5.0, bottom=5.0, scale=100.0
):
    logging.info("print_html: Starting printing process")
    thread = GlobalAccess().get_main_window().get_split_printer_thread()
    queue = GlobalAccess().get_main_window().get_split_printer_queue()
    if not queue:
        queue = Queue()
        GlobalAccess().get_main_window().set_split_printer_queue(queue)
        logging.info("print_html:  Queue created")
    if not thread:
        thread = PrintProcess(queue, printer_name, html, left, top, right, bottom)
        thread.start()
        GlobalAccess().get_main_window().set_split_printer_thread(thread)
        logging.info("print_html:  Process initialized and started")

    queue.put(html)
    logging.info("print_html: Task has been put to queue")
