"""
Hotspotter pipeline module

Module Concepts::

    PREFIXES:
    qaid2_XXX - prefix mapping query chip index to
    qfx2_XXX  - prefix mapping query chip feature index to

    TUPLES::
     * nns    - a (qfx2_idx, qfx2_dist) tuple
     * nnfilt - a (qfx2_fs, qfx2_valid) tuple

    SCALARS::
     * idx    - the index into the nnindexers descriptors
     * dist   - the distance to a corresponding feature
     * fs     - a score of a corresponding feature
     * valid  - a valid bit for a corresponding feature

    REALIZATIONS::
    qaid2_nns - maping from query chip index to nns
    {
     * qfx2_idx   - ranked list of query feature indexes to database feature indexes
     * qfx2_dist - ranked list of query feature indexes to database feature indexes
    }

    * qaid2_norm_weight - mapping from qaid to (qfx2_normweight, qfx2_selnorm)
             = qaid2_nnfilt[qaid]
"""

from __future__ import absolute_import, division, print_function
# Python
from six.moves import zip, range
import six
from collections import defaultdict
import sys
# Scientific
import numpy as np
from vtool import keypoint as ktool
from vtool import spatial_verification as sver
# Hotspotter
from ibeis.model.hots import hots_query_result
from ibeis.model.hots import hstypes
#from ibeis.model.hots import coverage_image
from ibeis.model.hots import nn_weights
from ibeis.model.hots import voting_rules2 as vr2
from ibeis.model.hots import exceptions as hsexcept
import utool
import utool as ut
from functools import partial
#profile = utool.profile
print, print_,  printDBG, rrr, profile = utool.inject(__name__, '[hs]', DEBUG=False)


TAU = 2 * np.pi  # tauday.com
NOT_QUIET = utool.NOT_QUIET and not utool.get_argflag('--quiet-query')
VERB_PIPELINE = utool.get_argflag(('--verbose-pipeline', '--verb-pipe'))
VERYVERBOSE_PIPELINE = utool.get_argflag(('--very-verbose-pipeline', '--very-verb-pipe'))
VERBOSE = utool.VERBOSE or VERB_PIPELINE

#=================
# Globals
#=================

START_AFTER = 2


# specialized progress func
log_progress = partial(utool.log_progress, startafter=START_AFTER, disable=utool.QUIET)


# Query Level 0
#@profile
#@utool.indent_func('[Q0]')
@profile
def request_ibeis_query_L0(ibs, qreq_):
    r"""
    Driver logic of query pipeline

    Args:
        ibs   (IBEISController): IBEIS database object to be queried
        qreq_ (QueryRequest): hyper-parameters. use ``prep_qreq`` to create one

    Returns:
        (dict of QueryResult): qaid2_qres mapping from query indexes to Query Result Objects

    Example:
        >>> # VsMany:
        >>> # ENABLE_DOCTEST
        >>> import ibeis
        >>> import utool as ut
        >>> from ibeis.model.hots import pipeline
        >>> custom_qparams = dict(codename='vsmany')
        >>> ibs, qreq_ = pipeline.get_pipeline_testdata(custom_qparams=custom_qparams)
        >>> print(qreq_.qparams.query_cfgstr)
        >>> qaid2_qres = pipeline.request_ibeis_query_L0(ibs, qreq_)
        >>> qres = qaid2_qres[list(qaid2_qres.keys())[0]]
        >>> if ut.get_argflag('--show') or ut.inIPython():
        ...     qres.show_analysis(ibs, fnum=0, make_figtitle=True)
        >>> print(qres.get_inspect_str())

    Example:
        >>> # VsOne:
        >>> # ENABLE_DOCTEST
        >>> import ibeis
        >>> import utool as ut
        >>> from ibeis.model.hots import pipeline
        >>> # pipeline.rrr()
        >>> custom_qparams1 = dict(codename='vsone', sv_on=False)
        >>> ibs1, qreq_1 = pipeline.get_pipeline_testdata(custom_qparams=custom_qparams1)
        >>> print(qreq_1.qparams.query_cfgstr)
        >>> qaid2_qres1 = pipeline.request_ibeis_query_L0(ibs1, qreq_1)
        >>> qres1 = qaid2_qres1[list(qaid2_qres1.keys())[0]]
        >>> if ut.get_argflag('--show') or ut.inIPython():
        ...     qres1.show_analysis(ibs1, fnum=1, make_figtitle=True)
        >>> print(qres1.get_inspect_str())

    python ibeis/model/hots/pipeline.py --test-request_ibeis_query_L0

    """
    metadata = {}
    # Load data for nearest neighbors
    qreq_.lazy_load(ibs)
    # TODO incorporate metdata into qreq
    qreq_.metadata = metadata
    #

    if VERB_PIPELINE:
        print('\n\n[hs] +--- STARTING HOTSPOTTER PIPELINE ---')
        print('[hs] * len(internal_qaids) = %r' % len(qreq_.internal_qaids))
        print('[hs] * len(internal_daids) = %r' % len(qreq_.internal_daids))

    if qreq_.qparams.pipeline_root == 'smk':
        from ibeis.model.hots.smk import smk_match
        # Alternative to naive bayes matching:
        # Selective match kernel
        qaid2_scores, qaid2_chipmatch_FILT_ = smk_match.execute_smk_L5(qreq_)
    elif qreq_.qparams.pipeline_root in ['vsone', 'vsmany']:
        # Nearest neighbors (qaid2_nns)
        # * query descriptors assigned to database descriptors
        # * FLANN used here
        qaid2_nns_ = nearest_neighbors(qreq_, qreq_.metadata)

        # Nearest neighbors weighting and scoring (filt2_weights, metadata)
        # * feature matches are weighted
        filt2_weights_ = weight_neighbors(qaid2_nns_, qreq_, qreq_.metadata)
        #print(filt2_weights_)

        # Thresholding and weighting (qaid2_nnfilter)
        # * feature matches are pruned
        qaid2_nnfilt_ = filter_neighbors(qaid2_nns_, filt2_weights_, qreq_)

        # Nearest neighbors to chip matches (qaid2_chipmatch)
        # * Inverted index used to create aid2_fmfsfk (TODO: aid2_fmfv)
        # * Initial scoring occurs
        # * vsone inverse swapping occurs here
        qaid2_chipmatch_FILT_ = build_chipmatches(qaid2_nns_, qaid2_nnfilt_, qreq_)
    else:
        print('invalid pipeline root %r' % (qreq_.qparams.pipeline_root))

    # Spatial verification (qaid2_chipmatch) (TODO: cython)
    # * prunes chip results and feature matches
    qaid2_chipmatch_SVER_ = spatial_verification(qaid2_chipmatch_FILT_, qreq_)

    # Query results format (qaid2_qres)
    # * Final Scoring. Prunes chip results.
    # * packs into a wrapped query result object
    qaid2_qres_ = chipmatch_to_resdict(qaid2_chipmatch_SVER_, metadata, qreq_)

    if VERB_PIPELINE:
        print('[hs] L___ FINISHED HOTSPOTTER PIPELINE ___')

    return qaid2_qres_

