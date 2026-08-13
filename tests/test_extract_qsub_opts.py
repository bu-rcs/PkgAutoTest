"""Unit tests for SccModule.extract_qsub_opts() in find_qsub.py.

The qsub options of every #$ directive in a test.qsub are joined into the single
`qsub_options` CSV column, which pkgtest.nf hands to SGE as one clusterOptions
line.  A '#' that survives that join comments out every option after it, so the
per-directive comments have to be removed while the directives are still on
separate lines.  See issue #49.
"""

import importlib.util
import os

FIND_QSUB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'scripts', 'find_qsub.py')


def load_find_qsub():
    ''' Import find_qsub.py by path - it is a script, not an installed module. '''
    spec = importlib.util.spec_from_file_location('find_qsub', FIND_QSUB)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_qsub(tmp_path, *directives):
    ''' Write a minimal test.qsub containing the given #$ directive lines. '''
    qsub = tmp_path / 'test.qsub'
    qsub.write_text('#!/bin/bash -l\n' + '\n'.join(directives) + '\n\nmodule list\n')
    return str(qsub)


def extract(tmp_path, *directives):
    ''' Extract the qsub options from a test.qsub built from these directives. '''
    SccModule = load_find_qsub().SccModule
    return SccModule.extract_qsub_opts(None, write_qsub(tmp_path, *directives))


def test_inline_comment_does_not_hide_later_options(tmp_path):
    ''' The shapeit/5.1.1 case from issue #49: -l avx512 follows a commented
        directive and must still reach SGE. '''
    opts = extract(tmp_path,
                   '#$ -pe omp 4 # Use 4 CPUs',
                   '#$ -l avx512 # Request a node that supports AVX512 and newer CPU instructions')

    assert opts == '-pe omp 4 -l avx512'
    # No '#' may survive: SGE drops everything after one.
    assert '#' not in opts


def test_options_without_comments_are_unchanged(tmp_path):
    ''' Directives that carry no comment keep their existing behavior. '''
    opts = extract(tmp_path, '#$ -pe mpi_16_tasks_per_node 32', '#$ -l h_rt=12:00:00')

    assert opts == '-pe mpi_16_tasks_per_node 32 -l h_rt=12:00:00'


def test_ignored_flags_are_still_dropped(tmp_path):
    ''' -j, -P and -N are supplied by pkgtest.nf and stay filtered out, with or
        without a comment. '''
    opts = extract(tmp_path,
                   '#$ -P scv # set by the pipeline',
                   '#$ -N my_test',
                   '#$ -j y',
                   '#$ -l mem_per_core=8G')

    assert opts == '-l mem_per_core=8G'


def test_comment_only_directive_contributes_nothing(tmp_path):
    ''' A directive commented out in place adds no options - and no stray text
        for the --gpus-only / --no-gpus filters to match on. '''
    opts = extract(tmp_path, '#$ -pe omp 4', '#$ # -l gpus=1 disabled for now')

    assert opts == '-pe omp 4'
    assert '-l gpus' not in opts
