import time
from qpython import qconnection
from fxqu4nt.logger import create_logger
from fxqu4nt.settings import get_mcnf


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

    def test(self):
        try:
            data = self.q('`int$ til 10')
            if data == list(range(10)):
                return True
            return False
        except Exception as e:
            self.logger.error("Error:%s" % str(e))
        return False

    def close(self):
        self.q.close()

    def add_symbols(self, symbols):
        if len(symbols) == 0:
            return

    def add_tick_data(self, symbol, tick_data):
        pass

    def get_symbols(self):
        result = self.q('SymMeta', pandas=True)
        result.index = result.index.map(lambda x: x.decode("utf-8"))
        for col in ["path"]:
            result[col] = result[col].apply(lambda x: x.decode("utf-8"))
        return result

    def update_symbol(self, symbol, ticks):
        pass

    def restore(self):
        pass


gquotedb = None


def get_db(host=None, port=None):
    global gquotedb
    if gquotedb is None:
        if host is None or port is None:
            cnf = get_mcnf()
            host = cnf["host"]
            port = int(cnf["port"])
        gquotedb = QuotesDB(host=host, port=port)
    return gquotedb