#============================
# 1) Nearest Neighbors
#============================


#@ut.indent_func('[nn]')
@profile
def nearest_neighbors(qreq_, metadata):
    """
    Plain Nearest Neighbors

    Args:
        qreq_  (QueryRequest): hyper-parameters

    Returns:
        dict: qaid2_nnds - a dict mapping query annnotation-ids to a nearest
            neighbor tuple (indexes, dists). indexes and dist have the shape
            (nDesc x K) where nDesc is the number of descriptors in the
            annotation, and K is the number of approximate nearest neighbors.


    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots import pipeline
        >>> pipeline.rrr()
        >>> custom_qparams = dict(custom_qparams=dict(codename='vsone'))
        >>> ibs, qreq_ = pipeline.get_pipeline_testdata(custom_qparams=custom_qparams)
        >>> # Run Test
        >>> qaid2_nns = pipeline.nearest_neighbors(qreq_, qreq_.metadata)
        >>> # Asserts
        >>> assert list(qaid2_nns.keys()) == qreq_.get_external_qaids().tolist()
        >>> tup = list(qaid2_nns.values())[0]
        >>> assert tup[0].shape == tup[1].shape
    """
    # Neareset neighbor configuration
    K      = qreq_.qparams.K
    Knorm  = qreq_.qparams.Knorm
    checks = qreq_.qparams.checks
    if NOT_QUIET or VERB_PIPELINE:
        print('[hs] Step 1) Assign nearest neighbors: ' + qreq_.qparams.nn_cfgstr)
    num_neighbors = K + Knorm  # number of nearest neighbors
    qvecs_list = qreq_.get_internal_qvecs()  # query descriptors
    # Allocate numpy array for each query annotation
    # TODO: dtype=np.ndarray is just an object, might be useful to use
    # pointers?
    nQAnnots = len(qvecs_list)
    nn_idxs_arr   = np.empty(nQAnnots, dtype=np.ndarray)  # database indexes
    nn_dists_arr = np.empty(nQAnnots, dtype=np.ndarray)  # corresponding distance
    # Internal statistics reporting
    nTotalNN, nTotalDesc = 0, 0
    mark_, end_ = log_progress('Assign NN: ', len(qvecs_list))
    for count, qfx2_vec in enumerate(qvecs_list):
        mark_(count)  # progress
        # Check that we can query this annotation
        if len(qfx2_vec) == 0:
            # Assign empty nearest neighbors
            (qfx2_idx, qfx2_dist) = qreq_.indexer.empty_neighbors(num_neighbors)
        else:
            # Find Neareset Neighbors nntup = (indexes, dists)
            (qfx2_idx, qfx2_dist) = qreq_.indexer.knn(qfx2_vec, num_neighbors, checks)
            nTotalNN += qfx2_idx.size
            nTotalDesc += len(qfx2_vec)
        # record number of query and result desc
        nn_idxs_arr[count]   = qfx2_idx
        nn_dists_arr[count] = qfx2_dist
    end_()
    if NOT_QUIET or VERB_PIPELINE:
        print('[hs] * assigned %d desc (from %d annots) to %r nearest neighbors'
              % (nTotalDesc, nQAnnots, nTotalNN))
    #return nn_idxs_arr, nn_dists_arr
    # Return old style dicts for now
    qaids = qreq_.get_internal_qaids()
    qaid2_nns_ = {aid: (qfx2_idx, qfx2_dist) for (aid, qfx2_idx, qfx2_dist) in
                  zip(qaids, nn_idxs_arr, nn_dists_arr)}

    if qreq_.qparams.with_metadata:
        metadata['nns'] = qaid2_nns_
    return qaid2_nns_


#============================
# 2) Nearest Neighbor weights
#============================


#@ut.indent_func('[wn]')
def weight_neighbors(qaid2_nns, qreq_, metadata):
    """
    Args:
        qaid2_nns (dict):
        qreq_ (QueryRequest): hyper-parameters
        metadata (dict): metadata dictionary

    Returns:
        dict : filt2_weights

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots import pipeline
        >>> ibs, qreq_ = pipeline.get_pipeline_testdata()
        >>> # Run Test
        >>> qaid2_nns = pipeline.nearest_neighbors(qreq_, qreq_.metadata)
        >>> filt2_weights = weight_neighbors(qaid2_nns, qreq_, qreq_.metadata)
    """
    if NOT_QUIET:
        print('[hs] Step 2) Weight neighbors: ' + qreq_.qparams.filt_cfgstr)
    if not qreq_.qparams.filt_on:
        filt2_weights = {}
    else:
        filt2_weights = _weight_neighbors(qaid2_nns, qreq_, metadata)
    return filt2_weights


#@ut.indent_func('[_wn]')
@profile
def _weight_neighbors(qaid2_nns, qreq_, metadata):
    """
    Args:
        qaid2_nns (int): query annotation id
        qreq_ (QueryRequest): hyper-parameters
        metadata (dict): metadata dictionary

    Returns:
        dict : filt2_weights

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots.pipeline import *  # NOQA
        >>> from ibeis.model.hots import pipeline
        >>> from ibeis.model.hots import nn_weights
        >>> metadata = {}
        >>> custom_qparams = {'dupvote_weight': 1.0}
        >>> tup = nn_weights.testdata_nn_weights(custom_qparams=custom_qparams)
        >>> ibs, daid_list, qaid_list, qaid2_nns, qreq_  = tup
        >>> filt2_weights = pipeline._weight_neighbors(qaid2_nns, qreq_, metadata)
    """
    nnweight_list = qreq_.qparams.active_filter_list
    # Prealloc output
    filt2_weights = {nnweight: None for nnweight in nnweight_list}
    # Buidl output
    for nnweightkey in nnweight_list:
        nn_filter_fn = nn_weights.NN_WEIGHT_FUNC_DICT[nnweightkey]
        # Apply [nnweightkey] weight to each nearest neighbor
        # FIXME: only compute metadata if requested
        qaid2_norm_weight = nn_filter_fn(qaid2_nns, qreq_, metadata)
        filt2_weights[nnweightkey] = qaid2_norm_weight
    return filt2_weights


