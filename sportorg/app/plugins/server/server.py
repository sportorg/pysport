from threading import Thread
from .view import *


class ServerThread(Thread):
    def run(self):
        app.run()


def run():
    server = ServerThread()
    server.start()

    return server


def stop():
    pass

if __name__ == '__main__':
    app.run()

print('server plugin')
