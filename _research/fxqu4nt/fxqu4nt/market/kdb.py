import os
import shutil
import time
import qpython
import pandas as pd
from typing import List
from qpython import qconnection

from fxqu4nt.market.symbol import Symbol
from fxqu4nt.logger import create_logger
from fxqu4nt.settings import get_mcnf
from fxqu4nt.utils.common import normalize_path

TICK_SUFFIX = "zTick"
M1_SUFFIX = "zM1"
SYMBOL_META_TABLE = "SymMeta"
SYMBOL_META_TABLE_FILE = "SymMeta.dat"
SYMBOL_PREFIX = "Symbolz"
SYMBOL_DIR = "Symbols"

SUFFIXES = [TICK_SUFFIX, M1_SUFFIX]


class QuotesDB(object):
    def __init__(self, host: str = 'localhost', port: int = 5042, storage: str = None):
        """ QuotesDB init class

        :param host: Host to connect to q server
        :param port: Port to connect to q server
        :param storage: Local storage symbol data
        """
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

    def clone(self):
        return QuotesDB(host=self.host, port=self.port, storage=self.storage)

    def test(self):
        """ Test connect to q server """
        try:
            data = self.q('`int$ til 10')
            if data == list(range(10)):
                return True
            return False
        except Exception as e:
            self.logger.error("Error:%s" % str(e))
        return False

    def _debug(self, query):
        """ Using to logging query string """
        self.logger.debug("Execute query: %s" % query)

    def close(self):
        """ Close q connection """
        self.q.close()

    def quote_table_name(self, symbol: [str, Symbol]):
        """ Get Quote Table name of a symbol

        :param symbol: str or Symbol instance
        :return: Quote Table name of symbol in q
        """
        if isinstance(symbol, Symbol):
            name = symbol.name
        else:
            name = symbol
        return SYMBOL_PREFIX+name+TICK_SUFFIX

    def count_quote_row(self, symbol: [str, Symbol]):
        """ Count number quotes row for symbol

        :param symbol: str or Symbol instance
        :return: Count of quotes
        """
        qfmt = "count select from {tbn}"
        try:
            query = qfmt.format(tbn=self.quote_table_name(symbol))
            result = self.q(query)
            self._debug(query)
            return result
        except Exception as e:
            if isinstance(symbol, Symbol):
                name = symbol.name
            else:
                name = symbol
            self.logger.error("Count quote table for symbol %s error: %s" % (name, str(e)))
        return None

    def first_quote_date(self, symbol: [str, Symbol]):
        """ Get the first quote row for symbol

        :param symbol: str or Symbol instance
        :return: The first quote row
        """
        qfmt = ".Q.ind[{tbn};enlist[0]]"
        try:
            print(self.quote_table_name(symbol))
            query = qfmt.format(tbn=self.quote_table_name(symbol))
            self._debug(query)
            result = self.q(query, pandas=True)
            return result.iloc[0]["DateTime"]
        except Exception as e:
            if isinstance(symbol, Symbol):
                name = symbol.name
            else:
                name = symbol
            self.logger.error("Get first quote row for symbol %s error: %s" % (name, str(e)))
        return None

    def last_quote_date(self, symbol: [str, Symbol]):
        """ Get the last quote row for symbol

        :param symbol: str or Symbol instance
        :return: The last quote row
        """
        qfmt = ".Q.ind[{tbn};{last}]"
        try:
            query = qfmt.format(tbn=self.quote_table_name(symbol), last=self.count_quote_row(symbol))
            result = self.q(query, pandas=True)
            self._debug(query)
            return result.iloc[0]["DateTime"]
        except Exception as e:
            if isinstance(symbol, Symbol):
                name = symbol.name
            else:
                name = symbol
            self.logger.error("Get first quote row for symbol %s error: %s" % (name, str(e)))
        return None

    def add_symbols(self, symbols: List[Symbol]):
        """Add a list symbols

        :param symbols: A list of Symbol instance
        :return:
        """
        if len(symbols) == 0:
            return
        for symbol in symbols:
            self.add_symbol(symbol)

    def add_symbol(self, symbol: Symbol) -> bool:
        """ Add a symbol to meta table

        :param symbol: Symbol to add
        :return: Boolean
        """
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
        self.save_meta_table()
        return True

    def add_tick_data(self, symbol: [str, Symbol], tick_data: str) -> bool:
        """  Add quotes data for a symbol, using if file has a normal size

        :param symbol: Symbol to add, name or `Symbol` instance
        :param tick_data: Csv tick data path
        :return: Boolean
        """
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

    def async_add_tick_data(self, symbol: [str, Symbol], tick_data: str):
        """  Add quotes data for a symbol, using for large file
        The function `tcsvpt` was loaded when program start. The `tcsvqt` will return date which processed on demand.
        See q/quote_csv_partition.q for detail.

        :param symbol: Symbol to add, name or `Symbol` instance
        :param tick_data: Csv tick data path
        :param listener: Listener Thread
        :return: Boolean
        """
        tick_path = normalize_path(tick_data)
        if isinstance(symbol, Symbol):
            name = symbol.name
        else:
            name = symbol
        var = SYMBOL_PREFIX + name + TICK_SUFFIX
        origin_dir = os.path.join(self.storage, SYMBOL_DIR, name, TICK_SUFFIX[1:]).replace("/", "\\")
        symbol_dir = normalize_path(os.path.join(self.storage, SYMBOL_DIR, name, TICK_SUFFIX[1:]))
        try:
            self.q.sendAsync('tcsvpt', symbol_dir, tick_path, var)
            return origin_dir
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
        # TODO:
        raise NotImplementedError

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
                return meta_path
            except Exception as e:
                self.logger.error("Restore SymMeta table error:%s" % str(e))
        return None

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
        qfmt = "\l {path}"
        for sym_name, row in symbol_meta.iterrows():
            sym_dir = os.path.join(self.storage, SYMBOL_DIR, sym_name)
            if not os.path.exists(sym_dir):
                continue
            for suffix in SUFFIXES:
                path = normalize_path(os.path.join(sym_dir, suffix[1:]))
                try:
                    if os.path.exists(path):
                        query = qfmt.format(path=path)
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
        if self.restore_meta_table():
            self.logger.info("Restore Symbol quotes")
            self.restore_symbol_quotes()

    def remove_symbol(self, symbol: [Symbol, str]) -> bool:
        """ Remove symbol's meta data

        :param symbol: Symbol to remove
        :return: Boolean
        """
        self.changed = True
        if isinstance(symbol, Symbol):
            symbol = symbol.name
        qfmt = "delete from `{table} where name=`{symbol}"
        try:
            query = qfmt.format(table=SYMBOL_META_TABLE, symbol=symbol)
            self._debug(query)
            self.q(query)
            self.save_meta_table() # overwrite the current meta table
            return True
        except Exception as e:
            self.logger.error("Remove symbol %s table error:%s" % (symbol, str(e)))
        return False

    def remove_symbol_quotes(self, symbol: [Symbol, str]):
        """ Remove quotes data for a symbol, using for normal file or large file

        :param symbol: Symbol to remove
        :return:
        """
        self.changed = True
        if isinstance(symbol, Symbol):
            symbol = symbol.name
        sym_dir = os.path.join(self.storage, SYMBOL_DIR, symbol)
        qfmt = "$[`{var} in key`.;delete {var} from `.;]"

        # Remove for normal file
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
        # Remove for splayed table
        for suffix in SUFFIXES:
            path = normalize_path(os.path.join(sym_dir, suffix[1:]))
            try:
                if os.path.exists(path):
                    for f in os.listdir(path):
                        if f != ".":
                            rp = os.path.join(path, f)
                            shutil.rmtree(rp)
            except Exception as e:
                self.logger.error("Remove tick data for symbol %s table error:%s" % (symbol, str(e)))

    def load_script(self, script_path):
        """ Load q script

        :param script_path: q script path
        :return:
        """
        script_path = normalize_path(script_path)
        qfmt = "\\l {path}"

        try:
            self.logger.info("Load script %s to kdb" % (script_path))
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
