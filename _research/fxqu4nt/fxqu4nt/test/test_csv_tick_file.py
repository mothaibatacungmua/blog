import os
import unittest
import shutil

from fxqu4nt.utils.csv_tick_file import *
from fxqu4nt.utils.csv_tick_file import _parse_time
from fxqu4nt.test.test_utils import get_test_data, get_test_dir


csv_file = os.path.join(get_test_data(), "EURUSD.csv")


class TestCsvTickFile(unittest.TestCase):
    def test_head(self):
        n = 10
        with open(csv_file, "r") as fobj:
            lines = [x.strip() for x in fobj.readlines()[:n]]

        buff = head(csv_file, n)
        self.assertEqual("\n".join(lines), buff)

    def test_tail(self):
        self.maxDiff = None
        n = 10
        with open(csv_file, "r") as fobj:
            lines = [x.strip() for x in fobj.readlines()[-n:]]
        buff = tail(csv_file, n)
        self.assertEqual("\n".join(lines), buff)

    def _test_by(self, csv_file, tmp_dir):
        _2010_year_lines = []
        _2011_year_lines = []
        with open(csv_file, "r") as fobj:
            for line in fobj:
                if line.startswith("2010"):
                    _2010_year_lines.append(line.strip())
                if line.startswith("2011"):
                    _2011_year_lines.append(line.strip())

        _2010_year_lines_splitted = []
        _2011_year_lines_splitted = []
        _2010_csv_file = os.path.join(tmp_dir, "2010.csv")
        _2011_csv_file = os.path.join(tmp_dir, "2011.csv")
        with open(_2010_csv_file, "r") as fobj:
            _2010_year_lines_splitted = [x.strip() for x in fobj.readlines()[1:] if len(x.strip())]
        with open(_2011_csv_file, "r") as fobj:
            _2011_year_lines_splitted = [x.strip() for x in fobj.readlines()[1:] if len(x.strip())]

        self.assertEqual(_2010_year_lines, _2010_year_lines_splitted)
        self.assertEqual(_2011_year_lines, _2011_year_lines_splitted)

    def test_split_by_year(self):
        tmp_dir = os.path.join(get_test_dir(), "tmp_split_year")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        split_by_year(csv_file, tmp_dir, verbose=False)
        self._test_by(csv_file, tmp_dir)
        shutil.rmtree(tmp_dir)

    def _test_bm(self, csv_file, tmp_dir):
        month_dict = {}
        with open(csv_file, "r") as fobj:
            for i, line in enumerate(fobj):
                if i == 0:
                    continue
                line = line.strip()
                if not len(line):
                    continue
                dt = _parse_time(line)
                k = f"{dt.year}{dt.month:02d}"
                if k in month_dict:
                    month_dict[k].append(line)
                else:
                    month_dict[k] = [line]
        num_files = len([x for x in os.listdir(tmp_dir) if x.endswith(".csv")])
        self.assertEqual(num_files, len(month_dict))

        split_month_dict = {}
        for x in os.listdir(tmp_dir):
            if x.endswith(".csv"):
                k = x.split(".")[0]
                with open(os.path.join(tmp_dir, x)) as fobj:
                    split_month_dict[k] = [x.strip() for x in fobj.readlines()[1:] if len(x.strip())]
                self.assertEqual(len(month_dict[k]), len(split_month_dict[k]))
                self.assertEqual(month_dict[k], split_month_dict[k])

    def test_split_by_month(self):
        tmp_dir = os.path.join(get_test_dir(), "tmp_split_month")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        split_by_month(csv_file, tmp_dir, verbose=False)
        self._test_bm(csv_file, tmp_dir)
        shutil.rmtree(tmp_dir)

    def test_sub_ranges(self):
        nworkers = 4
        offset_ranges = sub_ranges(csv_file, nworkers=nworkers)
        self.assertEqual(len(offset_ranges), nworkers)

        fsize = get_file_size(csv_file)
        total_size = 0
        with open(csv_file) as fobj:
            for i, r in enumerate(offset_ranges):
                fobj.seek(r[0])

                buff = fobj.read(r[1] - r[0])
                total_size += len(buff)
                if i < nworkers - 1:
                    self.assertEqual(buff[-1], "\n")
                else:
                    self.assertEqual(buff[-1], "5")
        self.assertEqual(fsize, total_size)

    def test_parallel_split_by_year(self):
        tmp_dir = os.path.join(get_test_dir(), "tmp_parallel_split_year")
        parallel_split_by_year(csv_file, tmp_dir, nworkers=10)
        self._test_by(csv_file, tmp_dir)
        shutil.rmtree(tmp_dir)

    def test_parallel_split_by_month(self):
        tmp_dir = os.path.join(get_test_dir(), "tmp_parallel_split_month")
        parallel_split_by_month(csv_file, tmp_dir, nworkers=10)
        self._test_bm(csv_file, tmp_dir)
        shutil.rmtree(tmp_dir)

    def _test_fd(self, csv_file, out_file):
        forigin = open(csv_file, "r")
        origin_lines = forigin.readlines()[1:]

        fconvert = open(out_file, "r")
        convert_lines = fconvert.readlines()[1:]

        self.assertEqual(len(origin_lines), len(convert_lines))

        for l in convert_lines:
            dt = _parse_time(l)
            self.assertLess(dt.weekday(), 5)

    def test_fix_date(self):
        tmp_dir = os.path.join(get_test_dir(), "tmp_fix_date")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        out_file = os.path.join(tmp_dir, "out.csv")
        fix_date(csv_file, out_file, verbose=False)

        self._test_fd(csv_file, out_file)
        shutil.rmtree(tmp_dir)

    def test_parallel_fix_date(self):
        tmp_dir = os.path.join(get_test_dir(), "tmp_fix_date")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        out_file = os.path.join(tmp_dir, "out.csv")
        parallel_fix_date(csv_file, out_file)

        self._test_fd(csv_file, out_file)
        shutil.rmtree(tmp_dir)
