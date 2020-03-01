import time
from qpython import qconnection
from fxqu4nt.logger import create_logger


class QuotesDB(object):
    def __init__(self, host='localhost', port=5042):
        self.logger = create_logger(self.__class__.__name__,  level='info')
        self.q = qconnection.QConnection(host=host, port=port)
        self.q.open()
        time.sleep(1)
        if self.q.is_connected():
            self.logger.info("Connected to kdb+ server. IPC version: %s" % self.q.protocol_version)
        else:
            self.logger.error("Connect to kdb+ server fail!")

    def close(self):
        self.q.close()

    def add_symbols(self, symbols):
        if len(symbols) == 0:
            return

    def add_tick_data(self, symbol, tick_data):
        pass

    def get_symbols(self):
        result = self.q('symbols')
        print(result)

    def update_symbol(self, symbol, ticks):
        pass

    def restore(self):
        pass


if __name__ == "__main__":
    quotes_db = QuotesDB()
    quotes_db.get_symbols()
    quotes_db.close()