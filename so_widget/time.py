import threading
import time


class Clock(threading.Thread):
    def __init__(self, master, start_time=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.master = master
        self.start_time = start_time

    def run(self):
        while True:
            t = time.strftime("%H:%M:%S", time.gmtime())
            self.master['text'] = t
            time.sleep(1)
