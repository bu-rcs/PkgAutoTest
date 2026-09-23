#!/usr/bin/env python3
"""Assemble a PkgAutoTest report CSV from the per-test row files.

Each runTests task in pkgtest.nf publishes a single-row CSV into the test
results directory as soon as that test finishes.  This script concatenates
those rows into one report and reconciles them against the pipeline's input
CSV, so that a test which produced no row at all is recorded as NO_RESULT
rather than silently missing from the report.

This replaces Nextflow's collectFile(), which is a terminal barrier that never
fires if a task dies without emitting its output file and therefore hangs the
whole pipeline.  Because this script is standalone it can also be run by hand
against a run that was killed:

    collect_report.py --test_results_dir test_results_module_list \\
                      --input module_list.csv \\
                      --output report_module_list.csv

The report's columns are defined by the report_columns map in pkgtest.nf,
which passes the header as --header.
Run by hand without --header, the columns are recovered from the per-test
result files, each of which carries the header as its first line.

Exits non-zero if any test produced no row, so that a cron run surfaces the
discrepancy.
"""

import argparse
import csv
import os
import sys

# The report's columns are defined by the report_columns map in pkgtest.nf,
# which passes the header here as --header and also writes it as the first
# line of every per-test result file.  Edit the columns there, not here.
#
# The first field name, used to recognise a header line inside a result file.
FIRST_COLUMN = 'job_number'

# The column that identifies which input CSV row a result belongs to.  The
# report is reconciled against the input CSV on this column.
KEY_COLUMN = 'test_path'

# How to fill each report column for a test that produced no result, keyed on
# the column name as it appears in the header.  Values are the input CSV column
# to copy from; a column missing from here is filled with 'NA'.  This is keyed
# on names rather than positions so that reordering or adding a report column
# only means editing the report_columns map in pkgtest.nf.
NO_RESULT_FIELDS = {
    'qsub_file':   lambda row: os.path.basename(row.get('test_path') or ''),
    'test_result': lambda row: 'NO_RESULT',
    'module':      lambda row: row.get('module_name_version'),
    'installer':   lambda row: row.get('module_installer'),
    'category':    lambda row: row.get('module_category'),
    'install_date': lambda row: row.get('module_install_date'),
    'test_path':   lambda row: row.get('test_path'),
}


def resolve_header(header, test_results_dir):
    """Return the report's column header line.

    The pipeline passes it as --header.  For a run assembled by hand it is
    recovered from the per-test result files, each of which carries it as its
    first line.  Only a directory with no usable result file leaves us with
    nothing to use, which means no test produced a result at all.
    """
    if header:
        return header.strip()

    if os.path.isdir(test_results_dir):
        for name in sorted(os.listdir(test_results_dir)):
            if not name.endswith('.csv'):
                continue
            try:
                with open(os.path.join(test_results_dir, name)) as fh:
                    first = fh.readline().rstrip('\n')
            except OSError:
                continue
            if first.startswith(FIRST_COLUMN):
                return first

    raise SystemExit(
        'ERROR: no result file in %s to take the report header from.\n'
        '       This means no test produced a result.  Pass the header\n'
        '       explicitly with --header to write a header-only report.'
        % test_results_dir)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--test_results_dir', required=True,
                   help='Directory holding the per-test single-row CSV result files.')
    p.add_argument('--input', required=True,
                   help="The pipeline's input CSV, as produced by find_qsub.py.")
    p.add_argument('--output', required=True,
                   help='Report CSV to write.')
    p.add_argument('--header', default=None,
                   help='The report column header line.  The pipeline passes '
                        'this; when omitted it is taken from the first line '
                        'of a per-test result file.')
    return p.parse_args()


def read_input(path):
    """Return the input CSV rows as a list of dicts, keyed by column name."""
    with open(path, newline='') as fh:
        return list(csv.DictReader(fh))


def collect_rows(test_results_dir, columns):
    """Read every result file in test_results_dir.

    Returns (rows, malformed) where rows is a list of (test_path, line) and
    malformed is a list of (filename, reason).  Files that are empty or
    header-only are reported as malformed rather than skipped silently: on the
    normal onComplete path no copies are in flight, so such a file means
    something actually went wrong.

    The test_path is read from its position in the header rather than from the
    end of the line, so the report's columns can be reordered or extended
    without breaking the reconciliation.
    """
    rows = []
    malformed = []
    nfields = len(columns)
    key_index = columns.index(KEY_COLUMN)

    if not os.path.isdir(test_results_dir):
        return rows, [(test_results_dir, 'test results directory does not exist')]

    for name in sorted(os.listdir(test_results_dir)):
        if not name.endswith('.csv'):
            continue
        full = os.path.join(test_results_dir, name)
        try:
            with open(full) as fh:
                lines = [ln.rstrip('\n') for ln in fh if ln.strip()]
        except OSError as exc:
            malformed.append((name, 'unreadable: %s' % exc))
            continue

        # Drop the per-file header; what remains should be exactly one row.
        data = [ln for ln in lines if not ln.startswith(FIRST_COLUMN)]
        if not data:
            malformed.append((name, 'no data row (empty or header only)'))
            continue

        for line in data:
            fields = line.split(',')
            if len(fields) != nfields:
                malformed.append((name, 'expected %d fields, found %d'
                                  % (nfields, len(fields))))
                continue
            rows.append((fields[key_index].strip(), line))

    return rows, malformed


def no_result_row(in_row, columns):
    """Build a NO_RESULT report row for an input row that produced no output.

    Driven by the shared header's column names, so adding or reordering a
    report column does not need a change here.
    """
    fields = []
    for column in columns:
        fill = NO_RESULT_FIELDS.get(column)
        fields.append((fill(in_row) if fill else None) or 'NA')
    return ', '.join(fields)


def main():
    args = parse_args()

    header = resolve_header(args.header, args.test_results_dir)
    columns = [c.strip() for c in header.split(',')]

    if KEY_COLUMN not in columns:
        raise SystemExit('ERROR: the report header has no %r column, which is '
                         'needed to match results to input rows: %s'
                         % (KEY_COLUMN, header))

    in_rows = read_input(args.input)
    rows, malformed = collect_rows(args.test_results_dir, columns)

    collected = {test_path for test_path, _ in rows}

    # A duplicate test_path in the input CSV would map two tasks onto one row
    # file, and one would overwrite the other.  Warn about it explicitly.
    seen = set()
    duplicates = set()
    for in_row in in_rows:
        tp = (in_row.get('test_path') or '').strip()
        if tp in seen:
            duplicates.add(tp)
        seen.add(tp)

    missing = [in_row for in_row in in_rows
               if (in_row.get('test_path') or '').strip() not in collected]

    with open(args.output, 'w') as out:
        out.write(header + '\n')
        for _, line in rows:
            out.write(line + '\n')
        for in_row in missing:
            out.write(no_result_row(in_row, columns) + '\n')

    print('Report:          %s' % args.output)
    print('Input rows:      %d' % len(in_rows))
    print('Collected rows:  %d  (from %s)' % (len(rows), args.test_results_dir))
    print('Missing rows:    %d  (written as NO_RESULT)' % len(missing))

    for in_row in missing:
        print('  NO RESULT: %s  %s' % (in_row.get('module_name_version'),
                                       in_row.get('test_path')))
    for name, reason in malformed:
        print('  MALFORMED: %s  (%s)' % (name, reason), file=sys.stderr)
    for tp in sorted(duplicates):
        print('  DUPLICATE test_path in %s: %s  (rows overwrite each other)'
              % (args.input, tp), file=sys.stderr)

    if missing or malformed or duplicates:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
