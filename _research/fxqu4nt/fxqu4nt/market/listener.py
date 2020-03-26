from threading import Thread, Event
from qpython import qconnection


class Listener(Thread):
    def __init__(self, q=None):
        super(Listener, self).__init__()
        self.q = q
        self._stopper = Event()

    def stop(self):
        self._stopper.set()

    def stopped(self):
        return self._stopper.isSet()

    def set_q(self, q: qconnection.QConnection):
        self.q = q