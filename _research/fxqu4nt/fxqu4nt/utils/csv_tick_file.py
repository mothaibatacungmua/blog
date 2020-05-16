import os
import mmap
from datetime import datetime, timedelta
import time
import tempfile
import shutil
import multiprocessing as mp
from multiprocessing.managers import ValueProxy
import ctypes

from fxqu4nt.logger import create_logger
from fxqu4nt.utils.common import get_tmp_dir


MAX_BYTES_LINE = 256
CHUNK = mmap.ALLOCATIONGRANULARITY*10

logger = create_logger("CsvTickFile", 'info')


def _parse_time(row):
    dt = row.split(",")[0]
    dt = datetime.strptime(dt, "%Y%m%d %H:%M:%S.%f")
    return dt


def get_file_size(csv_file):
    fobj = open(csv_file, 'rb')
    fobj.seek(0, os.SEEK_END)
    fsize = fobj.tell()
    fobj.close()
    return fsize


def head(csv_file, n):
    n = int(n)
    if n > 1000:
        logger.warning("head() displays only first 1000 lines")
        n = 1000
    max_bytes = MAX_BYTES_LINE * n
    fobj = open(csv_file, 'rb')
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


def tail(csv_file, n):
    n = int(n)
    if n > 1000:
        logger.warning("tail() displays only last 1000 lines")
        n = 1000
    max_bytes = MAX_BYTES_LINE * n
    fobj = open(csv_file, 'rb')
    fsize = get_file_size(csv_file)
    start = (fsize - max_bytes) - (fsize - max_bytes) % mmap.ALLOCATIONGRANULARITY

    mm = mmap.mmap(fobj.fileno(), fsize - start, offset=start, access=mmap.ACCESS_READ)
    buf = []
    start = 0
    end = fsize
    while len(buf) < n:
        found = mm.rfind(b'\n', start, end)
        line = mm[found + 1:end + 1].decode("utf-8")
        buf.insert(0, line)
        end = found - 1

    mm.close()
    fobj.close()
    return "\n".join(buf)


def split_by_month(
        csv_file,
        out_dir=".",
        offset_range=None,
        write_header=True,
        wid=0,
        verbose=True,
        progress: ValueProxy=None):
    """ Split csv quote data by month

    :param csv_file: Input csv file
    :param out_dir: Output directory
    :param offset_range: Range considered in file
    :param write_header: Write out header
    :param wid: Process ID
    :param verbose: Print log
    :param progress: Tracking progress
    :return: Output directory
    """
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    start_time = time.time()
    fobj = open(csv_file, 'r')

    count = 0
    month_lines = []
    current_year = None
    current_month = None
    month_f = None
    fsize = get_file_size(csv_file)

    if offset_range is None:
        offset_range = [0, fsize]
    fobj.seek(offset_range[0])

    prev_offset = fobj.tell()
    header = head(csv_file, 1)
    line = fobj.readline()
    while line:
        if fobj.tell() > offset_range[1]:
            break
        line = line.strip()
        if len(line) == 0:
            line = fobj.readline()
            count += 1
            continue
        if count == 0:
            line = fobj.readline()
            count += 1
            continue
        else:
            dt = _parse_time(line)
            if current_year != dt.year or current_month != dt.month or \
                    current_year is None or current_month is None:
                if month_f is not None:
                    month_f.write("\n" + "\n".join(month_lines))
                    month_f.close()
                    month_lines = []
                month_f = open(os.path.join(out_dir, "%s%02d.csv" % (dt.year, dt.month)), "w")
                if write_header: month_f.write(header)
                current_year = dt.year
                current_month = dt.month
                month_lines.append(line)
                if verbose: logger.info("wid%d/split(): Splitting tick data for %s%02d" % (wid, current_year, current_month))
            else:
                month_lines.append(line)
                if len(month_lines) > 10000:
                    month_f.write("\n" + "\n".join(month_lines))
                    month_lines = []
                    dealed = fobj.tell() - prev_offset
                    per = float(dealed) / fsize
                    prev_offset = fobj.tell()
                    if progress is not None:
                        progress.value += per
        count += 1
        line = fobj.readline()

    # flush year_lines buffer
    month_f.write("\n" + "\n".join(month_lines))
    month_f.close()

    dealed = fobj.tell() - prev_offset
    per = float(dealed) / fsize
    if progress is not None:
        progress.value += per

    end_time = time.time()
    if verbose: logger.info("wid%d/split(): Splitting process token %0.4f seconds" % (wid, end_time - start_time))

    return out_dir


