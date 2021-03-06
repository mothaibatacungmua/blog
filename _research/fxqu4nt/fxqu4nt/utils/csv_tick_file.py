import os
import mmap
from datetime import datetime, timedelta
import time
import tempfile
import shutil
import multiprocessing as mp
from multiprocessing.managers import ValueProxy

from fxqu4nt.logger import create_logger


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


def _check_start_and_write(fobj, lines):
    if fobj.tell() > 0:
        fobj.write("\n" + "\n".join(lines))
    else:
        fobj.write("\n".join(lines))


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
        line = line.strip()
        if fobj.tell() == offset_range[1] or fobj.tell() == fsize:
            if len(line): month_lines.append(line)
            break
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
            if current_year != dt.year or current_month != dt.month or \
                    current_year is None or current_month is None:
                if month_f is not None:
                    _check_start_and_write(month_f, month_lines)
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
                    _check_start_and_write(month_f, month_lines)
                    month_lines = []
                    dealed = fobj.tell() - prev_offset
                    per = float(dealed) / fsize
                    prev_offset = fobj.tell()
                    if progress is not None:
                        progress.value += per
        count += 1
        line = fobj.readline()

    # flush year_lines buffer
    _check_start_and_write(month_f, month_lines)
    month_f.close()

    dealed = fobj.tell() - prev_offset
    per = float(dealed) / fsize
    if progress is not None:
        progress.value += per

    end_time = time.time()
    if verbose: logger.info("wid%d/split(): Splitting process token %0.4f seconds, number of lines:%d" % (wid, end_time - start_time, count))

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
        line = line.strip()
        if fobj.tell() == offset_range[1] or fobj.tell() == fsize:
            if len(line): year_lines.append(line)
            break
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
                    _check_start_and_write(year_f, year_lines)
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
                    _check_start_and_write(year_f, year_lines)
                    year_lines = []
                    dealed = fobj.tell() - prev_offset
                    per = float(dealed)/fsize
                    prev_offset = fobj.tell()
                    if progress is not None:
                        progress.value += per
        count += 1
        line = fobj.readline()

    _check_start_and_write(year_f, year_lines)
    year_f.close()

    dealed = fobj.tell() - prev_offset
    per = float(dealed) / fsize
    if progress is not None:
        progress.value += per

    end_time = time.time()
    if verbose: logger.info("wid%d/split(): Splitting process token %0.4f seconds, number of lines:%d" % (wid, end_time - start_time, count))

    return out_dir


def _fix_sample(line):
    dt = _parse_time(line)
    while dt.weekday() >= 5:
        dt = dt - timedelta(seconds=3600 * 24)
    patch_line = line.split(",")
    second_part = patch_line[0].split(" ")[1]
    first_part = f"{dt.year}{dt.month:02d}{dt.day:02d}"
    patch_line[0] = first_part + " " + second_part
    return ",".join(patch_line)


def fix_date(
        csv_file,
        out_file=None,
        offset_range=None,
        write_header=True,
        wid=0,
        verbose=True,
        progress: ValueProxy=None):
    """

    :param csv_file: Input csv file
    :param out_file: Output csv file (Optional)
    :param offset_range: Range considered in file
    :param write_header: Write out header
    :param wid: Process ID
    :param verbose: Print log
    :param progress: Tracking progress
    :return:
    """
    temp_name = next(tempfile._get_candidate_names())
    pdir = os.path.dirname(csv_file)
    temp_path = os.path.join(pdir, temp_name)
    fwrite = open(temp_path, "w")

    fsize = get_file_size(csv_file)
    fobj = open(csv_file, 'r')

    if offset_range is None:
        offset_range = [0, fsize]
    fobj.seek(offset_range[0])
    count = 0
    header = head(csv_file, 1)
    prev_offset = fobj.tell()
    patch_lines = []

    start_time = time.time()
    if write_header: fwrite.write(header)
    line = fobj.readline()
    while line:
        line = line.strip()
        if fobj.tell() > (offset_range[1] + 1):
            break
        if fobj.tell() == offset_range[1] or fobj.tell() == fsize:
            if len(line): patch_lines.append(_fix_sample(line))
            break
        if len(line) == 0:
            line = fobj.readline()
            count += 1
            continue
        if count == 0 and offset_range[0] == 0:
            line = fobj.readline()
            count += 1
            continue
        else:
            patch_lines.append(_fix_sample(line))
            if len(patch_lines) > 10000:
                _check_start_and_write(fwrite, patch_lines)
                patch_lines = []
                dealed = fobj.tell() - prev_offset
                per = float(dealed) / fsize
                prev_offset = fobj.tell()
                if progress is not None:
                    progress.value += per
        count += 1
        line = fobj.readline()
    _check_start_and_write(fwrite, patch_lines)
    fwrite.close()
    end_time = time.time()
    if verbose: logger.info("wid%d/split(): Splitting process token %0.4f seconds, number of lines:%d" % (wid, end_time - start_time, count))

    dealed = fobj.tell() - prev_offset
    per = float(dealed) / fsize
    if progress is not None:
        progress.value += per
    if out_file:
        shutil.move(temp_path, out_file)
        return out_file
    shutil.move(temp_path, csv_file)
    return csv_file