#==========================
# 3) Neighbor scoring (Voting Profiles)
#==========================


#@ut.indent_func('[_tsw]')
@profile
def _threshold_and_scale_weights(qaid, qfx2_nnidx, filt2_weights, qreq_):
    """
    helper function _threshold_and_scale_weights

    qfx2_score is an ndarray containing the score of individual feature matches.
    qfx2_valid marks if that score will be thresholded.

    Args:
        qaid (int): query annotation id
        qfx2_nnidx (dict):
        filt2_weights (dict):
        qreq_ (QueryRequest): hyper-parameters

    Return:
        tuple : (qfx2_score, qfx2_valid)

    Example:
        >>> from ibeis.model.hots.pipeline import *  # NOQA
    """
    # Baseline is all matches have score 1 and all matches are valid
    qfx2_score = np.ones(qfx2_nnidx.shape, dtype=hstypes.FS_DTYPE)
    qfx2_valid = np.ones(qfx2_nnidx.shape, dtype=np.bool)
    # Apply the filter weightings to determine feature validity and scores
    for filt, aid2_weights in six.iteritems(filt2_weights):
        qfx2_weights = aid2_weights[qaid]
        sign, thresh, weight = qreq_.qparams.filt2_stw[filt]  # stw = sign, thresh, weight
        if thresh is not None:
            # Filter if threshold is specified
            qfx2_trueweights = sign * qfx2_weights
            truethresh = sign * thresh
            qfx2_passed = qfx2_trueweights <= truethresh
            #if VERB_PIPELINE:
            #    print('[pipe.thresh] TEST(%r): (truethresh:%r) <= (qfx2_trueweights.min()=%r)' %
            #            (filt, truethresh, qfx2_trueweights.min()))
            #    print('[pipe.thresh] * %d matches passed' % (qfx2_passed.sum()))
            #    print('[pipe.thresh] * and %d matches are now valid' % (qfx2_valid.sum(),))
            qfx2_valid  = np.logical_and(qfx2_valid, qfx2_passed)
        if not weight == 0:
            # Score if weight is specified
            # This used to be an addition. should it still be?
            qfx2_score *= (weight * qfx2_weights)
    return qfx2_score, qfx2_valid


#@ut.indent_func('[fn]')
@profile
def filter_neighbors(qaid2_nns, filt2_weights, qreq_):
    """
    Args:
        qaid2_nns (dict):
        filt2_weights (dict):
        qreq_ (QueryRequest): hyper-parameters

    Returns:
        qaid2_nnfilt

    Example:
        >>> from ibeis.model.hots.pipeline import *  # NOQA
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots import pipeline
        >>> pipeline.rrr()
        >>> custom_qparams = dict(dupvote_weight=1.0)
        >>> custom_qparams = dict(codename='vsone')
        >>> ibs, qreq_ = pipeline.get_pipeline_testdata(custom_qparams=custom_qparams)
        >>> # Run Test
        >>> qaid2_nns     = pipeline.nearest_neighbors(qreq_, qreq_.metadata)
        >>> filt2_weights = pipeline.weight_neighbors(qaid2_nns, qreq_, qreq_.metadata)
        >>> qaid2_nnfilt  = pipeline.filter_neighbors(qaid2_nns, filt2_weights, qreq_)
    """
    qaid2_nnfilt = {}
    # Configs
    cant_match_sameimg  = not qreq_.qparams.can_match_sameimg
    cant_match_samename = not qreq_.qparams.can_match_samename
    cant_match_self     = not cant_match_sameimg
    K = qreq_.qparams.K
    if NOT_QUIET:
        print('[hs] Step 3) Filter neighbors: ')
    # Filter matches based on config and weights
    mark_, end_ = log_progress('Filter NN: ', len(qaid2_nns))
    for count, qaid in enumerate(six.iterkeys(qaid2_nns)):
        mark_(count)  # progress
        (qfx2_idx, _) = qaid2_nns[qaid]
        qfx2_nnidx = qfx2_idx.T[0:K].T
        # Get a numeric score score and valid flag for each feature match
        qfx2_score, qfx2_valid = _threshold_and_scale_weights(qaid, qfx2_nnidx, filt2_weights, qreq_)
        qfx2_aid = qreq_.indexer.get_nn_aids(qfx2_nnidx)
        if VERBOSE or VERB_PIPELINE:
            print('')
            print('[hs] * %d assignments are invalid by filter thresholds' %
                  ((True - qfx2_valid).sum()))
        if qreq_.qparams.gravity_weighting:
            raise NotImplementedError('have not finished gv weighting')
            #from vtool import linalg as ltool
            #qfx2_nnkpts = qreq_.indexer.get_nn_kpts(qfx2_nnidx)
            #qfx2_nnori = ktool.get_oris(qfx2_nnkpts)
            #qfx2_kpts  = qreq_.get_annot_kpts(qaid)  # FIXME: Highly inefficient
            #qfx2_oris  = ktool.get_oris(qfx2_kpts)
            ## Get the orientation distance
            #qfx2_oridist = ltool.rowwise_oridist(qfx2_nnori, qfx2_oris)
            ## Normalize into a weight (close orientations are 1, far are 0)
            #qfx2_gvweight = (TAU - qfx2_oridist) / TAU
            ## Apply gravity vector weight to the score
            #qfx2_score *= qfx2_gvweight
        # Remove Impossible Votes:
        # dont vote for yourself or another chip in the same image
        if cant_match_self:
            qfx2_notsamechip = qfx2_aid != qaid
            #<DBG>
            if VERYVERBOSE_PIPELINE:
                __self_verbose_check(qfx2_notsamechip, qfx2_valid)
            #</DBG>
            qfx2_valid = np.logical_and(qfx2_valid, qfx2_notsamechip)
        if cant_match_sameimg:
            qfx2_gid = qreq_.get_annot_gids(qfx2_aid)
            qgid     = qreq_.get_annot_gids(qaid)
            qfx2_notsameimg = qfx2_gid != qgid
            #<DBG>
            if VERYVERBOSE_PIPELINE:
                __sameimg_verbose_check(qfx2_notsameimg, qfx2_valid)
            #</DBG>
            qfx2_valid = np.logical_and(qfx2_valid, qfx2_notsameimg)
        if cant_match_samename:
            qfx2_nid = qreq_.get_annot_nids(qfx2_aid)
            qnid = qreq_.get_annot_nids(qaid)
            qfx2_notsamename = qfx2_nid != qnid
            #<DBG>
            if VERYVERBOSE_PIPELINE:
                __samename_verbose_check(qfx2_notsamename, qfx2_valid)
            #</DBG>
            qfx2_valid = np.logical_and(qfx2_valid, qfx2_notsamename)
        #printDBG('[hs] * Marking %d assignments as invalid' % ((True - qfx2_valid).sum()))
        qaid2_nnfilt[qaid] = (qfx2_score, qfx2_valid)
    end_()
    return qaid2_nnfilt


