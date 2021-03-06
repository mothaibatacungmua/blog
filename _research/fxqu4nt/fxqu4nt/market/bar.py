import os
from abc import ABC, abstractmethod
from collections import namedtuple
from typing import List, Union
from datetime import datetime
import pandas as pd
from pandas import Timestamp
import numpy as np


from fxqu4nt.market.symbol import Symbol
from fxqu4nt.market.kdb import QuotesDB
from fxqu4nt.utils.common import q_dt_str
from fxqu4nt.logger import create_logger

OHLC = namedtuple('OHLC', ['OpenBid', 'HighBid', 'LowBid', 'CloseBid', 'OpenAsk', 'HighAsk', 'LowAsk', 'CloseAsk', 'Volume', 'Start', 'End'])


class BarBase(ABC):
    def fetch(self, sdt, edt):
        pass

    def fisrt_quote_date(self):
        pdFirstDateTime: Timestamp = self.kdb.first_quote_date(self.symbol)
        firstDateTime = pdFirstDateTime.to_pydatetime()
        return firstDateTime


class TickBar(BarBase):
    def __init__(self, kdb: QuotesDB, symbol:[str, Symbol],step_size=50):
        self.kdb = kdb
        self.q = self.kdb.q
        self.symbol = symbol
        self.step_size = step_size
        self.logger = create_logger(self.__class__.__name__)

    def fetch(self, sdt, edt, pandas=False) -> Union[pd.DataFrame, List['OHLC']]:
        tbn = self.kdb.quote_table_name(self.symbol)
        qfmt = ".tickbar.makeBars[{tbn};{step_size};{sdt};{edt}]"
        try:
            query = qfmt.format(tbn=tbn,
                                step_size=str(self.step_size),
                                sdt=q_dt_str(sdt), edt=q_dt_str(edt))
            result = self.q(query, pandas=True)
            self.logger.debug("Execute query: %s" % query)
            if pandas:
                return result
            result = [
                OHLC(OpenBid=r["OpenBid"], HighBid=r["HighBid"], LowBid=r["LowBid"], CloseBid=r["CloseBid"],
                     OpenAsk=r["OpenAsk"], HighAsk=r["HighAsk"], LowAsk=r["LowAsk"], CloseAsk=r["CloseAsk"],
                     Volume=r["Volume"], Start=r["Start"], End=r["End"])
                for idx, r in result.iterrows()
            ]
            return result
        except Exception as e:
            self.logger.error("Fetch tick bar with step size:%d error: %s" % (self.step_size, str(e)))
        return []

    def __repr__(self):
        return "Tick %d Bar" % self.step_size

    def exist(self):
        if isinstance(self.symbol, Symbol):
            name = self.symbol.name
        else:
            name = self.symbol

        bar_path = self.kdb._get_symbol_path(name)
        tbn = "GenTick{tick_size:05d}Bars{symbol}".format(tick_size=self.step_size, symbol=name)
        bar_path = os.path.join(bar_path, tbn)

        if os.path.exists(bar_path):
            return True

        return False

    def generate(self):
        if isinstance(self.symbol, Symbol):
            name = self.symbol.name
        else:
            name = self.symbol

        bar_path = self.kdb._get_symbol_path(name)
        tbn = "GenTick{tick_size:05d}Bars{symbol}".format(tick_size=self.step_size, symbol=name)
        bar_path = os.path.join(bar_path, tbn)
        qtb = self.kdb.quote_table_name(self.symbol)

        self.q.sendSync('.tickbar.genBars',
                         bar_path,
                         tbn, np.bytes_(qtb.encode('utf-8')),
                         np.int32(self.step_size)) # see q/tick_bar.q
        return bar_path