def split(csv_file, mode, out_dir="."):
    if mode == "year": return split_by_year(csv_file, out_dir)
    if mode == "month": return split_by_month(csv_file, out_dir)
    logger.error("split() doesn't support mode `%s`" % mode)


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


def _parallel_split(csv_file, out_dir=".", mode="month", nworkers=4, progress: ValueProxy=None):
    parts = sub_ranges(csv_file, nworkers=nworkers)
    pool = mp.Pool(processes=nworkers)
    for wid in range(nworkers):
        p = os.path.join(out_dir, "wid%d" % wid)
        if os.path.exists(p):
            shutil.rmtree(p)
        os.makedirs(p)

    if mode == "month":
        split_fn = split_by_month
    elif mode == "year":
        split_fn = split_by_year
    else:
        raise ValueError(f"Not support split mode {mode}")

    results = []
    def track_result(x):
        results.append(x)
    workers = [pool.apply_async(split_fn,
              args=(
              csv_file, os.path.join(out_dir, "wid%d" % wid), parts[wid], False, wid, True, progress), callback=track_result)
               for wid in range(nworkers)]
    for p in workers:
        p.wait()
    results = sorted(results)
    header = head(csv_file, 1)
    fobj = None

    for d in results:
        for f in sorted(list(os.listdir(d))):
            fp = os.path.join(out_dir, f)
            fpp = os.path.join(d, f)
            if not os.path.exists(fp):
                if fobj: fobj.close()
                fobj = open(fp, "w")
                fobj.write(header)
                fobj.write("\n")
            with open(fpp, "r") as part_obj:
                buff = part_obj.read(8092)
                while buff:
                    fobj.write(buff)
                    buff = part_obj.read(8092)
            fobj.write("\n")
    if fobj: fobj.close()
    for d in results:
        shutil.rmtree(d)


def parallel_split_by_month(csv_file, out_dir=".", nworkers=4, progress: ValueProxy=None):
    return _parallel_split(
        csv_file,
        out_dir=out_dir,
        mode="month",
        nworkers=nworkers,
        progress=progress)


def parallel_split_by_year(csv_file, out_dir=".", nworkers=4, progress: ValueProxy=None):
    return _parallel_split(
        csv_file,
        out_dir=out_dir,
        mode="year",
        nworkers=nworkers,
        progress=progress)


def parallel_fix_date(csv_file, out_file=None, nworkers=4, progress: ValueProxy=None):
    if out_file is None:
        out_dir = os.path.dirname(csv_file)
        basename = os.path.basename(csv_file)
    else:
        out_dir = os.path.dirname(out_file)
        basename = os.path.basename(out_file)
    parts = sub_ranges(csv_file, nworkers=nworkers)
    pool = mp.Pool(processes=nworkers)
    for wid in range(nworkers):
        p = os.path.join(out_dir, "wid%d" % wid)
        if os.path.exists(p):
            shutil.rmtree(p)
        os.makedirs(p)

    basenames = [os.path.join(out_dir, "wid%d" % wid, basename) for wid in range(nworkers)]
    results = []

    def track_result(x):
        results.append(x)

    workers = [pool.apply_async(fix_date,
                                args=(
                                    csv_file, basenames[wid], parts[wid], False, wid, True,
                                    progress), callback=track_result)
               for wid in range(nworkers)]
    for p in workers:
        p.wait()

    results = sorted(results)
    header = head(csv_file, 1)

    fout = open(out_file, "w")
    fout.write(header + "\n")

    for d in results:
        with open(d) as fobj:
            buff = fobj.read(8092)
            while buff:
                fout.write(buff)
                buff = fobj.read(8092)
        fout.write("\n")

    fout.close()
    return out_file