def __self_verbose_check(qfx2_notsamechip, qfx2_valid):
    nInvalidChips = ((True - qfx2_notsamechip)).sum()
    nNewInvalidChips = (qfx2_valid * (True - qfx2_notsamechip)).sum()
    total = qfx2_valid.size
    print('[hs] * self invalidates %d/%d assignments' % (nInvalidChips, total))
    print('[hs] * %d are newly invalided by self' % (nNewInvalidChips))


def __samename_verbose_check(qfx2_notsamename, qfx2_valid):
    nInvalidNames = ((True - qfx2_notsamename)).sum()
    nNewInvalidNames = (qfx2_valid * (True - qfx2_notsamename)).sum()
    total = qfx2_valid.size
    print('[hs] * nid invalidates %d/%d assignments' % (nInvalidNames, total))
    print('[hs] * %d are newly invalided by nid' % nNewInvalidNames)


def __sameimg_verbose_check(qfx2_notsameimg, qfx2_valid):
    nInvalidImgs = ((True - qfx2_notsameimg)).sum()
    nNewInvalidImgs = (qfx2_valid * (True - qfx2_notsameimg)).sum()
    total = qfx2_valid.size
    print('[hs] * gid invalidates %d/%d assignments' % (nInvalidImgs, total))
    print('[hs] * %d are newly invalided by gid' % nNewInvalidImgs)


def identity_filter(qaid2_nns, qreq_):
    """ testing function returns unfiltered nearest neighbors
    this does check that you are not matching yourself
    """
    K = qreq_.qparams.K
    qaid2_nnfilt = {}
    for count, qaid in enumerate(six.iterkeys(qaid2_nns)):
        (qfx2_idx, _) = qaid2_nns[qaid]
        qfx2_nnidx = qfx2_idx[:, 0:K]
        qfx2_score = np.ones(qfx2_nnidx.shape, dtype=hstypes.FS_DTYPE)
        qfx2_valid = np.ones(qfx2_nnidx.shape, dtype=np.bool)
        # Check that you are not matching yourself
        qfx2_aid = qreq_.indexer.get_nn_aids(qfx2_nnidx)
        qfx2_notsamechip = qfx2_aid != qaid
        qfx2_valid = np.logical_and(qfx2_valid, qfx2_notsamechip)
        qaid2_nnfilt[qaid] = (qfx2_score, qfx2_valid)
    return qaid2_nnfilt


#============================
# 4) Conversion from featurematches to chipmatches qfx2 -> aid2
#============================


