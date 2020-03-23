from threading import Thread
from qpython import qconnection


class Listener(Thread):
    def set_q(self, q: qconnection.QConnection):
        self.q = q