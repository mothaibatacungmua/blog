from abc import ABC, abstractmethod
from collections import namedtuple
from typing import List, Union
from datetime import datetime
import pandas as pd
from pandas import Timestamp
from fxqu4nt.market.symbol import Symbol
from fxqu4nt.market.kdb import QuotesDB
from fxqu4nt.market.constant import PriceType
from fxqu4nt.utils.common import q_dt_str
from fxqu4nt.logger import create_logger

OHLC = namedtuple('OHLC', ['Open', 'High', 'Low', 'Close', 'Volume', 'Start', 'End'])


class BarBase(ABC):
    def fetch(self, sdt, edt):
        pass

    def fisrt_quote_date(self):
        pdFirstDateTime: Timestamp = self.kdb.first_quote_date(self.symbol)
        firstDateTime = pdFirstDateTime.to_pydatetime()
        return firstDateTime


class TickBar(BarBase):
    def __init__(self, kdb: QuotesDB, symbol:[str, Symbol], price_type=PriceType.Ask, step_size=50):
        self.kdb = kdb
        self.q = self.kdb.q
        self.symbol = symbol
        self.price_type = price_type
        self.step_size = step_size
        self.logger = create_logger(self.__class__.__name__)

    def fetch(self, sdt, edt, pandas=False) -> Union[pd.DataFrame, List['OHLC']]:
        tbn = self.kdb.quote_table_name(self.symbol)
        qfmt = ".tickbar.makeBars[{tbn};`{price_type};{step_size};{sdt};{edt}]"
        try:
            query = qfmt.format(tbn=tbn,
                                price_type=self.price_type.name,
                                step_size=str(self.step_size),
                                sdt=q_dt_str(sdt), edt=q_dt_str(edt))
            result = self.q(query, pandas=True)
            self.logger.debug("Execute query: %s" % query)
            if pandas:
                return result
            result = [
                OHLC(Open=r["Open"], High=r["High"], Low=r["Low"], Close=r["Close"],
                     Volume=r["Volume"], Start=r["Start"], End=r["End"])
                for idx, r in result.iterrows()
            ]
            return result
        except Exception as e:
            self.logger.error("Fetch tick bar with step size:%d error: %s" % (self.step_size, str(e)))
        return []
