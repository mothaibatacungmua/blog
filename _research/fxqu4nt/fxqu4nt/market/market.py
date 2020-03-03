from fxqu4nt.settings import get_mcnf
from fxqu4nt.market.kdb import get_db


class Market(object):
    def __init__(self):
        self.kdb = get_db()

