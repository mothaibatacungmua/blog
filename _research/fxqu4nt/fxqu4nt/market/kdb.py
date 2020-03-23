import os
import time
import qpython
import pandas as pd
from typing import List
from qpython import qconnection

from fxqu4nt.market.symbol import Symbol
from fxqu4nt.logger import create_logger
from fxqu4nt.settings import get_mcnf
from fxqu4nt.utils.common import normalize_path
from fxqu4nt.market.listener import Listener

TICK_SUFFIX = "wTICK"
M1_SUFFIX = "wM1"
SYMBOL_META_TABLE = "SymMeta"
SYMBOL_META_TABLE_FILE = "SymMeta.dat"
SYMBOL_PREFIX = "Symbolw"
SYMBOL_DIR = "Symbols"

SUFFIXES = [TICK_SUFFIX, M1_SUFFIX]


class QuotesDB(object):
    def __init__(self, host: str = 'localhost', port: int = 5042, storage: str = None):
        self.host = host
        self.port = port
        self.storage = storage
        self.logger = create_logger(self.__class__.__name__,  level='debug')
        self.q: qconnection.QConnection = qconnection.QConnection(host=host, port=port)
        self.q.open()
        time.sleep(0.1)
        self.changed = False
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

    def _debug(self, query):
        self.logger.debug("Execute query: %s" % query)

    def close(self):
        self.q.close()

    def add_symbols(self, symbols: List[Symbol]):
        if len(symbols) == 0:
            return

    def add_symbol(self, symbol: Symbol):
        sym_meta = self.get_symbols()
        if sym_meta is None:
            if not self.create_empty_sym_meta():
                return False
            else:
                columns = ["name", "point", "min_vol", "max_vol", "vol_step"]
                sym_meta = pd.DataFrame(columns=columns)
                sym_meta.set_index("name")
        if symbol.name in sym_meta.index:
            self.logger.warning("Symbol was existed, please change symbol's settings by the update function")
            return False
        query = "`{table} insert (`{name};{point:0.7f};{min_vol:0.7f};{max_vol:0.7f};{vol_step:0.7f})"\
                .format(table=SYMBOL_META_TABLE,
                        name=symbol.name,
                        point=symbol.point,
                        min_vol=symbol.min_vol,
                        max_vol=symbol.max_vol,
                        vol_step=symbol.vol_step)
        try:
            self._debug(query)
            self.q(query)
            self.logger.info("Symbol added with settings:%s" % str(symbol))
        except Exception as e:
            self.logger.error("Add Symbol to SymMeta table error:%s" % str(e))
            return False
        self.changed = True
        return True

    def add_tick_data(self, symbol: [str, Symbol], tick_data: str):
        tick_path = normalize_path(tick_data)
        if isinstance(symbol, Symbol):
            name = symbol.name
        else:
            name = symbol
        var = SYMBOL_PREFIX+name+TICK_SUFFIX
        query = '{var}:("ZFFI"; enlist ",") 0:`:{path}'\
            .format(var=var, path=tick_path)

        first_date_q = 'select [1] from `{var}'.format(var=var)
        last_date_q = 'select [-1] from `{var}'.format(var=var)

        try:
            self._debug(query)
            self.q(query)

            fd_df = self.q(first_date_q, pandas=True)
            ld_df = self.q(last_date_q, pandas=True)
            fd = fd_df.iloc[0]["DateTime"]
            ld = ld_df.iloc[0]["DateTime"]
            self.logger.info("Tick data Symbol %s added, from: %s to: %s" % (name, str(fd), str(ld)))
        except Exception as e:
            self.logger.error("Add tick data for symbol %s error:%s" % (name, str(e)))
            return False
        return True

    def async_add_tick_data(self, symbol: [str, Symbol], tick_data: str, listener: Listener):
        tick_path = normalize_path(tick_data)
        if isinstance(symbol, Symbol):
            name = symbol.name
        else:
            name = symbol
        symbol_dir = normalize_path(os.path.join(self.storage, SYMBOL_DIR, name, "quotes"))
        # the function `csvpt` was loaded when program start. See q/quote_csv_partition.q for detail
        listener.start()
        listener.set_q(self.q)
        try:
            self.q.sendAsync('csvpt', symbol_dir, tick_path)
        except Exception as e:
            self.logger.error("Add tick data for symbol %s error:%s" % (name, str(e)))

    def get_symbols(self):
        try:
            result = self.q('SymMeta', pandas=True)
        except qpython.qtype.QException:
            return None
        result.index = result.index.map(lambda x: x.decode("utf-8"))
        return result

    def update_symbol(self, symbol, ticks):
        pass

    def is_symbol_exist(self, symbol: str):
        query = "select from {table} where name=`{name}".format(table=SYMBOL_META_TABLE, name=symbol)
        try:
            self._debug(query)
            result = self.q(query, pandas=True)
            if result.empty:
                return False
            return True
        except qpython.qtype.QException:
            return False

    def create_empty_sym_meta(self):
        query = "{table}:([name: ()] point:(); min_vol:(); max_vol:(); vol_step:())".format(table=SYMBOL_META_TABLE)
        try:
            self._debug(query)
            self.q(query)
        except Exception as e:
            self.logger.error("Create empty SymMeta table error:%s" % str(e))
            return False
        self.changed = True
        return True

    def _get_symbol_path(self, symbol_name):
        return normalize_path(os.path.join(self.storage, SYMBOL_DIR, symbol_name))

    def _get_meta_table_path(self):
        return normalize_path(os.path.join(self.storage, SYMBOL_META_TABLE_FILE))

    def save_meta_table(self):
        meta_path = self._get_meta_table_path()
        query = "`:{path} set {table}".format(path=meta_path, table=SYMBOL_META_TABLE)
        try:
            self._debug(query)
            self.q(query)
        except Exception as e:
            self.logger.error("Create empty SymMeta table error:%s" % str(e))
            return False
        return True

    def restore_meta_table(self):
        meta_path = self._get_meta_table_path()
        if os.path.exists(meta_path):
            query = "{table}:(get `:{path})".format(table=SYMBOL_META_TABLE, path=meta_path)
            try:
                self._debug(query)
                self.q(query)
            except Exception as e:
                self.logger.error("Restore SymMeta table error:%s" % str(e))

    def save_symbol_quotes(self):
        symbol_meta = self.get_symbols()
        qfmt = "$[`{var} in key`.;`:{path} set {var};]"
        for sym_name, row in symbol_meta.iterrows():
            sym_dir = os.path.join(self.storage, SYMBOL_DIR, sym_name)
            if not os.path.exists(sym_dir):
                os.makedirs(sym_dir)

            for suffix in SUFFIXES:
                var = SYMBOL_PREFIX + sym_name + suffix
                path = normalize_path(os.path.join(sym_dir, suffix[1:]+".dat"))
                try:
                    query = qfmt.format(var=var, path=path)
                    self._debug(query)
                    self.q(query)
                except Exception as e:
                    self.logger.error("Save tick data for symbol %s table error:%s" % (sym_name, str(e)))

    def restore_symbol_quotes(self):
        symbol_meta = self.get_symbols()
        qfmt = "{var}:(get `:{path})"
        for sym_name, row in symbol_meta.iterrows():
            sym_dir = os.path.join(self.storage, SYMBOL_DIR, sym_name)
            if not os.path.exists(sym_dir):
                continue
            for suffix in SUFFIXES:
                var = SYMBOL_PREFIX + sym_name + suffix
                path = normalize_path(os.path.join(sym_dir, suffix[1:] + ".dat"))
                try:
                    if os.path.exists(path):
                        query = qfmt.format(var=var, path=path)
                        self._debug(query)
                        self.q(query)
                except Exception as e:
                    self.logger.error("Restore tick data for symbol %s table error:%s" % (sym_name, str(e)))

    def save_all(self):
        if self.changed:
            self.logger.info("Saving SymMeta table...")
            self.save_meta_table()
            self.logger.info("Saving Symbol quotes...")
            self.save_symbol_quotes()

    def restore_all(self):
        self.logger.info("Restore SymMeta table")
        self.restore_meta_table()
        self.logger.info("Restore Symbol quotes")
        self.restore_symbol_quotes()

    def remove_symbol(self, symbol: [Symbol, str]):
        self.changed = True
        if isinstance(symbol, Symbol):
            symbol = symbol.name
        qfmt = "delete from `{table} where name=`{symbol}"
        try:
            query = qfmt.format(table=SYMBOL_META_TABLE, symbol=symbol)
            self._debug(query)
            self.q(query)
            self.save_meta_table() # overwrite the current meta table
        except Exception as e:
            self.logger.error("Remove symbol %s table error:%s" % (symbol, str(e)))

    def remove_symbol_quotes(self, symbol: [Symbol, str]):
        self.changed = True
        if isinstance(symbol, Symbol):
            symbol = symbol.name
        sym_dir = os.path.join(self.storage, SYMBOL_DIR, symbol)
        qfmt = "$[`{var} in key`.;delete {var} from `.;]"
        for suffix in SUFFIXES:
            var = SYMBOL_PREFIX + symbol + suffix
            path = normalize_path(os.path.join(sym_dir, suffix[1:] + ".dat"))
            try:
                query = qfmt.format(var=var, path=path)
                self._debug(query)
                self.q(query)
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                self.logger.error("Remove tick data for symbol %s table error:%s" % (symbol, str(e)))

    def load_script(self, script_path):
        script_path = normalize_path(script_path)
        qfmt = "\\l {path}"

        try:
            query = qfmt.format(path=script_path)
            self._debug(query)
            self.q(query)
        except Exception as e:
            self.logger.error("Load script %s to kdb server error:%s" % (script_path, str(e)))


gquotedb = None


def get_db(host=None, port=None, storage=None) -> QuotesDB:
    global gquotedb
    if gquotedb is None:
        if host is None or port is None:
            cnf = get_mcnf()
            host = cnf["host"]
            port = int(cnf["port"])
            storage = cnf["storage"]
        gquotedb = QuotesDB(host=host, port=port, storage=storage)
    return gquotedb
