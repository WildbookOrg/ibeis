# -*- coding: utf-8 -*-
# Autogenerated on 12:54:39 2017/06/25
# flake8: noqa
from __future__ import absolute_import, division, print_function, unicode_literals
from wbia.algo.verif import clf_helpers
from wbia.algo.verif import sklearn_utils
from wbia.algo.verif import deploy
from wbia.algo.verif import pairfeat
from wbia.algo.verif import verifier
from wbia.algo.verif import vsone
import utool

print, rrr, profile = utool.inject2(__name__, '[wbia.algo.verif]')


def reassign_submodule_attributes(verbose=1):
    """
    Updates attributes in the __init__ modules with updated attributes
    in the submodules.
    """
    import sys

    if verbose and '--quiet' not in sys.argv:
        print('dev reimport')
    # Self import
    import wbia.algo.verif

    # Implicit reassignment.
    seen_ = set([])
    for tup in IMPORT_TUPLES:
        if len(tup) > 2 and tup[2]:
            continue  # dont import package names
        submodname, fromimports = tup[0:2]
        submod = getattr(wbia.algo.verif, submodname)
        for attr in dir(submod):
            if attr.startswith('_'):
                continue
            if attr in seen_:
                # This just holds off bad behavior
                # but it does mimic normal util_import behavior
                # which is good
                continue
            seen_.add(attr)
            setattr(wbia.algo.verif, attr, getattr(submod, attr))


def reload_subs(verbose=1):
    """ Reloads wbia.algo.verif and submodules """
    if verbose:
        print('Reloading wbia.algo.verif submodules')
    rrr(verbose > 1)

    def wrap_fbrrr(mod):
        def fbrrr(*args, **kwargs):
            """ fallback reload """
            if verbose > 0:
                print('Auto-reload (using rrr) not setup for mod=%r' % (mod,))

        return fbrrr

    def get_rrr(mod):
        if hasattr(mod, 'rrr'):
            return mod.rrr
        else:
            return wrap_fbrrr(mod)

    def get_reload_subs(mod):
        return getattr(mod, 'reload_subs', wrap_fbrrr(mod))

    get_rrr(clf_helpers)(verbose > 1)
    get_rrr(sklearn_utils)(verbose > 1)
    get_rrr(vsone)(verbose > 1)
    rrr(verbose > 1)
    try:
        # hackish way of propogating up the new reloaded submodule attributes
        reassign_submodule_attributes(verbose=verbose)
    except Exception as ex:
        print(ex)


rrrr = reload_subs

IMPORT_TUPLES = [
    ('clf_helpers', None),
    ('sklearn_utils', None),
    ('vsone', None),
    ('deploy', None),
    ('verifier', None),
    ('pairfeat', None),
]
"""
Regen Command:
    cd /home/joncrall/code/wbia/wbia/algo/verif
    makeinit.py --modname=wbia.algo.verif
"""
