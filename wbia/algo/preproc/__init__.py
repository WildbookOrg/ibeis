# -*- coding: utf-8 -*-
# Autogenerated on 19:52:29 2016/03/14
# flake8: noqa
from __future__ import absolute_import, division, print_function, unicode_literals
from wbia.algo.preproc import preproc_annot
from wbia.algo.preproc import preproc_image
from wbia.algo.preproc import preproc_occurrence
from wbia.algo.preproc import preproc_residual
from wbia.algo.preproc import preproc_rvec
import utool

print, rrr, profile = utool.inject2(__name__, '[wbia.algo.preproc]')


def reassign_submodule_attributes(verbose=True):
    """
    why reloading all the modules doesnt do this I don't know
    """
    import sys

    if verbose and '--quiet' not in sys.argv:
        print('dev reimport')
    # Self import
    import wbia.algo.preproc

    # Implicit reassignment.
    seen_ = set([])
    for tup in IMPORT_TUPLES:
        if len(tup) > 2 and tup[2]:
            continue  # dont import package names
        submodname, fromimports = tup[0:2]
        submod = getattr(wbia.algo.preproc, submodname)
        for attr in dir(submod):
            if attr.startswith('_'):
                continue
            if attr in seen_:
                # This just holds off bad behavior
                # but it does mimic normal util_import behavior
                # which is good
                continue
            seen_.add(attr)
            setattr(wbia.algo.preproc, attr, getattr(submod, attr))


def reload_subs(verbose=True):
    """ Reloads wbia.algo.preproc and submodules """
    if verbose:
        print('Reloading submodules')
    rrr(verbose=verbose)

    def wrap_fbrrr(mod):
        def fbrrr(*args, **kwargs):
            """ fallback reload """
            if verbose:
                print('No fallback relaod for mod=%r' % (mod,))
            # Breaks ut.Pref (which should be depricated anyway)
            # import imp
            # imp.reload(mod)

        return fbrrr

    def get_rrr(mod):
        if hasattr(mod, 'rrr'):
            return mod.rrr
        else:
            return wrap_fbrrr(mod)

    def get_reload_subs(mod):
        return getattr(mod, 'reload_subs', wrap_fbrrr(mod))

    get_rrr(preproc_annot)(verbose=verbose)
    get_rrr(preproc_image)(verbose=verbose)
    get_rrr(preproc_occurrence)(verbose=verbose)
    get_rrr(preproc_residual)(verbose=verbose)
    get_rrr(preproc_rvec)(verbose=verbose)
    rrr(verbose=verbose)
    try:
        # hackish way of propogating up the new reloaded submodule attributes
        reassign_submodule_attributes(verbose=verbose)
    except Exception as ex:
        print(ex)


rrrr = reload_subs

IMPORT_TUPLES = [
    ('preproc_annot', None),
    ('preproc_image', None),
    ('preproc_occurrence', None),
    ('preproc_residual', None),
    ('preproc_rvec', None),
]
"""
Regen Command:
    cd /home/joncrall/code/wbia/wbia/algo/preproc
    makeinit.py --modname=wbia.algo.preproc --write
"""
