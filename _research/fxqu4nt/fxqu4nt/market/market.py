from fxqu4nt.settings import get_mcnf
from fxqu4nt.market.kdb import QuotesDB

quotes_db = None


class Market(object):
    def __init__(self):
        pass

    def _initialize(self):
        global quotes_db
        # Load configuration
        self.cnf = get_mcnf()

        kdb_cnf = self.cnf["kdb"]
        if quotes_db is None:
            quotes_db = QuotesDB(
                host=kdb_cnf.get("host", "localhost"),
                port=kdb_cnf.get("port", 5042))

