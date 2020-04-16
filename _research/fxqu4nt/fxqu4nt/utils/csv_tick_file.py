import os
import mmap
from datetime import datetime, timedelta
from fxqu4nt.logger import create_logger
import time
import tempfile
import shutil


MAX_BYTES_LINE = 256
CHUNK = mmap.ALLOCATIONGRANULARITY*10


class CsvTickFile(object):
    def __init__(self, fpath):
        self.logger = create_logger(self.__class__.__name__, 'info')
        self.fpath = fpath
        self.get_size()

    def get_size(self):
        fobj = open(self.fpath, 'rb')
        fobj.seek(0, os.SEEK_END)
        self.fsize = fobj.tell()
        fobj.close()

    def fix_date(self, cbfn=None):
        bufflen = 1024*1024*2
        temp_name = next(tempfile._get_candidate_names())
        pdir = os.path.dirname(self.fpath)
        temp_path = os.path.join(pdir, temp_name)
        fwrite = open(temp_path, "w")
        with open(self.fpath, 'rb') as fobj:
            buff = fobj.read(bufflen) # 16Mb
            remainder = b''
            lidx = buff.rfind(b'\n')
            if lidx < len(buff)-1 and lidx >= 0:
                remainder = buff[lidx+1:]
                buff = buff[:lidx]
            while len(buff):
                lines = [l.decode('utf-8') for l in buff.split(b'\n')]
                wbuff = []
                for line in lines:
                    line = line.strip()
                    if len(line) == 0:
                        continue
                    if line.startswith("DateTime"):
                        fwrite.write(line + "\n")
                        continue
                    dt = self._parse_time(line)
                    while dt.weekday() >= 5:
                        dt = dt - timedelta(seconds=3600*24)
                    patch_line = line.split(",")
                    patch_line[0] = dt.strftime("%Y%m%d %H:%M:%S.%f")
                    wbuff.append(",".join(patch_line))

                fwrite.write("\n".join(wbuff) + "\n")
                fwrite.flush()
                if not cbfn is None: cbfn(fobj) # callback to track progress
                buff = remainder + fobj.read(bufflen)  # 16Mb
                lidx = buff.rfind(b'\n')
                remainder = b''
                if lidx < len(buff) - 1 and lidx >= 0:
                    remainder = buff[lidx + 1:]
                    buff = buff[:lidx]

        fwrite.close()
        shutil.move(temp_path, self.fpath)
        self.get_size()

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

    def _parse_time(self, row):
        dt = row.split(",")[0]
        dt = datetime.strptime(dt, "%Y%m%d %H:%M:%S.%f")
        return dt

    def _split_by_year(self, out_dir="."):
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        header = None
        start_time = time.time()
        fobj = open(self.fpath, 'rb')

        start = 0
        buf = fobj.read(CHUNK)
        count = 0
        year_lines = []
        current_year = None
        year_f = None

        while len(buf) > 0:
            line = b''
            last = buf.rfind(b'\n', 0, len(buf))
            start = start + last + 1
            if fobj.tell() < self.fsize:
                fobj.seek(start)
            # extract line from buf
            for c in buf[:last+1]:
                c = bytes([c])
                if c != b'\n': line += c
                else:
                    line = line.decode("utf-8").strip()
                    if len(line) == 0:
                        continue
                    if count == 0:
                        header = line
                    else:
                        dt = self._parse_time(line)
                        if current_year != dt.year or current_year is None:
                            if year_f is not None:
                                year_f.write("\n" + "\n".join(year_lines))
                                year_f.close()
                                year_lines = []
                            year_f = open(os.path.join(out_dir, "%s.csv" % str(dt.year)), "w")
                            year_f.write(header)
                            current_year = dt.year
                            year_lines.append(line)
                            self.logger.info("split(): Splitting tick data for %d" % current_year)
                        else:
                            year_lines.append(line)
                            if len(year_lines) > 10000:
                                year_f.write("\n" + "\n".join(year_lines))
                                year_lines = []
                    count += 1
                    line = b''

            if fobj.tell() != self.fsize:
                buf = fobj.read(CHUNK)
            else:
                # flush year_lines buffer
                year_f.write("\n" + "\n".join(year_lines))
                year_f.close()
                break
        end_time = time.time()
        self.logger.info("split(): Splitting process token %0.4f seconds" % (end_time - start_time))

    def _split_by_month(self, out_dir="."):
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        header = None
        start_time = time.time()
        fobj = open(self.fpath, 'rb')

        start = 0
        buf = fobj.read(CHUNK)
        count = 0
        month_lines = []
        current_year = None
        current_month = None
        month_f = None

        while len(buf) > 0:
            line = b''
            last = buf.rfind(b'\n', 0, len(buf))
            start = start + last + 1
            if fobj.tell() < self.fsize:
                fobj.seek(start)
            # extract line from buf
            for c in buf[:last + 1]:
                c = bytes([c])
                if c != b'\n':
                    line += c
                else:
                    line = line.decode("utf-8").strip()
                    if len(line) == 0:
                        continue
                    if count == 0:
                        header = line
                    else:
                        dt = self._parse_time(line)
                        if current_year != dt.year or current_month != dt.month or \
                                current_year is None or current_month is None:
                            if month_f is not None:
                                month_f.write("\n" + "\n".join(month_lines))
                                month_f.close()
                                month_lines = []
                            month_f = open(os.path.join(out_dir, "%s%02d.csv" % (dt.year, dt.month)), "w")
                            month_f.write(header)
                            current_year = dt.year
                            current_month = dt.month
                            month_lines.append(line)
                            self.logger.info("split(): Splitting tick data for %s%02d" % (current_year, current_month))
                        else:
                            month_lines.append(line)
                            if len(month_lines) > 10000:
                                month_f.write("\n" + "\n".join(month_lines))
                                month_lines = []
                    count += 1
                    line = b''

            if fobj.tell() != self.fsize:
                buf = fobj.read(CHUNK)
            else:
                # flush year_lines buffer
                month_f.write("\n" + "\n".join(month_lines))
                month_f.close()
                break
        end_time = time.time()
        self.logger.info("split(): Splitting process token %0.4f seconds" % (end_time - start_time))

    def split(self, mode, out_dir="."):
        if mode == "year": return self._split_by_year(out_dir)
        if mode == "month": return self._split_by_month(out_dir)
        self.logger.error("split() doesn't support mode `%s`" % mode)