@profile
def _fix_fmfsfk(aid2_fm, aid2_fs, aid2_fk):
    minMatches = 2  # TODO: paramaterize
    # Convert to numpy
    fm_dtype = hstypes.FM_DTYPE
    fs_dtype = hstypes.FS_DTYPE
    fk_dtype = hstypes.FK_DTYPE
    # FIXME: This is slow
    aid2_fm_ = {aid: np.array(fm, fm_dtype)
                for aid, fm in six.iteritems(aid2_fm)
                if len(fm) > minMatches}
    aid2_fs_ = {aid: np.array(fs, fs_dtype)
                for aid, fs in six.iteritems(aid2_fs)
                if len(fs) > minMatches}
    aid2_fk_ = {aid: np.array(fk, fk_dtype)
                for aid, fk in six.iteritems(aid2_fk)
                if len(fk) > minMatches}
    # Ensure shape
    for aid, fm in six.iteritems(aid2_fm_):
        fm.shape = (fm.size // 2, 2)
    chipmatch = (aid2_fm_, aid2_fs_, aid2_fk_)
    return chipmatch


def new_fmfsfk():
    aid2_fm = defaultdict(list)
    aid2_fs = defaultdict(list)
    aid2_fk = defaultdict(list)
    return aid2_fm, aid2_fs, aid2_fk


#@ut.indent_func('[bc]')
@profile
def build_chipmatches(qaid2_nns, qaid2_nnfilt, qreq_):
    """
    Args:
        qaid2_nns    : dict of assigned nearest features (only indexes are used here)
        qaid2_nnfilt : dict of (featmatch_scores, featmatch_mask)
                        where the scores and matches correspond to the assigned
                        nearest features
        qreq_(QueryRequest) : hyper-parameters

    Returns:
        qaid2_chipmatch : feat match, feat score, feat rank

    Notes:
        The prefix ``qaid2_`` denotes a mapping where keys are query-annotation-id

        vsmany/vsone counts here. also this is where the filter
        weights and thershold are applied to the matches. Essientally
        nearest neighbors are converted into weighted assignments

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots import pipeline
        >>> custom_qparams = dict(dupvote_weight=1.0)
        >>> custom_qparams = dict(codename='vsone')
        >>> ibs, qreq_ = pipeline.get_pipeline_testdata('NAUT_Dan', custom_qparams=custom_qparams)
        >>> # Run Test
        >>> qaid2_nns       = pipeline.nearest_neighbors(qreq_, qreq_.metadata)
        >>> filt2_weights   = pipeline.weight_neighbors(qaid2_nns, qreq_, qreq_.metadata)
        >>> qaid2_nnfilt    = pipeline.filter_neighbors(qaid2_nns, filt2_weights, qreq_)
        >>> qaid2_chipmatch = pipeline.build_chipmatches(qaid2_nns, qaid2_nnfilt, qreq_)
    """

    # Config
    K = qreq_.qparams.K
    is_vsone =  qreq_.qparams.vsone
    if NOT_QUIET:
        pipeline_root = qreq_.qparams.pipeline_root
        print('[hs] Step 4) Building chipmatches %s' % (pipeline_root,))
    # Return var
    qaid2_chipmatch = {}
    nFeatMatches = 0
    #Vsone
    if is_vsone:
        assert len(qreq_.get_external_qaids()) == 1
        assert len(qreq_.get_internal_daids()) == 1
        aid2_fm, aid2_fs, aid2_fk = new_fmfsfk()
    # Iterate over chips with nearest neighbors
    mark_, end_ = log_progress('Build Chipmatch: ', len(qaid2_nns))

    # Iterate over INTERNAL query annotation ids
    for count, qaid in enumerate(six.iterkeys(qaid2_nns)):
        mark_(count)  # Mark progress
        (qfx2_idx, _) = qaid2_nns[qaid]
        (qfx2_fs, qfx2_valid) = qaid2_nnfilt[qaid]
        nQKpts = qfx2_idx.shape[0]
        # Build feature matches
        qfx2_nnidx = qfx2_idx.T[0:K].T
        qfx2_aid  = qreq_.indexer.get_nn_aids(qfx2_nnidx)
        qfx2_fx   = qreq_.indexer.get_nn_featxs(qfx2_nnidx)
        # FIXME: Can probably get away without using tile here
        qfx2_qfx = np.tile(np.arange(nQKpts), (K, 1)).T
        qfx2_k   = np.tile(np.arange(K), (nQKpts, 1))
        # Pack valid feature matches into an interator
        valid_lists = (qfx2[qfx2_valid] for qfx2 in (qfx2_qfx, qfx2_aid, qfx2_fx, qfx2_fs, qfx2_k,))
        # TODO: Sorting the valid lists by aid might help the speed of this
        # code. Also, consolidating fm, fs, and fk into one vector will reduce
        # the amount of appends.
        match_iter = zip(*valid_lists)

        #+-----
        # Vsmany - Append query feature matches to database aids
        #+-----
        if not is_vsone:
            aid2_fm, aid2_fs, aid2_fk = new_fmfsfk()
            for qfx, aid, fx, fs, fk in match_iter:
                aid2_fm[aid].append((qfx, fx))  # Note the difference
                aid2_fs[aid].append(fs)
                aid2_fk[aid].append(fk)
                nFeatMatches += 1
            chipmatch = _fix_fmfsfk(aid2_fm, aid2_fs, aid2_fk)
            qaid2_chipmatch[qaid] = chipmatch
            #if not QUIET:
            #    nFeats_in_matches = [len(fm) for fm in six.itervalues(aid2_fm)]
            #    print('nFeats_in_matches_stats = ' +
            #          utool.dict_str(utool.get_stats(nFeats_in_matches)))
        #L_____

        #+-----
        # Vsone - Append database feature matches to query aids
        #+-----
        else:
            for qfx, aid, fx, fs, fk in match_iter:
                # Remember in vsone internal qaids = external daids
                aid2_fm[qaid].append((fx, qfx))  # Note the difference
                aid2_fs[qaid].append(fs)
                aid2_fk[qaid].append(fk)
                nFeatMatches += 1
        #L_____
    #Vsone
    if is_vsone:
        chipmatch = _fix_fmfsfk(aid2_fm, aid2_fs, aid2_fk)
        qaid = qreq_.get_external_qaids()[0]
        qaid2_chipmatch[qaid] = chipmatch
    end_()
    if NOT_QUIET:
        print('[hs] * made %d feat matches' % nFeatMatches)
    return qaid2_chipmatch


def assert_qaid2_chipmatch(ibs, qreq_, qaid2_chipmatch):
    """ Runs consistency check """
    external_qaids = qreq_.get_external_qaids().tolist()
    external_daids = qreq_.get_external_daids().tolist()

    if len(external_qaids) == 1 and qreq_.qparams.pipeline_root == 'vsone':
        nExternalQVecs = ibs.get_annot_vecs(external_qaids[0]).shape[0]
        assert qreq_.indexer.idx2_vec.shape[0] == nExternalQVecs, 'did not index query descriptors properly'

    assert external_qaids == list(qaid2_chipmatch.keys()), 'bad external qaids'
    # Loop over internal qaids
    for qaid, chipmatch in qaid2_chipmatch.iteritems():
        nQVecs = ibs.get_annot_vecs(qaid).shape[0]  # NOQA
        (daid2_fm, daid2_fs, daid2_fk) = chipmatch
        assert external_daids.tolist() == list(daid2_fm.keys())
        daid2_fm

        pass


#============================
# 5) Spatial Verification
#============================


#@ut.indent_func('[sv]')
def spatial_verification(qaid2_chipmatch, qreq_, dbginfo=False):
    """
    Args:
        qaid2_chipmatch (dict):
        qreq_ (QueryRequest): hyper-parameters
        dbginfo (bool):

    Returns:
        dict or tuple(dict, dict)

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots import pipeline
        >>> custom_qparams = dict(dupvote_weight=1.0, prescore_method='nsum', score_method='nsum')
        >>> ibs, qreq_ = pipeline.get_pipeline_testdata('PZ_MTEST', custom_qparams=custom_qparams)
        >>> # Run Test
        >>> qaid2_nns       = pipeline.nearest_neighbors(qreq_, qreq_.metadata)
        >>> filt2_weights   = pipeline.weight_neighbors(qaid2_nns, qreq_, qreq_.metadata)
        >>> qaid2_nnfilt    = pipeline.filter_neighbors(qaid2_nns, filt2_weights, qreq_)
        >>> qaid2_chipmatch = pipeline.build_chipmatches(qaid2_nns, qaid2_nnfilt, qreq_)
        >>> qaid2_chipmatch = pipeline.spatial_verification(qaid2_chipmatch, qreq_)
    """
    if not qreq_.qparams.sv_on or qreq_.qparams.xy_thresh is None:
        print('[hs] Step 5) Spatial verification: off')
        return (qaid2_chipmatch, {}) if dbginfo else qaid2_chipmatch
    else:
        return _spatial_verification(qaid2_chipmatch, qreq_, dbginfo=dbginfo)


#@ut.indent_func('[_sv]')
@profile
def _spatial_verification(qaid2_chipmatch, qreq_, dbginfo=False):
    """
    make only spatially valid features survive

    Dev:
        >>> import pyflann
        >>> qaid = 1
        >>> daid = ibs.get_annot_groundtruth(qaid)[0]
        >>> qvecs = ibs.get_annot_vecs(qaid)
        >>> dvecs = ibs.get_annot_vecs(daid)
        >>> # Simple ratio-test matching
        >>> flann = pyflann.FLANN()
        >>> flann.build_index(dvecs)
        >>> qfx2_dfx, qfx2_dist = flann.nn_index(qvecs, 2)
        >>> ratio = (qfx2_dist.T[1] / qfx2_dist.T[0])
        >>> valid = ratio < 1.2
        >>> valid_qfx = np.where(valid)[0]
        >>> valid_dfx = qfx2_dfx.T[0][valid]
        >>> fm = np.vstack((valid_qfx, valid_dfx)).T
        >>> fs = ratio[valid]
        >>> fk = np.ones(fs.size)
        >>> qaid2_chipmatch = {qaid: ({daid: fm}, {daid: fs}, {daid: fk})}
        >>> qreq_ = query_request.new_ibeis_query_request(ibs, [qaid], [daid])
        >>> qreq_.ibs = ibs
        >>> dbginfo = False

    Example:
        >>> # VSOne
        >>> from ibeis.model.hots.pipeline import *  # NOQA
        >>> from ibeis.model.hots import pipeline
        >>> import ibeis
        >>> custom_qparams = dict(codename='vsone')
        >>> ibs, qreq_ = pipeline.get_pipeline_testdata('NAUT_Dan', custom_qparams=custom_qparams, daid_list='all')
        >>> qaid2_nns       = pipeline.nearest_neighbors(qreq_, qreq_.metadata)
        >>> filt2_weights   = pipeline.weight_neighbors(qaid2_nns, qreq_, qreq_.metadata)
        >>> qaid2_nnfilt    = pipeline.filter_neighbors(qaid2_nns, filt2_weights, qreq_)
        >>> qaid2_chipmatch = pipeline.build_chipmatches(qaid2_nns, qaid2_nnfilt, qreq_)
        >>> qaid2_chipmatchSV = pipeline._spatial_verification(qaid2_chipmatch, qreq_)

    Example:
        >>> from ibeis.model.hots.pipeline import *  # NOQA
        >>> from ibeis.model.hots import pipeline
        >>> import ibeis
        >>> custom_qparams = dict(dupvote_weight=1.0, prescore_method='nsum', score_method='nsum')
        >>> ibs, qreq_ = pipeline.get_pipeline_testdata('PZ_MTEST', custom_qparams=custom_qparams, daid_list='all')
        >>> qaid2_nns       = pipeline.nearest_neighbors(qreq_, qreq_.metadata)
        >>> filt2_weights   = pipeline.weight_neighbors(qaid2_nns, qreq_, qreq_.metadata)
        >>> qaid2_nnfilt    = pipeline.filter_neighbors(qaid2_nns, filt2_weights, qreq_)
        >>> qaid2_chipmatch = pipeline.build_chipmatches(qaid2_nns, qaid2_nnfilt, qreq_)
        >>> qaid2_chipmatchSV = pipeline._spatial_verification(qaid2_chipmatch, qreq_)

    """
    # TODO: Make sure vsone isn't being messed up by some stupid assumption here
    # spatial verification
    print('[hs] Step 5) Spatial verification: ' + qreq_.qparams.sv_cfgstr)
    prescore_method = qreq_.qparams.prescore_method
    nShortlist      = qreq_.qparams.nShortlist
    xy_thresh       = qreq_.qparams.xy_thresh
    scale_thresh    = qreq_.qparams.scale_thresh
    ori_thresh      = qreq_.qparams.ori_thresh
    use_chip_extent = qreq_.qparams.use_chip_extent
    min_nInliers    = qreq_.qparams.min_nInliers
    qaid2_chipmatchSV = {}
    nFeatSVTotal = 0
    nFeatMatchSV = 0
    #nFeatMatchSVAff = 0
    if qreq_.qparams.with_metadata or dbginfo:
        qaid2_svtups = {}  # dbg info (can remove if there is a speed issue)
    def print_(msg, count=0):
        """ temp print_. Using count in this way is a hack """
        if NOT_QUIET:
            if count % 25 == 0:
                sys.stdout.write(msg)
            count += 1
    # Find a transform from chip2 to chip1 (the old way was 1 to 2)
    for qaid in six.iterkeys(qaid2_chipmatch):
        chipmatch = qaid2_chipmatch[qaid]
        daid2_prescore = score_chipmatch(qaid, chipmatch, prescore_method, qreq_)
        #print('Prescore: %r' % (daid2_prescore,))
        (daid2_fm, daid2_fs, daid2_fk) = chipmatch
        if prescore_method == 'nsum':
            daids_list = np.array(daid2_prescore.keys())
            dnids_list = np.array(qreq_.ibs.get_annot_nids(daids_list))
            prescore_arr = np.array(daid2_prescore.values())
            import vtool as vt
            unique_nids, groupxs = vt.group_indicies(dnids_list)
            grouped_prescores = vt.apply_grouping(prescore_arr, groupxs)
            dnid2_prescore = dict(zip(unique_nids, [arr.max() for arr in grouped_prescores]))
            # Ensure that you verify each member of the top shortlist names
            topx2_nid = utool.util_dict.keys_sorted_by_value(dnid2_prescore)[::-1]
            # Use shortlist of names instead of annots
            nNamesRerank = min(len(topx2_nid), nShortlist)
            topx2_aids = [daids_list[dnids_list == nid] for nid in topx2_nid[:nNamesRerank]]
            # override shortlist because we already selected a subset of names
            topx2_aid = utool.flatten(topx2_aids)
            nRerank = len(topx2_aid)
        else:
            topx2_aid = utool.util_dict.keys_sorted_by_value(daid2_prescore)[::-1]
            nRerank = min(len(topx2_aid), nShortlist)
        # Precompute output container
        if dbginfo or qreq_.qparams.with_metadata:
            daid2_svtup = {}  # dbg info (can remove if there is a speed issue)
        daid2_fm_V, daid2_fs_V, daid2_fk_V = new_fmfsfk()
        # Query Keypoints
        kpts1 = qreq_.get_annot_kpts(qaid)
        topx2_kpts = qreq_.get_annot_kpts(topx2_aid)
        # Check the diaglen sizes before doing the homography
        topx2_dlen_sqrd = precompute_topx2_dlen_sqrd(qreq_, daid2_fm, topx2_aid,
                                                      topx2_kpts, nRerank,
                                                      use_chip_extent)
        # spatially verify the top __NUM_RERANK__ results
        for topx in range(nRerank):
            daid = topx2_aid[topx]
            fm = daid2_fm[daid]
            if len(fm) == 0:
                print_('o')  # sv failure
                continue
            dlen_sqrd = topx2_dlen_sqrd[topx]
            kpts2 = topx2_kpts[topx]
            fs    = daid2_fs[daid]
            fk    = daid2_fk[daid]
            try:
                sv_tup = sver.spatial_verification(kpts1, kpts2, fm,
                                                   xy_thresh, scale_thresh, ori_thresh, dlen_sqrd,
                                                   min_nInliers, returnAff=dbginfo or qreq_.qparams.with_metadata)
            except Exception as ex:
                utool.printex(ex, 'Unknown error in spatial verification.',
                              keys=['kpts1', 'kpts2',  'fm', 'xy_thresh',
                                    'scale_thresh', 'dlen_sqrd', 'min_nInliers'])
                sv_tup = None
                #if utool.STRICT:
                #    print('Strict is on. Reraising')
                #    raise
            nFeatSVTotal += len(fm)
            if sv_tup is None:
                print_('o')  # sv failure
            else:
                # Return the inliers to the homography
                homog_inliers, H, aff_inliers, Aff = sv_tup
                if dbginfo or qreq_.qparams.with_metadata:
                    daid2_svtup[daid] = sv_tup
                daid2_fm_V[daid] = fm[homog_inliers, :]
                daid2_fs_V[daid] = fs[homog_inliers]
                daid2_fk_V[daid] = fk[homog_inliers]
                nFeatMatchSV += len(homog_inliers)
                #nFeatMatchSVAff += len(aff_inliers)
                if NOT_QUIET:
                    #print(inliers)
                    print_('.')  # verified something
        # Rebuild the feature match / score arrays to be consistent
        chipmatchSV = _fix_fmfsfk(daid2_fm_V, daid2_fs_V, daid2_fk_V)
        if dbginfo or qreq_.qparams.with_metadata:
            qaid2_svtups[qaid] = daid2_svtup
        qaid2_chipmatchSV[qaid] = chipmatchSV
    print_('\n')
    if NOT_QUIET:
        #print('[hs] * Affine verified %d/%d feat matches' % (nFeatMatchSVAff, nFeatSVTotal))
        print('[hs] * Homog  verified %d/%d feat matches' % (nFeatMatchSV, nFeatSVTotal))
    if dbginfo or qreq_.qparams.with_metadata:
        qreq_.metadata['qaid2_svtups'] = qaid2_svtups
    if dbginfo:
        return qaid2_chipmatchSV, qaid2_svtups
    else:
        return qaid2_chipmatchSV


#@ut.indent_func('[pdls]')
def precompute_topx2_dlen_sqrd(qreq_, aid2_fm, topx2_aid, topx2_kpts,
                                nRerank, use_chip_extent):
    """
    helper for spatial verification, computes the squared diagonal length of
    matching chips

    Args:
        qreq_ (QueryRequest): hyper-parameters
        aid2_fm (dict):
        topx2_aid (dict):
        topx2_kpts (dict):
        nRerank (int):
        use_chip_extent (bool):

    Returns:
        topx2_dlen_sqrd
    """
    if use_chip_extent:
        topx2_chipsize = list(qreq_.get_annot_chipsizes(topx2_aid))
        def chip_dlen_sqrd(tx):
            (chipw, chiph) = topx2_chipsize[tx]
            dlen_sqrd = chipw ** 2 + chiph ** 2
            return dlen_sqrd
        topx2_dlen_sqrd = [chip_dlen_sqrd(tx) for tx in range(nRerank)]
    else:
        # Use extent of matching keypoints
        def kpts_dlen_sqrd(tx):
            kpts2 = topx2_kpts[tx]
            aid = topx2_aid[tx]
            fm  = aid2_fm[aid]
            # This dosent make sense when len(fm) == 0
            if len(fm) == 0:
                return -1
            x_m, y_m = ktool.get_xys(kpts2[fm[:, 1]])
            dlensqrd = (x_m.max() - x_m.min()) ** 2 + (y_m.max() - y_m.min()) ** 2
            return dlensqrd
        topx2_dlen_sqrd = [kpts_dlen_sqrd(tx) for tx in range(nRerank)]
    return topx2_dlen_sqrd


#============================
# Scoring Mechanism
#============================

#@ut.indent_func('[scm]')
@profile
def score_chipmatch(qaid, chipmatch, score_method, qreq_):
    """
    Args:
        qaid (int): query annotation id
        chipmatch (tuple):
        score_method (str):
        qreq_ (QueryRequest): hyper-parameters

    Returns:
        daid2_score : scores for each database id w.r.t. a single query
    """
    (aid2_fm, aid2_fs, aid2_fk) = chipmatch
    # HACK: Im not even sure if the 'w' suffix is correctly handled anymore
    if score_method.find('w') == len(score_method) - 1:
        score_method = score_method[:-1]
    # Choose the appropriate scoring mechanism
    if score_method == 'csum':
        daid2_score = vr2.score_chipmatch_csum(chipmatch)
    elif score_method == 'nsum':
        daid2_score = vr2.score_chipmatch_nsum(chipmatch, qreq_)
    #elif score_method == 'pl':
    #    daid2_score, nid2_score = vr2.score_chipmatch_PL(qaid, chipmatch, qreq_)
    #elif score_method == 'borda':
    #    daid2_score, nid2_score = vr2.score_chipmatch_pos(qaid, chipmatch, qreq_, 'borda')
    #elif score_method == 'topk':
    #    daid2_score, nid2_score = vr2.score_chipmatch_pos(qaid, chipmatch, qreq_, 'topk')
    #elif score_method.startswith('coverage'):
    #    # Method num is at the end of coverage
    #    method = int(score_method.replace('coverage', '0'))
    #    daid2_score = coverage_image.score_chipmatch_coverage(qaid, chipmatch, qreq_, method=method)
    else:
        raise Exception('[hs] unknown scoring method:' + score_method)
    return daid2_score


#============================
# 6) Query Result Format
#============================


#@ut.indent_func('[ctr]')
@profile
def chipmatch_to_resdict(qaid2_chipmatch, metadata, qreq_,
                         qaid2_scores=None):
    """
    Args:
        qaid2_chipmatch (dict):
        metadata (dict):
        qreq_ (QueryRequest): hyper-parameters
        qaid2_scores (dict): optional

    Returns:
        qaid2_qres

    Examples:
        >>> from ibeis.model.hots.pipeline import *  # NOQA

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots import pipeline
        >>> custom_qparams = dict(dupvote_weight=1.0, prescore_method='nsum', score_method='nsum')
        >>> ibs, qreq_ = pipeline.get_pipeline_testdata('PZ_MTEST', custom_qparams=custom_qparams)
        >>> # Run Test
        >>> qaid2_nns       = pipeline.nearest_neighbors(qreq_, qreq_.metadata)
        >>> filt2_weights   = pipeline.weight_neighbors(qaid2_nns, qreq_, qreq_.metadata)
        >>> qaid2_nnfilt    = pipeline.filter_neighbors(qaid2_nns, filt2_weights, qreq_)
        >>> qaid2_chipmatch_FILT = pipeline.build_chipmatches(qaid2_nns, qaid2_nnfilt, qreq_)
        >>> qaid2_chipmatch_SVER = pipeline.spatial_verification(qaid2_chipmatch_FILT, qreq_)
        >>> qaid2_qres = pipeline.chipmatch_to_resdict(qaid2_chipmatch_SVER, qreq_.metadata, qreq_)
        >>> qres = qaid2_qres[1]

    """
    if NOT_QUIET:
        print('[hs] Step 6) Convert chipmatch -> qres')
    qaids   = qreq_.get_external_qaids()
    qauuids = qreq_.get_external_quuids()
    cfgstr = qreq_.get_cfgstr()
    score_method = qreq_.qparams.score_method
    # Create the result structures for each query.
    qaid2_qres = {}
    # Currently not looping over the keys so we have access to uuids
    # using qreq_ externals aids should be equivalent
    #for qaid in six.iterkeys(qaid2_chipmatch):
    for qaid, qauuid in zip(qaids, qauuids):
        # Create a query result structure
        qres = hots_query_result.QueryResult(qaid, qauuid, cfgstr)
        qaid2_qres[qaid] = qres

    for qaid, qres in six.iteritems(qaid2_qres):
        pass
        # For each query's chipmatch
        chipmatch = qaid2_chipmatch[qaid]
        if chipmatch is not None:
            try:
                aid2_fm, aid2_fs, aid2_fk = chipmatch
            except Exception as ex:
                utool.printex(ex, 'error converting chipmatch',
                              keys=['chipmatch'])
                raise
            qres.aid2_fm = aid2_fm
            qres.aid2_fs = aid2_fs
            qres.aid2_fk = aid2_fk

        # Perform final scoring
        if qaid2_scores is None:
            daid2_score = score_chipmatch(qaid, chipmatch, score_method, qreq_)
        else:
            daid2_score = qaid2_scores[qaid]
            if not isinstance(daid2_score, dict):
                # Pandas hack
                daid2_score = daid2_score.to_dict()
        # Populate query result fields
        qres.aid2_score = daid2_score  # FIXME fig qreq name

        qres.metadata = {}  # dbgstats
        with utool.EmbedOnException():
            for key, qaid2_meta in six.iteritems(metadata):
                qres.metadata[key] = qaid2_meta[qaid]  # things like k+1th
    # Retain original score method
    return qaid2_qres


#@ut.indent_func('[tlr]')
@profile
def try_load_resdict(qreq_, force_miss=False):
    """
    Args:
        qreq_ (QueryRequest): hyper-parameters
        force_miss (bool):

    Returns:
        tuple : (qaid2_qres_hit, cachemiss_qaids)

    Try and load the result structures for each query.
    returns a list of failed qaids
    """
    qaids   = qreq_.get_external_qaids()
    qauuids = qreq_.get_external_quuids()

    cfgstr = qreq_.get_cfgstr()
    qresdir = qreq_.get_qresdir()
    qaid2_qres_hit = {}
    cachemiss_qaids = []
    for qaid, qauuid in zip(qaids, qauuids):
        try:
            qres = hots_query_result.QueryResult(qaid, qauuid, cfgstr)
            qres.load(qresdir, force_miss=force_miss)  # 77.4 % time
            qaid2_qres_hit[qaid] = qres  # cache hit
        except (hsexcept.HotsCacheMissError, hsexcept.HotsNeedsRecomputeError):
            cachemiss_qaids.append(qaid)  # cache miss
    return qaid2_qres_hit, cachemiss_qaids


def save_resdict(qreq_, qaid2_qres):
    """
    Args:
        qreq_ (QueryRequest): hyper-parameters
        qaid2_qres (dict):

    Returns:
        None
    """
    qresdir = qreq_.get_qresdir()
    for qres in six.itervalues(qaid2_qres):
        qres.save(qresdir)


def get_pipeline_testdata(dbname=None, custom_qparams={}, qaid_list=None, daid_list=None):
    """
    >>> import ibeis
    >>> from ibeis.model.hots import pipeline
    >>> custom_qparams = custom_qparams=dict(pipeline_root='vsone', codename='vsone')
    >>> ibs, qreq_ = pipeline.get_pipeline_testdata(custom_qparams=custom_qparams)
    >>> print(qreq_.qparams.query_cfgstr)
    """
    import ibeis
    from ibeis.model.hots import query_request
    if dbname is None:
        dbname = ut.get_argval('--db', str, 'testdb1')
    ibs = ibeis.opendb(dbname)
    if qaid_list is None:
        qaid_list = [1]
    if daid_list is None:
        daid_list = ibs.get_valid_aids()
        daid_list = daid_list[0:min(5, len(daid_list))]
    elif daid_list == 'all':
        daid_list = ibs.get_valid_aids()
    ibs = ibeis.test_main(db=dbname)
    ibs.cfg.query_cfg.with_metadata = True
    qreq_ = query_request.new_ibeis_query_request(ibs, qaid_list, daid_list, custom_qparams)
    qreq_.lazy_load(ibs)
    # TODO incorporate metdata into qreq
    qreq_.metadata = {}
    return ibs, qreq_


if __name__ == '__main__':
    """
    python ibeis/model/hots/pipeline.py --verb-test
    python ibeis/model/hots/pipeline.py --test-build_chipmatches
    python ibeis/model/hots/pipeline.py --test-spatial-verification
    python ibeis/model/hots/pipeline.py --test-request_ibeis_query_L0 --show
    python ibeis/model/hots/pipeline.py --test-request_ibeis_query_L0 --show --subx 0
    python ibeis/model/hots/pipeline.py --test-request_ibeis_query_L0 --show --subx 1 --db NAUT_Dan
    python ibeis/model/hots/pipeline.py --test-request_ibeis_query_L0 --subx 1 --db NAUT_Dan --noindent
    python ibeis/model/hots/pipeline.py --allexamples
    """
    import multiprocessing
    multiprocessing.freeze_support()
    ut.doctest_funcs()
    if ut.get_argflag('--show'):
        from plottool import df2
        exec(df2.present())
