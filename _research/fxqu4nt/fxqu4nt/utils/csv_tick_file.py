import os
import mmap
import logging
from fxqu4nt.logger import create_logger

MAX_BYTES_LINE = 256


class CsvTickFile(object):
    def __init__(self, fpath):
        self.logger = create_logger(self.__class__.__name__, 'info')
        self.fpath = fpath
        fobj = open(fpath, 'rb')
        fobj.seek(0, os.SEEK_END)
        self.fsize = fobj.tell()
        fobj.close()

    def head(self, n):
        n = int(n)
        if n > 1000:
            self.logger.warning("head() displays only first 1000 lines")
            n = 1000
        max_bytes = MAX_BYTES_LINE * n
        fobj = open(self.fpath, 'rb')
        mm = mmap.mmap(fobj.fileno(), max_bytes, access=mmap.ACCESS_READ)
        buf = []
        offset = 0
        while len(buf) < n:
            found = mm.find(b'\n', offset)
            line = mm[offset:found].decode("utf-8")
            offset = found + 1
            buf.append(line)
        mm.close()
        fobj.close()
        return "\n".join(buf)

    def tail(self, n):
        n = int(n)
        if n > 1000:
            self.logger.warning("tail() displays only last 1000 lines")
            n = 1000
        max_bytes = MAX_BYTES_LINE * n
        fobj = open(self.fpath, 'rb')
        start = (self.fsize - max_bytes) - (self.fsize - max_bytes) % mmap.ALLOCATIONGRANULARITY
        mm = mmap.mmap(fobj.fileno(), max_bytes, offset=start, access=mmap.ACCESS_READ)
        buf = []
        start = 0
        end = max_bytes
        while len(buf) < n:
            found = mm.rfind(b'\n', start, end)
            line = mm[found+1:end+1].decode("utf-8")
            buf.insert(0, line)
            end = found - 1

        mm.close()
        fobj.close()
        return "\n".join(buf)