def split_by_year(
        csv_file,
        out_dir=".",
        offset_range=None,
        write_header=True,
        wid=0,
        verbose=True,
        progress: ValueProxy=None):
    """ Split csv quote data by year

    :param csv_file: Input csv file
    :param out_dir: Output directory
    :param offset_range: Range considered in file
    :param write_header: Write out header
    :param wid: Process ID
    :param verbose: Print log
    :param progress: Tracking progress
    :return: Output directory
    """
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    start_time = time.time()
    fobj = open(csv_file, 'r')

    count = 0
    year_lines = []
    current_year = None
    year_f = None
    fsize = get_file_size(csv_file)

    if offset_range is None:
        offset_range = [0, fsize]
    fobj.seek(offset_range[0])

    header = head(csv_file, 1)
    prev_offset = fobj.tell()
    line = fobj.readline()
    while line:
        if fobj.tell() > offset_range[1]:
            break
        line = line.strip()
        if len(line) == 0:
            line = fobj.readline()
            count += 1
            continue
        if count == 0 and offset_range[0] == 0:
            line = fobj.readline()
            count += 1
            continue
        else:
            dt = _parse_time(line)
            if current_year != dt.year or current_year is None:
                if year_f is not None:
                    year_f.write("\n" + "\n".join(year_lines))
                    year_f.close()
                    year_lines = []
                year_f = open(os.path.join(out_dir, "%s.csv" % str(dt.year)), "w")
                if write_header: year_f.write(header)
                current_year = dt.year
                year_lines.append(line)
                if verbose: logger.info("wid%d/split(): Splitting tick data for %d" % (wid, current_year))
            else:
                year_lines.append(line)
                if len(year_lines) > 10000:
                    year_f.write("\n" + "\n".join(year_lines))
                    year_lines = []
                    dealed = fobj.tell() - prev_offset
                    per = float(dealed)/fsize
                    prev_offset = fobj.tell()
                    if progress is not None:
                        progress.value += per
        count += 1
        line = fobj.readline()

    year_f.write("\n" + "\n".join(year_lines))
    year_f.close()

    dealed = fobj.tell() - prev_offset
    per = float(dealed) / fsize
    if progress is not None:
        progress.value += per

    end_time = time.time()
    if verbose: logger.info("wid%d/split(): Splitting process token %0.4f seconds" % (wid, end_time - start_time))

    return out_dir


def fix_date(csv_file, cbfn=None):
    bufflen = 1024*1024*2
    temp_name = next(tempfile._get_candidate_names())
    pdir = os.path.dirname(csv_file)
    temp_path = os.path.join(pdir, temp_name)
    fwrite = open(temp_path, "w")
    with open(csv_file, 'rb') as fobj:
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
                dt = _parse_time(line)
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
    shutil.move(temp_path, csv_file)


def split(csv_file, mode, out_dir="."):
    if mode == "year": return split_by_year(csv_file, out_dir)
    if mode == "month": return split_by_month(csv_file, out_dir)
    logger.error("split() doesn't support mode `%s`" % mode)


def _split_month_worker(csv_file, wid, offset_range):
    tmp_dir = get_tmp_dir()
    save_dir = os.path.join(tmp_dir, f"split_{wid}")
    os.makedirs(save_dir)

    split_by_month(csv_file, out_dir=save_dir, offset_range=offset_range, wid=wid)
    return save_dir


def _split_year_worker(csv_file, wid, offset_range):
    tmp_dir = get_tmp_dir()
    save_dir = os.path.join(tmp_dir, f"split_{wid}")
    os.makedirs(save_dir)

    split_by_year(csv_file, out_dir=save_dir, offset_range=offset_range, wid=wid)
    return save_dir


def sub_ranges(csv_file, nworkers=4):
    fsize = get_file_size(csv_file)

    part_size = int(fsize / nworkers)
    offset = 0
    parts = []

    fobj = open(csv_file, 'rb')
    max_bytes = MAX_BYTES_LINE * 5

    for i in range(0, nworkers):
        fobj.seek(offset + part_size - max_bytes)
        if i == (nworkers - 1):
            buff = fobj.read(max_bytes + MAX_BYTES_LINE * (nworkers + 2))
        else:
            buff = fobj.read(max_bytes)
        if fobj.tell() < fsize:
            found = buff.rfind(b'\n')
        else:
            found = fsize-1
        parts.append((offset, offset + part_size - max_bytes + found+1))
        offset = offset + part_size - max_bytes + found+1
    return parts


def parallel_split_by_month(csv_file, out_dir=".", nworkers=4, progress: ValueProxy=None):
    parts = sub_ranges(csv_file, nworkers=nworkers)
    pool = mp.Pool(processes=nworkers)
    for wid in range(nworkers):
        os.makedirs(os.path.join(out_dir, "wid%d" % wid))
    results = [pool.apply(split_by_month,
                          args=(csv_file, os.path.join(out_dir, "wid%d" % wid), parts[wid], False, wid, False, progress))
                    for wid in range(nworkers)]
    print(results)


def parallel_split_by_year(self, out_dir=".", nworkers=4):
    pass
