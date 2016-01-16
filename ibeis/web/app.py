# -*- coding: utf-8 -*-
"""
Dependencies: flask, tornado
"""
from __future__ import absolute_import, division, print_function
import random
from os.path import join, exists, splitext, basename
import uuid
import zipfile
import time
import six
import math
import tornado.wsgi
import tornado.httpserver
from flask import request, redirect, url_for, make_response, current_app
import logging
import socket
import simplejson as json
from ibeis.control import controller_inject
from ibeis import constants as const
from ibeis.constants import KEY_DEFAULTS, SPECIES_KEY, PI, TAU
from ibeis.web import appfuncs as ap
from ibeis.web import zmq_task_queue  # NOQA
import utool as ut


DEFAULT_WEB_API_PORT = ut.get_argval('--port', type_=int, default=5000)


register_api   = controller_inject.get_ibeis_flask_api(__name__)
register_route = controller_inject.get_ibeis_flask_route(__name__)


BROWSER = ut.get_argflag('--browser')
PAGE_SIZE = 500


################################################################################

def default_species(ibs):
    # hack function
    dbname = ibs.get_dbname()
    if dbname == 'CHTA_Master':
        default_species = 'cheetah'
    elif dbname == 'ELPH_Master':
        default_species = 'elephant_savanna'
    elif dbname == 'GIR_Master':
        default_species = 'giraffe_reticulated'
    elif dbname == 'GZ_Master':
        default_species = 'zebra_grevys'
    elif dbname == 'LION_Master':
        default_species = 'lion'
    elif dbname == 'PZ_Master':
        default_species = 'zebra_plains'
    elif dbname == 'WD_Master':
        default_species = 'wild_dog'
    elif dbname == 'NNP_MasterGIRM':
        default_species = 'giraffe_masai'
    elif 'NNP_' in dbname:
        default_species = 'zebra_plains'
    elif 'GZC' in dbname:
        default_species = 'zebra_plains'
    else:
        default_species = None
    print('[web] DEFAULT SPECIES: %r' % (default_species))
    return default_species


def imageset_image_processed(ibs, gid_list):
    images_reviewed = [ reviewed == 1 for reviewed in ibs.get_image_reviewed(gid_list) ]
    return images_reviewed


def imageset_annot_viewpoint_processed(ibs, aid_list):
    annots_reviewed = [ reviewed is not None for reviewed in ibs.get_annot_yaws(aid_list) ]
    return annots_reviewed


def imageset_annot_quality_processed(ibs, aid_list):
    annots_reviewed = [ reviewed is not None and reviewed is not -1 for reviewed in ibs.get_annot_qualities(aid_list) ]
    return annots_reviewed


def imageset_annot_additional_processed(ibs, aid_list, nid_list):
    sex_list = ibs.get_annot_sex(aid_list)
    age_list = ibs.get_annot_age_months_est(aid_list)
    annots_reviewed = [
        (nid < 0) or (nid > 0 and sex >= 0 and -1 not in list(age) and list(age).count(None) < 2)
        for nid, sex, age in zip(nid_list, sex_list, age_list)
    ]
    return annots_reviewed


def convert_old_viewpoint_to_yaw(view_angle):
    """ we initially had viewpoint coordinates inverted

    Example:
        >>> import math
        >>> TAU = 2 * math.pi
        >>> old_viewpoint_labels = [
        >>>     ('left'       ,   0, 0.000 * TAU,),
        >>>     ('frontleft'  ,  45, 0.125 * TAU,),
        >>>     ('front'      ,  90, 0.250 * TAU,),
        >>>     ('frontright' , 135, 0.375 * TAU,),
        >>>     ('right'      , 180, 0.500 * TAU,),
        >>>     ('backright'  , 225, 0.625 * TAU,),
        >>>     ('back'       , 270, 0.750 * TAU,),
        >>>     ('backleft'   , 315, 0.875 * TAU,),
        >>> ]
        >>> fmtstr = 'old %15r %.2f -> new %15r %.2f'
        >>> for lbl, angle, radians in old_viewpoint_labels:
        >>>     print(fmtstr % (lbl, angle, lbl, convert_old_viewpoint_to_yaw(angle)))
    """
    if view_angle is None:
        return None
    view_angle = ut.deg_to_rad(view_angle)
    yaw = (-view_angle + (TAU / 2)) % TAU
    return yaw


def convert_yaw_to_old_viewpoint(yaw):
    """ we initially had viewpoint coordinates inverted

    Example:
        >>> import math
        >>> TAU = 2 * math.pi
        >>> old_viewpoint_labels = [
        >>>     ('left'       ,   0, 0.000 * TAU,),
        >>>     ('frontleft'  ,  45, 0.125 * TAU,),
        >>>     ('front'      ,  90, 0.250 * TAU,),
        >>>     ('frontright' , 135, 0.375 * TAU,),
        >>>     ('right'      , 180, 0.500 * TAU,),
        >>>     ('backright'  , 225, 0.625 * TAU,),
        >>>     ('back'       , 270, 0.750 * TAU,),
        >>>     ('backleft'   , 315, 0.875 * TAU,),
        >>> ]
        >>> fmtstr = 'original_angle %15r %.2f -> yaw %15r %.2f -> reconstructed_angle %15r %.2f'
        >>> for lbl, angle, radians in old_viewpoint_labels:
        >>>     yaw = convert_old_viewpoint_to_yaw(angle)
        >>>     reconstructed_angle = convert_yaw_to_old_viewpoint(yaw)
        >>>     print(fmtstr % (lbl, angle, lbl, yaw, lbl, reconstructed_angle))
    """
    if yaw is None:
        return None
    view_angle = ((TAU / 2) - yaw) % TAU
    view_angle = ut.rad_to_deg(view_angle)
    return view_angle


################################################################################


@register_route('/')
def root():
    return ap.template(None)


@register_route('/view')
def view():
    def _date_list(gid_list):
        unixtime_list = ibs.get_image_unixtime(gid_list)
        datetime_list = [
            ut.unixtime_to_datetimestr(unixtime)
            if unixtime is not None else
            'UNKNOWN'
            for unixtime in unixtime_list
        ]
        datetime_split_list = [ datetime.split(' ') for datetime in datetime_list ]
        date_list = [ datetime_split[0] if len(datetime_split) == 2 else 'UNKNOWN' for datetime_split in datetime_split_list ]
        return date_list

    ibs = current_app.ibs
    aid_list = ibs.filter_aids_count()
    gid_list = ibs.get_annot_gids(aid_list)
    nid_list = ibs.get_annot_name_rowids(aid_list)
    date_list = _date_list(gid_list)

    gid_list_unique = list(set(gid_list))
    date_list_unique = _date_list(gid_list_unique)
    date_taken_dict = {}
    for gid, date in zip(gid_list_unique, date_list_unique):
        if date not in date_taken_dict:
            date_taken_dict[date] = [0, 0]
        date_taken_dict[date][1] += 1

    gid_list_all = ibs.get_valid_gids()
    date_list_all = _date_list(gid_list_all)
    for gid, date in zip(gid_list_all, date_list_all):
        if date in date_taken_dict:
            date_taken_dict[date][0] += 1

    value = 0
    label_list = []
    value_list = []
    index_list = []
    seen_set = set()
    current_seen_set = set()
    previous_seen_set = set()
    last_date = None
    date_seen_dict = {}
    for index, (aid, nid, date) in enumerate(zip(aid_list, nid_list, date_list)):
        index_list.append(index + 1)
        # Add to counters
        if date not in date_seen_dict:
            date_seen_dict[date] = [0, 0, 0, 0]

        date_seen_dict[date][0] += 1

        if nid not in current_seen_set:
            current_seen_set.add(nid)
            date_seen_dict[date][1] += 1
            if nid in previous_seen_set:
                date_seen_dict[date][3] += 1

        if nid not in seen_set:
            seen_set.add(nid)
            value += 1
            date_seen_dict[date][2] += 1

        # Add to register
        value_list.append(value)
        # Reset step (per day)
        if date != last_date and date != 'UNKNOWN':
            last_date = date
            previous_seen_set = set(current_seen_set)
            current_seen_set = set()
            label_list.append(date)
        else:
            label_list.append('')

    # def optimization1(x, a, b, c):
    #     return a * np.log(b * x) + c

    # def optimization2(x, a, b, c):
    #     return a * np.sqrt(x) ** b + c

    # def optimization3(x, a, b, c):
    #     return 1.0 / (a * np.exp(-b * x) + c)

    # def process(func, opts, domain, zero_index, zero_value):
    #     values = func(domain, *opts)
    #     diff = values[zero_index] - zero_value
    #     values -= diff
    #     values[ values < 0.0 ] = 0.0
    #     values[:zero_index] = 0.0
    #     values = values.astype(int)
    #     return list(values)

    # optimization_funcs = [
    #     optimization1,
    #     optimization2,
    #     optimization3,
    # ]
    # # Get data
    # x = np.array(index_list)
    # y = np.array(value_list)
    # # Fit curves
    # end    = int(len(index_list) * 1.25)
    # domain = np.array(range(1, end))
    # zero_index = len(value_list) - 1
    # zero_value = value_list[zero_index]
    # regressed_opts = [ curve_fit(func, x, y)[0] for func in optimization_funcs ]
    # prediction_list = [
    #     process(func, opts, domain, zero_index, zero_value)
    #     for func, opts in zip(optimization_funcs, regressed_opts)
    # ]
    # index_list = list(domain)
    prediction_list = []

    date_seen_dict.pop('UNKNOWN', None)
    bar_label_list = sorted(date_seen_dict.keys())
    bar_value_list1 = [ date_taken_dict[date][0] for date in bar_label_list ]
    bar_value_list2 = [ date_taken_dict[date][1] for date in bar_label_list ]
    bar_value_list3 = [ date_seen_dict[date][0] for date in bar_label_list ]
    bar_value_list4 = [ date_seen_dict[date][1] for date in bar_label_list ]
    bar_value_list5 = [ date_seen_dict[date][2] for date in bar_label_list ]
    bar_value_list6 = [ date_seen_dict[date][3] for date in bar_label_list ]

    # label_list += ['Models'] + [''] * (len(index_list) - len(label_list) - 1)
    # value_list += [0] * (len(index_list) - len(value_list))

    # Counts
    imgsetid_list = ibs.get_valid_imgsetids()
    gid_list = ibs.get_valid_gids()
    aid_list = ibs.get_valid_aids()
    nid_list = ibs.get_valid_nids()
    contrib_list = ibs.get_valid_contrib_rowids()
    # nid_list = ibs.get_valid_nids()
    aid_list_count = ibs.filter_aids_count()
    # gid_list_count = list(set(ibs.get_annot_gids(aid_list_count)))
    nid_list_count_dup = ibs.get_annot_name_rowids(aid_list_count)
    nid_list_count = list(set(nid_list_count_dup))

    # Calculate the Petersen-Lincoln index form the last two days
    try:
        c1 = bar_value_list4[-2]
        c2 = bar_value_list4[-1]
        c3 = bar_value_list6[-1]
        pl_index = int(math.ceil( (c1 * c2) / c3 ))
        pl_error_num = float(c1 * c1 * c2 * (c2 - c3))
        pl_error_dom = float(c3 ** 3)
        pl_error = int(math.ceil( 1.96 * math.sqrt(pl_error_num / pl_error_dom) ))
    except IndexError:
        # pl_index = 'Undefined - Zero recaptured (k = 0)'
        pl_index = 0
        pl_error = 0
    except ZeroDivisionError:
        # pl_index = 'Undefined - Zero recaptured (k = 0)'
        pl_index = 0
        pl_error = 0

    # Get the markers
    gid_list_markers = ibs.get_annot_gids(aid_list_count)
    gps_list_markers = map(list, ibs.get_image_gps(gid_list_markers))
    gps_list_markers_all = map(list, ibs.get_image_gps(gid_list))

    REMOVE_DUP_CODE = True
    if not REMOVE_DUP_CODE:
        # Get the tracks
        nid_track_dict = ut.ddict(list)
        for nid, gps in zip(nid_list_count_dup, gps_list_markers):
            if gps[0] == -1.0 and gps[1] == -1.0:
                continue
            nid_track_dict[nid].append(gps)
        gps_list_tracks = [ nid_track_dict[nid] for nid in sorted(nid_track_dict.keys()) ]
    else:
        __nid_list, gps_track_list, aid_track_list = ibs.get_name_gps_tracks(aid_list=aid_list_count)
        gps_list_tracks = list(map(lambda x: list(map(list, x)), gps_track_list))

    valid_aids = ibs.get_valid_aids()
    valid_gids = ibs.get_valid_gids()
    valid_aids_ = ibs.filter_aids_custom(valid_aids)
    valid_gids_ = ibs.filter_gids_custom(valid_gids)
    used_gids = list(set( ibs.get_annot_gids(valid_aids) ))
    used_contrib_tags = list(set( ibs.get_image_contributor_tag(used_gids) ))

    # Get Age and sex (By Annot)
    # annot_sex_list = ibs.get_annot_sex(valid_aids_)
    # annot_age_months_est_min = ibs.get_annot_age_months_est_min(valid_aids_)
    # annot_age_months_est_max = ibs.get_annot_age_months_est_max(valid_aids_)
    # age_list = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    # for sex, min_age, max_age in zip(annot_sex_list, annot_age_months_est_min, annot_age_months_est_max):
    #     if sex not in [0, 1]:
    #         sex = 2
    #         # continue
    #     if (min_age is None or min_age < 12) and max_age < 12:
    #         age_list[sex][0] += 1
    #     elif 12 <= min_age and min_age < 36 and 12 <= max_age and max_age < 36:
    #         age_list[sex][1] += 1
    #     elif 36 <= min_age and (36 <= max_age or max_age is None):
    #         age_list[sex][2] += 1

    # Get Age and sex (By Name)
    name_sex_list = ibs.get_name_sex(nid_list_count)
    name_age_months_est_mins_list = ibs.get_name_age_months_est_min(nid_list_count)
    name_age_months_est_maxs_list = ibs.get_name_age_months_est_max(nid_list_count)
    age_list = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    age_unreviewed = 0
    age_ambiguous = 0
    for nid, sex, min_ages, max_ages in zip(nid_list_count, name_sex_list, name_age_months_est_mins_list, name_age_months_est_maxs_list):
        if len(set(min_ages)) > 1 or len(set(max_ages)) > 1:
            # print('[web] Invalid name %r: Cannot have more than one age' % (nid, ))
            age_ambiguous += 1
            continue
        min_age = None
        max_age = None
        if len(min_ages) > 0:
            min_age = min_ages[0]
        if len(max_ages) > 0:
            max_age = max_ages[0]
        # Histogram
        if (min_age is None and max_age is None) or (min_age is -1 and max_age is -1):
            # print('[web] Unreviewded name %r: Specify the age for the name' % (nid, ))
            age_unreviewed += 1
            continue
        if sex not in [0, 1]:
            sex = 2
            # continue
        if (min_age is None or min_age < 12) and max_age < 12:
            age_list[sex][0] += 1
        elif 12 <= min_age and min_age < 36 and 12 <= max_age and max_age < 36:
            age_list[sex][1] += 1
        elif 36 <= min_age and (36 <= max_age or max_age is None):
            age_list[sex][2] += 1

    dbinfo_str = dbinfo()

    return ap.template('view',
                       line_index_list=index_list,
                       line_label_list=label_list,
                       line_value_list=value_list,
                       prediction_list=prediction_list,
                       pl_index=pl_index,
                       pl_error=pl_error,
                       gps_list_markers=gps_list_markers,
                       gps_list_markers_all=gps_list_markers_all,
                       gps_list_tracks=gps_list_tracks,
                       bar_label_list=bar_label_list,
                       bar_value_list1=bar_value_list1,
                       bar_value_list2=bar_value_list2,
                       bar_value_list3=bar_value_list3,
                       bar_value_list4=bar_value_list4,
                       bar_value_list5=bar_value_list5,
                       bar_value_list6=bar_value_list6,
                       age_list=age_list,
                       age_ambiguous=age_ambiguous,
                       age_unreviewed=age_unreviewed,
                       dbinfo_str=dbinfo_str,
                       imgsetid_list=imgsetid_list,
                       imgsetid_list_str=','.join(map(str, imgsetid_list)),
                       num_imgsetids=len(imgsetid_list),
                       gid_list=gid_list,
                       gid_list_str=','.join(map(str, gid_list)),
                       num_gids=len(gid_list),
                       contrib_list=contrib_list,
                       contrib_list_str=','.join(map(str, contrib_list)),
                       num_contribs=len(contrib_list),
                       gid_list_count=valid_gids_,
                       gid_list_count_str=','.join(map(str, valid_gids_)),
                       num_gids_count=len(valid_gids_),
                       aid_list=aid_list,
                       aid_list_str=','.join(map(str, aid_list)),
                       num_aids=len(aid_list),
                       aid_list_count=valid_aids_,
                       aid_list_count_str=','.join(map(str, valid_aids_)),
                       num_aids_count=len(valid_aids_),
                       nid_list=nid_list,
                       nid_list_str=','.join(map(str, nid_list)),
                       num_nids=len(nid_list),
                       nid_list_count=nid_list_count,
                       nid_list_count_str=','.join(map(str, nid_list_count)),
                       num_nids_count=len(nid_list_count),
                       used_gids=used_gids,
                       num_used_gids=len(used_gids),
                       used_contribs=used_contrib_tags,
                       num_used_contribs=len(used_contrib_tags))


@register_route('/view/imagesets')
def view_imagesets():
    ibs = current_app.ibs
    filtered = True
    imgsetid = request.args.get('imgsetid', '')
    if len(imgsetid) > 0:
        imgsetid_list = imgsetid.strip().split(',')
        imgsetid_list = [ None if imgsetid_ == 'None' or imgsetid_ == '' else int(imgsetid_) for imgsetid_ in imgsetid_list ]
    else:
        imgsetid_list = ibs.get_valid_imgsetids()
        filtered = False
    start_time_posix_list = ibs.get_imageset_start_time_posix(imgsetid_list)
    datetime_list = [
        ut.unixtime_to_datetimestr(start_time_posix)
        if start_time_posix is not None else
        'Unknown'
        for start_time_posix in start_time_posix_list
    ]
    gids_list = [ ibs.get_valid_gids(imgsetid=imgsetid_) for imgsetid_ in imgsetid_list ]
    aids_list = [ ut.flatten(ibs.get_image_aids(gid_list)) for gid_list in gids_list ]
    images_reviewed_list           = [ imageset_image_processed(ibs, gid_list) for gid_list in gids_list ]
    annots_reviewed_viewpoint_list = [ imageset_annot_viewpoint_processed(ibs, aid_list) for aid_list in aids_list ]
    annots_reviewed_quality_list   = [ imageset_annot_quality_processed(ibs, aid_list) for aid_list in aids_list ]
    image_processed_list           = [ images_reviewed.count(True) for images_reviewed in images_reviewed_list ]
    annot_processed_viewpoint_list = [ annots_reviewed.count(True) for annots_reviewed in annots_reviewed_viewpoint_list ]
    annot_processed_quality_list   = [ annots_reviewed.count(True) for annots_reviewed in annots_reviewed_quality_list ]
    reviewed_list = [ all(images_reviewed) and all(annots_reviewed_viewpoint) and all(annot_processed_quality) for images_reviewed, annots_reviewed_viewpoint, annot_processed_quality in zip(images_reviewed_list, annots_reviewed_viewpoint_list, annots_reviewed_quality_list) ]
    imageset_list = zip(
        imgsetid_list,
        ibs.get_imageset_text(imgsetid_list),
        ibs.get_imageset_num_gids(imgsetid_list),
        image_processed_list,
        ibs.get_imageset_num_aids(imgsetid_list),
        annot_processed_viewpoint_list,
        annot_processed_quality_list,
        start_time_posix_list,
        datetime_list,
        reviewed_list,
    )
    imageset_list.sort(key=lambda t: t[7])
    return ap.template('view', 'imagesets',
                       filtered=filtered,
                       imgsetid_list=imgsetid_list,
                       imgsetid_list_str=','.join(map(str, imgsetid_list)),
                       num_imgsetids=len(imgsetid_list),
                       imageset_list=imageset_list,
                       num_imagesets=len(imageset_list))


@register_route('/view/images')
def view_images():
    ibs = current_app.ibs
    filtered = True
    imgsetid_list = []
    gid = request.args.get('gid', '')
    imgsetid = request.args.get('imgsetid', '')
    page = max(0, int(request.args.get('page', 1)))
    if len(gid) > 0:
        gid_list = gid.strip().split(',')
        gid_list = [ None if gid_ == 'None' or gid_ == '' else int(gid_) for gid_ in gid_list ]
    elif len(imgsetid) > 0:
        imgsetid_list = imgsetid.strip().split(',')
        imgsetid_list = [ None if imgsetid_ == 'None' or imgsetid_ == '' else int(imgsetid_) for imgsetid_ in imgsetid_list ]
        gid_list = ut.flatten([ ibs.get_valid_gids(imgsetid=imgsetid) for imgsetid_ in imgsetid_list ])
    else:
        gid_list = ibs.get_valid_gids()
        filtered = False
    # Page
    page_start = min(len(gid_list), (page - 1) * PAGE_SIZE)
    page_end   = min(len(gid_list), page * PAGE_SIZE)
    page_total = int(math.ceil(len(gid_list) / PAGE_SIZE))
    page_previous = None if page_start == 0 else page - 1
    page_next = None if page_end == len(gid_list) else page + 1
    gid_list = gid_list[page_start:page_end]
    print('[web] Loading Page [ %d -> %d ] (%d), Prev: %s, Next: %s' % (page_start, page_end, len(gid_list), page_previous, page_next, ))
    image_unixtime_list = ibs.get_image_unixtime(gid_list)
    datetime_list = [
        ut.unixtime_to_datetimestr(image_unixtime)
        if image_unixtime is not None
        else
        'Unknown'
        for image_unixtime in image_unixtime_list
    ]
    image_list = zip(
        gid_list,
        [ ','.join(map(str, imgsetid_list_)) for imgsetid_list_ in ibs.get_image_imgsetids(gid_list) ],
        ibs.get_image_gnames(gid_list),
        image_unixtime_list,
        datetime_list,
        ibs.get_image_gps(gid_list),
        ibs.get_image_party_tag(gid_list),
        ibs.get_image_contributor_tag(gid_list),
        ibs.get_image_notes(gid_list),
        imageset_image_processed(ibs, gid_list),
    )
    image_list.sort(key=lambda t: t[3])
    return ap.template('view', 'images',
                       filtered=filtered,
                       imgsetid_list=imgsetid_list,
                       imgsetid_list_str=','.join(map(str, imgsetid_list)),
                       num_imgsetids=len(imgsetid_list),
                       gid_list=gid_list,
                       gid_list_str=','.join(map(str, gid_list)),
                       num_gids=len(gid_list),
                       image_list=image_list,
                       num_images=len(image_list),
                       page=page,
                       page_start=page_start,
                       page_end=page_end,
                       page_total=page_total,
                       page_previous=page_previous,
                       page_next=page_next)


@register_route('/view/annotations')
def view_annotations():
    ibs = current_app.ibs
    filtered = True
    imgsetid_list = []
    gid_list = []
    aid = request.args.get('aid', '')
    gid = request.args.get('gid', '')
    imgsetid = request.args.get('imgsetid', '')
    page = max(0, int(request.args.get('page', 1)))
    if len(aid) > 0:
        aid_list = aid.strip().split(',')
        aid_list = [ None if aid_ == 'None' or aid_ == '' else int(aid_) for aid_ in aid_list ]
    elif len(gid) > 0:
        gid_list = gid.strip().split(',')
        gid_list = [ None if gid_ == 'None' or gid_ == '' else int(gid_) for gid_ in gid_list ]
        aid_list = ut.flatten(ibs.get_image_aids(gid_list))
    elif len(imgsetid) > 0:
        imgsetid_list = imgsetid.strip().split(',')
        imgsetid_list = [ None if imgsetid_ == 'None' or imgsetid_ == '' else int(imgsetid_) for imgsetid_ in imgsetid_list ]
        gid_list = ut.flatten([ ibs.get_valid_gids(imgsetid=imgsetid_) for imgsetid_ in imgsetid_list ])
        aid_list = ut.flatten(ibs.get_image_aids(gid_list))
    else:
        aid_list = ibs.get_valid_aids()
        filtered = False
    # Page
    page_start = min(len(aid_list), (page - 1) * PAGE_SIZE)
    page_end   = min(len(aid_list), page * PAGE_SIZE)
    page_total = int(math.ceil(len(aid_list) / PAGE_SIZE))
    page_previous = None if page_start == 0 else page - 1
    page_next = None if page_end == len(aid_list) else page + 1
    aid_list = aid_list[page_start:page_end]
    print('[web] Loading Page [ %d -> %d ] (%d), Prev: %s, Next: %s' % (page_start, page_end, len(aid_list), page_previous, page_next, ))
    annotation_list = zip(
        aid_list,
        ibs.get_annot_gids(aid_list),
        [ ','.join(map(str, imgsetid_list_)) for imgsetid_list_ in ibs.get_annot_imgsetids(aid_list) ],
        ibs.get_annot_image_names(aid_list),
        ibs.get_annot_names(aid_list),
        ibs.get_annot_exemplar_flags(aid_list),
        ibs.get_annot_species_texts(aid_list),
        ibs.get_annot_yaw_texts(aid_list),
        ibs.get_annot_quality_texts(aid_list),
        ibs.get_annot_sex_texts(aid_list),
        ibs.get_annot_age_months_est(aid_list),
        [ reviewed_viewpoint and reviewed_quality for reviewed_viewpoint, reviewed_quality in zip(imageset_annot_viewpoint_processed(ibs, aid_list), imageset_annot_quality_processed(ibs, aid_list)) ],
    )
    annotation_list.sort(key=lambda t: t[0])
    return ap.template('view', 'annotations',
                       filtered=filtered,
                       imgsetid_list=imgsetid_list,
                       imgsetid_list_str=','.join(map(str, imgsetid_list)),
                       num_imgsetids=len(imgsetid_list),
                       gid_list=gid_list,
                       gid_list_str=','.join(map(str, gid_list)),
                       num_gids=len(gid_list),
                       aid_list=aid_list,
                       aid_list_str=','.join(map(str, aid_list)),
                       num_aids=len(aid_list),
                       annotation_list=annotation_list,
                       num_annotations=len(annotation_list),
                       page=page,
                       page_start=page_start,
                       page_end=page_end,
                       page_total=page_total,
                       page_previous=page_previous,
                       page_next=page_next)


@register_route('/view/names')
def view_names():
    ibs = current_app.ibs
    filtered = True
    aid_list = []
    imgsetid_list = []
    gid_list = []
    nid = request.args.get('nid', '')
    aid = request.args.get('aid', '')
    gid = request.args.get('gid', '')
    imgsetid = request.args.get('imgsetid', '')
    page = max(0, int(request.args.get('page', 1)))
    if len(nid) > 0:
        nid_list = nid.strip().split(',')
        nid_list = [ None if nid_ == 'None' or nid_ == '' else int(nid_) for nid_ in nid_list ]
    if len(aid) > 0:
        aid_list = aid.strip().split(',')
        aid_list = [ None if aid_ == 'None' or aid_ == '' else int(aid_) for aid_ in aid_list ]
        nid_list = ibs.get_annot_name_rowids(aid_list)
    elif len(gid) > 0:
        gid_list = gid.strip().split(',')
        gid_list = [ None if gid_ == 'None' or gid_ == '' else int(gid_) for gid_ in gid_list ]
        aid_list = ut.flatten(ibs.get_image_aids(gid_list))
        nid_list = ibs.get_annot_name_rowids(aid_list)
    elif len(imgsetid) > 0:
        imgsetid_list = imgsetid.strip().split(',')
        imgsetid_list = [ None if imgsetid_ == 'None' or imgsetid_ == '' else int(imgsetid_) for imgsetid_ in imgsetid_list ]
        gid_list = ut.flatten([ ibs.get_valid_gids(imgsetid=imgsetid_) for imgsetid_ in imgsetid_list ])
        aid_list = ut.flatten(ibs.get_image_aids(gid_list))
        nid_list = ibs.get_annot_name_rowids(aid_list)
    else:
        nid_list = ibs.get_valid_nids()
        filtered = False
    # Page
    PAGE_SIZE_ = int(PAGE_SIZE / 5)
    page_start = min(len(nid_list), (page - 1) * PAGE_SIZE_)
    page_end   = min(len(nid_list), page * PAGE_SIZE_)
    page_total = int(math.ceil(len(nid_list) / PAGE_SIZE_))
    page_previous = None if page_start == 0 else page - 1
    page_next = None if page_end == len(nid_list) else page + 1
    nid_list = nid_list[page_start:page_end]
    print('[web] Loading Page [ %d -> %d ] (%d), Prev: %s, Next: %s' % (page_start, page_end, len(nid_list), page_previous, page_next, ))
    aids_list = ibs.get_name_aids(nid_list)
    annotations_list = [ zip(
        aid_list_,
        ibs.get_annot_gids(aid_list_),
        [ ','.join(map(str, imgsetid_list_)) for imgsetid_list_ in ibs.get_annot_imgsetids(aid_list_) ],
        ibs.get_annot_image_names(aid_list_),
        ibs.get_annot_names(aid_list_),
        ibs.get_annot_exemplar_flags(aid_list_),
        ibs.get_annot_species_texts(aid_list_),
        ibs.get_annot_yaw_texts(aid_list_),
        ibs.get_annot_quality_texts(aid_list_),
        ibs.get_annot_sex_texts(aid_list_),
        ibs.get_annot_age_months_est(aid_list_),
        [ reviewed_viewpoint and reviewed_quality for reviewed_viewpoint, reviewed_quality in zip(imageset_annot_viewpoint_processed(ibs, aid_list_), imageset_annot_quality_processed(ibs, aid_list_)) ],
    ) for aid_list_ in aids_list ]
    name_list = zip(
        nid_list,
        annotations_list
    )
    name_list.sort(key=lambda t: t[0])
    return ap.template('view', 'names',
                       filtered=filtered,
                       imgsetid_list=imgsetid_list,
                       imgsetid_list_str=','.join(map(str, imgsetid_list)),
                       num_imgsetids=len(imgsetid_list),
                       gid_list=gid_list,
                       gid_list_str=','.join(map(str, gid_list)),
                       num_gids=len(gid_list),
                       aid_list=aid_list,
                       aid_list_str=','.join(map(str, aid_list)),
                       num_aids=len(aid_list),
                       nid_list=nid_list,
                       nid_list_str=','.join(map(str, nid_list)),
                       num_nids=len(nid_list),
                       name_list=name_list,
                       num_names=len(name_list),
                       page=page,
                       page_start=page_start,
                       page_end=page_end,
                       page_total=page_total,
                       page_previous=page_previous,
                       page_next=page_next)


@register_route('/turk')
def turk():
    imgsetid = request.args.get('imgsetid', '')
    imgsetid = None if imgsetid == 'None' or imgsetid == '' else int(imgsetid)
    return ap.template('turk', None, imgsetid=imgsetid)


@register_route('/turk/detection')
def turk_detection():
    ibs = current_app.ibs
    refer_aid = request.args.get('refer_aid', None)
    imgsetid = request.args.get('imgsetid', '')
    imgsetid = None if imgsetid == 'None' or imgsetid == '' else int(imgsetid)

    gid_list = ibs.get_valid_gids(imgsetid=imgsetid)
    reviewed_list = imageset_image_processed(ibs, gid_list)
    progress = '%0.2f' % (100.0 * reviewed_list.count(True) / len(gid_list), )

    imagesettext = None if imgsetid is None else ibs.get_imageset_text(imgsetid)
    gid = request.args.get('gid', '')
    if len(gid) > 0:
        gid = int(gid)
    else:
        gid_list_ = ut.filterfalse_items(gid_list, reviewed_list)
        if len(gid_list_) == 0:
            gid = None
        else:
            # gid = gid_list_[0]
            gid = random.choice(gid_list_)
    previous = request.args.get('previous', None)
    finished = gid is None
    review = 'review' in request.args.keys()
    display_instructions = request.cookies.get('detection_instructions_seen', 1) == 0
    display_species_examples = False  # request.cookies.get('detection_example_species_seen', 0) == 0
    if not finished:
        gpath = ibs.get_image_thumbpath(gid, ensure_paths=True, draw_annots=False)
        image = ap.open_oriented_image(gpath)
        image_src = ap.embed_image_html(image, filter_width=False)
        # Get annotations
        width, height = ibs.get_image_sizes(gid)
        scale_factor = float(ap.TARGET_WIDTH) / float(width)
        aid_list = ibs.get_image_aids(gid)
        annot_bbox_list = ibs.get_annot_bboxes(aid_list)
        annot_thetas_list = ibs.get_annot_thetas(aid_list)
        species_list = ibs.get_annot_species_texts(aid_list)
        # Get annotation bounding boxes
        annotation_list = []
        for aid, annot_bbox, annot_theta, species in zip(aid_list, annot_bbox_list, annot_thetas_list, species_list):
            temp = {}
            temp['left']   = int(scale_factor * annot_bbox[0])
            temp['top']    = int(scale_factor * annot_bbox[1])
            temp['width']  = int(scale_factor * (annot_bbox[2]))
            temp['height'] = int(scale_factor * (annot_bbox[3]))
            temp['label']  = species
            temp['id']     = aid
            temp['angle']  = float(annot_theta)
            annotation_list.append(temp)
        if len(species_list) > 0:
            species = max(set(species_list), key=species_list.count)  # Get most common species
        elif default_species(ibs) is not None:
            species = default_species(ibs)
        else:
            species = KEY_DEFAULTS[SPECIES_KEY]
    else:
        gpath = None
        species = None
        image_src = None
        annotation_list = []
    return ap.template('turk', 'detection',
                       imgsetid=imgsetid,
                       gid=gid,
                       refer_aid=refer_aid,
                       species=species,
                       image_path=gpath,
                       image_src=image_src,
                       previous=previous,
                       imagesettext=imagesettext,
                       progress=progress,
                       finished=finished,
                       annotation_list=annotation_list,
                       display_instructions=display_instructions,
                       display_species_examples=display_species_examples,
                       review=review)


def get_turk_annot_args(is_reviewed_func):
    """
    Helper to return aids in an imageset or a group review
    """
    ibs = current_app.ibs
    def _ensureid(_id):
        return None if _id == 'None' or _id == '' else int(_id)

    imgsetid = request.args.get('imgsetid', '')
    src_ag = request.args.get('src_ag', '')
    dst_ag = request.args.get('dst_ag', '')

    imgsetid = _ensureid(imgsetid)
    src_ag = _ensureid(src_ag)
    dst_ag = _ensureid(dst_ag)

    group_review_flag = src_ag is not None and dst_ag is not None
    if not group_review_flag:
        gid_list = ibs.get_valid_gids(imgsetid=imgsetid)
        aid_list = ut.flatten(ibs.get_image_aids(gid_list))
        reviewed_list = is_reviewed_func(ibs, aid_list)
    else:
        src_gar_rowid_list = ibs.get_annotgroup_gar_rowids(src_ag)
        dst_gar_rowid_list = ibs.get_annotgroup_gar_rowids(dst_ag)
        src_aid_list = ibs.get_gar_aid(src_gar_rowid_list)
        dst_aid_list = ibs.get_gar_aid(dst_gar_rowid_list)
        aid_list = src_aid_list
        reviewed_list = [ src_aid in dst_aid_list for src_aid in src_aid_list ]

    try:
        progress = '%0.2f' % (100.0 * reviewed_list.count(True) / len(aid_list), )
    except ZeroDivisionError:
        progress = '0.00'
    aid = request.args.get('aid', '')
    if len(aid) > 0:
        aid = int(aid)
    else:
        aid_list_ = ut.filterfalse_items(aid_list, reviewed_list)
        if len(aid_list_) == 0:
            aid = None
        else:
            if group_review_flag:
                aid = aid_list_[0]
            else:
                aid = random.choice(aid_list_)

    previous = request.args.get('previous', None)

    print('aid = %r' % (aid,))
    #print(ut.dict_str(ibs.get_annot_info(aid)))
    print(ut.obj_str(ibs.get_annot_info(aid, default=True, nl=True)))
    return aid_list, reviewed_list, imgsetid, src_ag, dst_ag, progress, aid, previous


@register_route('/turk/viewpoint')
def turk_viewpoint():
    """
    CommandLine:
        python -m ibeis.web.app --exec-turk_viewpoint --db PZ_Master1

    Example:
        >>> # SCRIPT
        >>> from ibeis.ibsfuncs import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb(defaultdb='PZ_Master1')
        >>> aid_list_ = ibs.find_unlabeled_name_members(suspect_yaws=True)
        >>> aid_list = ibs.filter_aids_to_quality(aid_list_, 'good', unknown_ok=False)
        >>> ibs.start_web_annot_groupreview(aid_list)
    """
    ibs = current_app.ibs
    tup = get_turk_annot_args(imageset_annot_viewpoint_processed)
    (aid_list, reviewed_list, imgsetid, src_ag, dst_ag, progress, aid, previous) = tup

    value = convert_yaw_to_old_viewpoint(ibs.get_annot_yaws(aid))
    review = 'review' in request.args.keys()
    finished = aid is None
    display_instructions = request.cookies.get('viewpoint_instructions_seen', 1) == 0
    if not finished:
        gid       = ibs.get_annot_gids(aid)
        gpath     = ibs.get_annot_chip_fpath(aid)
        image     = ap.open_oriented_image(gpath)
        image_src = ap.embed_image_html(image)
    else:
        gid       = None
        gpath     = None
        image_src = None

    imagesettext = ibs.get_imageset_text(imgsetid)
    return ap.template('turk', 'viewpoint',
                       imgsetid=imgsetid,
                       src_ag=src_ag,
                       dst_ag=dst_ag,
                       gid=gid,
                       aid=aid,
                       value=value,
                       image_path=gpath,
                       image_src=image_src,
                       previous=previous,
                       imagesettext=imagesettext,
                       progress=progress,
                       finished=finished,
                       display_instructions=display_instructions,
                       review=review)


@register_route('/turk/quality')
def turk_quality():
    """
    PZ Needs Tags:
        17242
        14468
        14427
        15946
        14771
        14084
        4102
        6074
        3409

    GZ Needs Tags;
    1302

    CommandLine:
        python -m ibeis.web.app --exec-turk_quality --db PZ_Master1
        python -m ibeis.web.app --exec-turk_quality --db GZ_Master1
        python -m ibeis.web.app --exec-turk_quality --db GIRM_Master1

    Example:
        >>> # SCRIPT
        >>> from ibeis.ibsfuncs import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb(defaultdb='testdb1')
        >>> aid_list_ = ibs.find_unlabeled_name_members(qual=True)
        >>> valid_views = ['primary', 'primary1', 'primary-1']
        >>> aid_list = ibs.filter_aids_to_viewpoint(aid_list_, valid_views, unknown_ok=False)
        >>> ibs.start_web_annot_groupreview(aid_list)
    """
    ibs = current_app.ibs
    tup = get_turk_annot_args(imageset_annot_quality_processed)
    (aid_list, reviewed_list, imgsetid, src_ag, dst_ag, progress, aid, previous) = tup

    value = ibs.get_annot_qualities(aid)
    if value == -1:
        value = None
    if value == 0:
        value = 1
    review = 'review' in request.args.keys()
    finished = aid is None
    display_instructions = request.cookies.get('quality_instructions_seen', 1) == 0
    if not finished:
        gid       = ibs.get_annot_gids(aid)
        gpath     = ibs.get_annot_chip_fpath(aid)
        image     = ap.open_oriented_image(gpath)
        image_src = ap.embed_image_html(image)
    else:
        gid       = None
        gpath     = None
        image_src = None
    imagesettext = ibs.get_imageset_text(imgsetid)
    return ap.template('turk', 'quality',
                       imgsetid=imgsetid,
                       src_ag=src_ag,
                       dst_ag=dst_ag,
                       gid=gid,
                       aid=aid,
                       value=value,
                       image_path=gpath,
                       image_src=image_src,
                       previous=previous,
                       imagesettext=imagesettext,
                       progress=progress,
                       finished=finished,
                       display_instructions=display_instructions,
                       review=review)


##@register_route('/turk/viewpoint')
#def old_turk_viewpoint():
#    #ibs = current_app.ibs
#    #imgsetid = request.args.get('imgsetid', '')
#    #imgsetid = None if imgsetid == 'None' or imgsetid == '' else int(imgsetid)
#    #imagesettext = None if imgsetid is None else ibs.get_imageset_text(imgsetid)
#    #src_ag = request.args.get('src_ag', '')
#    #src_ag = None if src_ag == 'None' or src_ag == '' else int(src_ag)
#    #dst_ag = request.args.get('dst_ag', '')
#    #dst_ag = None if dst_ag == 'None' or dst_ag == '' else int(dst_ag)

#    #group_review_flag = src_ag is not None and dst_ag is not None
#    #if not group_review_flag:
#    #    gid_list = ibs.get_valid_gids(imgsetid=imgsetid)
#    #    aid_list = ut.flatten(ibs.get_image_aids(gid_list))
#    #    reviewed_list = imageset_annot_viewpoint_processed(ibs, aid_list)
#    #else:
#    #    src_gar_rowid_list = ibs.get_annotgroup_gar_rowids(src_ag)
#    #    dst_gar_rowid_list = ibs.get_annotgroup_gar_rowids(dst_ag)
#    #    src_aid_list = ibs.get_gar_aid(src_gar_rowid_list)
#    #    dst_aid_list = ibs.get_gar_aid(dst_gar_rowid_list)
#    #    aid_list = src_aid_list
#    #    reviewed_list = [ src_aid in dst_aid_list for src_aid in src_aid_list ]
#    #previous = request.args.get('previous', None)
#    ibs = current_app.ibs
#    tup = get_turk_annot_args(imageset_annot_viewpoint_processed)
#    (aid_list, reviewed_list, imgsetid, src_ag, dst_ag, progress, aid, previous) = tup

#    value = convert_yaw_to_old_viewpoint(ibs.get_annot_yaws(aid))
#    review = 'review' in request.args.keys()
#    finished = aid is None
#    display_instructions = request.cookies.get('viewpoint_instructions_seen', 1) == 0
#    if not finished:
#        gid       = ibs.get_annot_gids(aid)
#        gpath     = ibs.get_annot_chip_fpath(aid)
#        image     = ap.open_oriented_image(gpath)
#        image_src = ap.embed_image_html(image)
#    else:
#        gid       = None
#        gpath     = None
#        image_src = None
#    imagesettext = ibs.get_imageset_text(imgsetid)
#    return ap.template('turk', 'viewpoint',
#                       imgsetid=imgsetid,
#                       src_ag=src_ag,
#                       dst_ag=dst_ag,
#                       gid=gid,
#                       aid=aid,
#                       value=value,
#                       image_path=gpath,
#                       image_src=image_src,
#                       previous=previous,
#                       imagesettext=imagesettext,
#                       progress=progress,
#                       finished=finished,
#                       display_instructions=display_instructions,
#                       review=review)


#@register_route('/turk/quality')
#def old_turk_quality():
#    #ibs = current_app.ibs
#    #imgsetid = request.args.get('imgsetid', '')
#    #imgsetid = None if imgsetid == 'None' or imgsetid == '' else int(imgsetid)

#    #gid_list = ibs.get_valid_gids(imgsetid=imgsetid)
#    #aid_list = ut.flatten(ibs.get_image_aids(gid_list))
#    #reviewed_list = imageset_annot_quality_processed(ibs, aid_list)
#    #try:
#    #    progress = '%0.2f' % (100.0 * reviewed_list.count(True) / len(aid_list), )
#    #except ZeroDivisionError:
#    #    progress = '0.00'

#    #aid = request.args.get('aid', '')
#    #if len(aid) > 0:
#    #    aid = int(aid)
#    #else:
#    #    aid_list_ = ut.filterfalse_items(aid_list, reviewed_list)
#    #    if len(aid_list_) == 0:
#    #        aid = None
#    #    else:
#    #        # aid = aid_list_[0]
#    #        aid = random.choice(aid_list_)
#    #previous = request.args.get('previous', None)

#    ibs = current_app.ibs
#    tup = get_turk_annot_args(imageset_annot_quality_processed)
#    (aid_list, reviewed_list, imgsetid, src_ag, dst_ag, progress, aid, previous) = tup

#    value = ibs.get_annot_qualities(aid)
#    if value == -1:
#        value = None
#    if value == 0:
#        value = 1
#    review = 'review' in request.args.keys()
#    finished = aid is None
#    display_instructions = request.cookies.get('quality_instructions_seen', 1) == 0
#    if not finished:
#        gid       = ibs.get_annot_gids(aid)
#        gpath     = ibs.get_annot_chip_fpath(aid)
#        image     = ap.open_oriented_image(gpath)
#        image_src = ap.embed_image_html(image)
#    else:
#        gid       = None
#        gpath     = None
#        image_src = None
#    imagesettext = ibs.get_imageset_text(imgsetid)
#    return ap.template('turk', 'quality',
#                       imgsetid=imgsetid,
#                       src_ag=src_ag,
#                       dst_ag=dst_ag,
#                       gid=gid,
#                       aid=aid,
#                       value=value,
#                       image_path=gpath,
#                       image_src=image_src,
#                       previous=previous,
#                       imagesettext=imagesettext,
#                       progress=progress,
#                       finished=finished,
#                       display_instructions=display_instructions,
#                       review=review)


@register_route('/turk/additional')
def turk_additional():
    ibs = current_app.ibs
    imgsetid = request.args.get('imgsetid', '')
    imgsetid = None if imgsetid == 'None' or imgsetid == '' else int(imgsetid)

    gid_list = ibs.get_valid_gids(imgsetid=imgsetid)
    aid_list = ut.flatten(ibs.get_image_aids(gid_list))
    nid_list = ibs.get_annot_nids(aid_list)
    reviewed_list = imageset_annot_additional_processed(ibs, aid_list, nid_list)
    try:
        progress = '%0.2f' % (100.0 * reviewed_list.count(True) / len(aid_list), )
    except ZeroDivisionError:
        progress = '0.00'

    imagesettext = None if imgsetid is None else ibs.get_imageset_text(imgsetid)
    aid = request.args.get('aid', '')
    if len(aid) > 0:
        aid = int(aid)
    else:
        aid_list_ = ut.filterfalse_items(aid_list, reviewed_list)
        if len(aid_list_) == 0:
            aid = None
        else:
            # aid = aid_list_[0]
            aid = random.choice(aid_list_)
    previous = request.args.get('previous', None)
    value_sex = ibs.get_annot_sex([aid])[0]
    if value_sex >= 0:
        value_sex += 2
    else:
        value_sex = None
    value_age_min, value_age_max = ibs.get_annot_age_months_est([aid])[0]
    value_age = None
    if (value_age_min is -1 or value_age_min is None) and (value_age_max is -1 or value_age_max is None):
        value_age = 1
    if (value_age_min is 0 or value_age_min is None) and value_age_max == 2:
        value_age = 2
    elif value_age_min is 3 and value_age_max == 5:
        value_age = 3
    elif value_age_min is 6 and value_age_max == 11:
        value_age = 4
    elif value_age_min is 12 and value_age_max == 23:
        value_age = 5
    elif value_age_min is 24 and value_age_max == 35:
        value_age = 6
    elif value_age_min is 36 and (value_age_max > 36 or value_age_max is None):
        value_age = 7

    review = 'review' in request.args.keys()
    finished = aid is None
    display_instructions = request.cookies.get('additional_instructions_seen', 1) == 0
    if not finished:
        gid       = ibs.get_annot_gids(aid)
        gpath     = ibs.get_annot_chip_fpath(aid)
        image     = ap.open_oriented_image(gpath)
        image_src = ap.embed_image_html(image)
    else:
        gid       = None
        gpath     = None
        image_src = None
    name_aid_list = None
    nid = ibs.get_annot_name_rowids(aid)
    if nid is not None:
        name_aid_list = ibs.get_name_aids(nid)
        quality_list = ibs.get_annot_qualities(name_aid_list)
        quality_text_list = ibs.get_annot_quality_texts(name_aid_list)
        yaw_text_list = ibs.get_annot_yaw_texts(name_aid_list)
        name_aid_combined_list = list(zip(
            name_aid_list,
            quality_list,
            quality_text_list,
            yaw_text_list,
        ))

        name_aid_combined_list.sort(key=lambda t: t[1], reverse=True)
    return ap.template('turk', 'additional',
                       imgsetid=imgsetid,
                       gid=gid,
                       aid=aid,
                       value_sex=value_sex,
                       value_age=value_age,
                       image_path=gpath,
                       name_aid_combined_list=name_aid_combined_list,
                       image_src=image_src,
                       previous=previous,
                       imagesettext=imagesettext,
                       progress=progress,
                       finished=finished,
                       display_instructions=display_instructions,
                       review=review)


@register_route('/submit/detection', methods=['POST'])
def submit_detection():
    ibs = current_app.ibs
    method = request.form.get('detection-submit', '')
    imgsetid = request.args.get('imgsetid', '')
    imgsetid = None if imgsetid == 'None' or imgsetid == '' else int(imgsetid)
    gid = int(request.form['detection-gid'])
    turk_id = request.cookies.get('turk_id', -1)

    if method.lower() == 'delete':
        # ibs.delete_images(gid)
        # print('[web] (DELETED) turk_id: %s, gid: %d' % (turk_id, gid, ))
        pass
    elif method.lower() == 'clear':
        aid_list = ibs.get_image_aids(gid)
        ibs.delete_annots(aid_list)
        print('[web] (CLEAERED) turk_id: %s, gid: %d' % (turk_id, gid, ))
        redirection = request.referrer
        if 'gid' not in redirection:
            # Prevent multiple clears
            if '?' in redirection:
                redirection = '%s&gid=%d' % (redirection, gid, )
            else:
                redirection = '%s?gid=%d' % (redirection, gid, )
        return redirect(redirection)
    else:
        current_aid_list = ibs.get_image_aids(gid)
        # Make new annotations
        width, height = ibs.get_image_sizes(gid)
        scale_factor = float(width) / float(ap.TARGET_WIDTH)
        # Get aids
        annotation_list = json.loads(request.form['detection-annotations'])
        bbox_list = [
            (
                int(scale_factor * annot['left']),
                int(scale_factor * annot['top']),
                int(scale_factor * annot['width']),
                int(scale_factor * annot['height']),
            )
            for annot in annotation_list
        ]
        theta_list = [
            float(annot['angle'])
            for annot in annotation_list
        ]
        survived_aid_list = [
            None if annot['id'] is None else int(annot['id'])
            for annot in annotation_list
        ]
        species_list = [
            annot['label']
            for annot in annotation_list
        ]
        # Delete annotations that didn't survive
        kill_aid_list = list(set(current_aid_list) - set(survived_aid_list))
        ibs.delete_annots(kill_aid_list)
        for aid, bbox, theta, species in zip(survived_aid_list, bbox_list, theta_list, species_list):
            if aid is None:
                ibs.add_annots([gid], [bbox], theta_list=[theta], species_list=[species])
            else:
                ibs.set_annot_bboxes([aid], [bbox])
                ibs.set_annot_thetas([aid], [theta])
                ibs.set_annot_species([aid], [species])
        ibs.set_image_reviewed([gid], [1])
        print('[web] turk_id: %s, gid: %d, bbox_list: %r, species_list: %r' % (turk_id, gid, annotation_list, species_list))
    # Return HTML
    refer = request.args.get('refer', '')
    if len(refer) > 0:
        return redirect(ap.decode_refer_url(refer))
    else:
        return redirect(url_for('turk_detection', imgsetid=imgsetid, previous=gid))


def movegroup_aid(ibs, aid, src_ag, dst_ag):
    gar_rowid_list = ibs.get_annot_gar_rowids(aid)
    annotgroup_rowid_list = ibs.get_gar_annotgroup_rowid(gar_rowid_list)
    src_index = annotgroup_rowid_list.index(src_ag)
    src_gar_rowid = gar_rowid_list[src_index]
    vals = (aid, src_ag, src_gar_rowid, dst_ag)
    print('Moving aid: %s from src_ag: %s (%s) to dst_ag: %s' % vals)
    # ibs.delete_gar([src_gar_rowid])
    ibs.add_gar([dst_ag], [aid])


@register_route('/submit/viewpoint', methods=['POST'])
def submit_viewpoint():
    ibs = current_app.ibs
    method = request.form.get('viewpoint-submit', '')
    imgsetid = request.args.get('imgsetid', '')
    imgsetid = None if imgsetid == 'None' or imgsetid == '' else int(imgsetid)

    src_ag = request.args.get('src_ag', '')
    src_ag = None if src_ag == 'None' or src_ag == '' else int(src_ag)
    dst_ag = request.args.get('dst_ag', '')
    dst_ag = None if dst_ag == 'None' or dst_ag == '' else int(dst_ag)

    aid = int(request.form['viewpoint-aid'])
    turk_id = request.cookies.get('turk_id', -1)
    if method.lower() == 'delete':
        ibs.delete_annots(aid)
        print('[web] (DELETED) turk_id: %s, aid: %d' % (turk_id, aid, ))
        aid = None  # Reset AID to prevent previous
    if method.lower() == 'make junk':
        ibs.set_annot_quality_texts([aid], [const.QUAL_JUNK])
        print('[web] (SET AS JUNK) turk_id: %s, aid: %d' % (turk_id, aid, ))
        redirection = request.referrer
        if 'aid' not in redirection:
            # Prevent multiple clears
            if '?' in redirection:
                redirection = '%s&aid=%d' % (redirection, aid, )
            else:
                redirection = '%s?aid=%d' % (redirection, aid, )
        return redirect(redirection)
    if method.lower() == 'rotate left':
        theta = ibs.get_annot_thetas(aid)
        theta = (theta + PI / 2) % TAU
        ibs.set_annot_thetas(aid, theta)
        (xtl, ytl, w, h) = ibs.get_annot_bboxes(aid)
        diffx = int(round((w / 2.0) - (h / 2.0)))
        diffy = int(round((h / 2.0) - (w / 2.0)))
        xtl, ytl, w, h = xtl + diffx, ytl + diffy, h, w
        ibs.set_annot_bboxes([aid], [(xtl, ytl, w, h)])
        print('[web] (ROTATED LEFT) turk_id: %s, aid: %d' % (turk_id, aid, ))
        redirection = request.referrer
        if 'aid' not in redirection:
            # Prevent multiple clears
            if '?' in redirection:
                redirection = '%s&aid=%d' % (redirection, aid, )
            else:
                redirection = '%s?aid=%d' % (redirection, aid, )
        return redirect(redirection)
    if method.lower() == 'rotate right':
        theta = ibs.get_annot_thetas(aid)
        theta = (theta - PI / 2) % TAU
        ibs.set_annot_thetas(aid, theta)
        (xtl, ytl, w, h) = ibs.get_annot_bboxes(aid)
        diffx = int(round((w / 2.0) - (h / 2.0)))
        diffy = int(round((h / 2.0) - (w / 2.0)))
        xtl, ytl, w, h = xtl + diffx, ytl + diffy, h, w
        ibs.set_annot_bboxes([aid], [(xtl, ytl, w, h)])
        print('[web] (ROTATED RIGHT) turk_id: %s, aid: %d' % (turk_id, aid, ))
        redirection = request.referrer
        if 'aid' not in redirection:
            # Prevent multiple clears
            if '?' in redirection:
                redirection = '%s&aid=%d' % (redirection, aid, )
            else:
                redirection = '%s?aid=%d' % (redirection, aid, )
        return redirect(redirection)
    else:
        if src_ag is not None and dst_ag is not None:
            movegroup_aid(ibs, aid, src_ag, dst_ag)
        value = int(request.form['viewpoint-value'])
        yaw = convert_old_viewpoint_to_yaw(value)
        ibs.set_annot_yaws([aid], [yaw], input_is_degrees=False)
        print('[web] turk_id: %s, aid: %d, yaw: %d' % (turk_id, aid, yaw))
    # Return HTML
    refer = request.args.get('refer', '')
    if len(refer) > 0:
        return redirect(ap.decode_refer_url(refer))
    else:
        return redirect(url_for('turk_viewpoint', imgsetid=imgsetid, src_ag=src_ag,
                                dst_ag=dst_ag, previous=aid))


@register_route('/submit/quality', methods=['POST'])
def submit_quality():
    ibs = current_app.ibs
    method = request.form.get('quality-submit', '')
    imgsetid = request.args.get('imgsetid', '')
    imgsetid = None if imgsetid == 'None' or imgsetid == '' else int(imgsetid)
    aid = int(request.form['quality-aid'])
    turk_id = request.cookies.get('turk_id', -1)

    src_ag = request.args.get('src_ag', '')
    src_ag = None if src_ag == 'None' or src_ag == '' else int(src_ag)
    dst_ag = request.args.get('dst_ag', '')
    dst_ag = None if dst_ag == 'None' or dst_ag == '' else int(dst_ag)

    if method.lower() == 'delete':
        ibs.delete_annots(aid)
        print('[web] (DELETED) turk_id: %s, aid: %d' % (turk_id, aid, ))
        aid = None  # Reset AID to prevent previous
    else:
        if src_ag is not None and dst_ag is not None:
            movegroup_aid(ibs, aid, src_ag, dst_ag)
        quality = int(request.form['quality-value'])
        ibs.set_annot_qualities([aid], [quality])
        print('[web] turk_id: %s, aid: %d, quality: %d' % (turk_id, aid, quality))
    # Return HTML
    refer = request.args.get('refer', '')
    if len(refer) > 0:
        return redirect(ap.decode_refer_url(refer))
    else:
        return redirect(url_for('turk_quality', imgsetid=imgsetid, src_ag=src_ag,
                                dst_ag=dst_ag, previous=aid))


@register_route('/submit/additional', methods=['POST'])
def submit_additional():
    ibs = current_app.ibs
    method = request.form.get('additional-submit', '')
    imgsetid = request.args.get('imgsetid', '')
    imgsetid = None if imgsetid == 'None' or imgsetid == '' else int(imgsetid)
    aid = int(request.form['additional-aid'])
    turk_id = request.cookies.get('turk_id', -1)

    if method.lower() == 'delete':
        ibs.delete_annots(aid)
        print('[web] (DELETED) turk_id: %s, aid: %d' % (turk_id, aid, ))
        aid = None  # Reset AID to prevent previous
    else:
        sex = int(request.form['additional-sex-value'])
        age = int(request.form['additional-age-value'])
        age_min = None
        age_max = None
        # Sex
        if sex >= 2:
            sex -= 2
        else:
            sex = -1

        if age == 1:
            age_min = None
            age_max = None
        elif age == 2:
            age_min = None
            age_max = 2
        elif age == 3:
            age_min = 3
            age_max = 5
        elif age == 4:
            age_min = 6
            age_max = 11
        elif age == 5:
            age_min = 12
            age_max = 23
        elif age == 6:
            age_min = 24
            age_max = 35
        elif age == 7:
            age_min = 36
            age_max = None

        ibs.set_annot_sex([aid], [sex])
        nid = ibs.get_annot_name_rowids(aid)
        DAN_SPECIAL_WRITE_AGE_TO_ALL_ANOTATIONS = True
        if nid is not None and DAN_SPECIAL_WRITE_AGE_TO_ALL_ANOTATIONS:
            aid_list = ibs.get_name_aids(nid)
            ibs.set_annot_age_months_est_min(aid_list, [age_min] * len(aid_list))
            ibs.set_annot_age_months_est_max(aid_list, [age_max] * len(aid_list))
        else:
            ibs.set_annot_age_months_est_min([aid], [age_min])
            ibs.set_annot_age_months_est_max([aid], [age_max])
        print('[web] turk_id: %s, aid: %d, sex: %r, age: %r' % (turk_id, aid, sex, age))
    # Return HTML
    refer = request.args.get('refer', '')
    if len(refer) > 0:
        return redirect(ap.decode_refer_url(refer))
    else:
        return redirect(url_for('turk_additional', imgsetid=imgsetid, previous=aid))


@register_route('/ajax/cookie')
def set_cookie():
    response = make_response('true')
    response.set_cookie(request.args['name'], request.args['value'])
    print('[web] Set Cookie: %r -> %r' % (request.args['name'], request.args['value'], ))
    return response


@register_route('/ajax/image/src/<gid>')
def image_src(gid=None, fresh=False, **kwargs):
    ibs = current_app.ibs
    # gpath = ibs.get_image_paths(gid)
    gpath = ibs.get_image_thumbpath(gid, ensure_paths=True)
    fresh = fresh or 'fresh' in request.args or 'fresh' in request.form
    if fresh:
        # print('*' * 80)
        # print('\n\n')
        # print('RUNNING WITH FRESH')
        # print('\n\n')
        # print('*' * 80)
        # ut.remove_dirs(gpath)
        import os
        os.remove(gpath)
        gpath = ibs.get_image_thumbpath(gid, ensure_paths=True)
    return ap.return_src(gpath)


@register_api('/api/image/<gid>/', methods=['GET'])
def image_src_api(gid=None, fresh=False, **kwargs):
    r"""
    Returns the base64 encoded image of image <gid>

    RESTful:
        Method: GET
        URL:    /api/image/<gid>/
    """
    return image_src(gid, fresh=fresh, **kwargs)


@register_route('/api/image/view/<gid>/', methods=['GET'])
def image_view_api(gid=None, fresh=False, **kwargs):
    r"""
    Returns the base64 encoded image of image <gid>

    RESTful:
        Method: GET
        URL:    /api/image/view/<gid>/
    """
    encoded = image_src(gid, fresh=fresh, **kwargs)
    return ap.template(None, 'single', encoded=encoded)


@register_api('/api/image/zip', methods=['POST'])
def image_upload_zip(**kwargs):
    r"""
    Returns the gid_list for image files submitted in a ZIP archive.  The image
    archive should be flat (no folders will be scanned for images) and must be smaller
    than 100 MB.  The archive can submit multiple images, ideally in JPEG format to save
    space.  Duplicate image uploads will result in the duplicate images receiving
    the same gid based on the hashed pixel values.

    Args:
        image_zip_archive (binary): the POST variable containing the binary
            (multi-form) image archive data
        **kwargs: Arbitrary keyword arguments; the kwargs are passed down to
            the add_images function

    Returns:
        gid_list (list if rowids): the list of gids corresponding to the images
            submitted.  The gids correspond to the image names sorted in
            lexigraphical order.

    RESTful:
        Method: POST
        URL:    /api/image/zip
    """
    ibs = current_app.ibs
    # Get image archive
    image_archive = request.files.get('image_zip_archive', None)
    if image_archive is None:
        raise IOError('Image archive not given')

    # If the directory already exists, delete it
    uploads_path = ibs.get_uploadsdir()
    ut.ensuredir(uploads_path)
    current_time = time.strftime('%Y_%m_%d_%H_%M_%S')

    modifier = 1
    upload_path = '%s' % (current_time)
    while exists(upload_path):
        upload_path = '%s_%04d' % (current_time, modifier)
        modifier += 1

    upload_path = join(uploads_path, upload_path)
    ut.ensuredir(upload_path)

    # Extract the content
    try:
        with zipfile.ZipFile(image_archive, 'r') as zfile:
            zfile.extractall(upload_path)
    except Exception:
        ut.remove_dirs(upload_path)
        raise IOError('Image archive extracton failed')

    """
    test to ensure Directory and utool do the same thing

    from detecttools.directory import Directory
    upload_path = ut.truepath('~/Pictures')
    gpath_list1 = sorted(ut.list_images(upload_path, recursive=False, full=True))

    direct = Directory(upload_path, include_file_extensions='images', recursive=False)
    gpath_list = direct.files()
    gpath_list = sorted(gpath_list)

    assert gpath_list1 == gpath_list
    """

    gpath_list = sorted(ut.list_images(upload_path, recursive=False, full=True))
    #direct = Directory(upload_path, include_file_extensions='images', recursive=False)
    #gpath_list = direct.files()
    #gpath_list = sorted(gpath_list)
    gid_list = ibs.add_images(gpath_list, **kwargs)
    return gid_list


@register_api('/api/image/json/', methods=['POST'])
def add_images_json(ibs, image_uri_list, image_uuid_list, image_width_list,
                    image_height_list, image_orig_name_list=None, image_ext_list=None,
                    image_time_posix_list=None, image_gps_lat_list=None,
                    image_gps_lon_list=None, image_notes_list=None, **kwargs):
    """
    REST:
        Method: POST
        URL: /api/image/json/

    Ignore:
        sudo pip install boto

    Args:
        image_uri_list (list) : list of string image uris, most likely HTTP(S) or S3
            encoded URLs.  Alternatively, this can be a list of dictionaries (JSON
            objects) that specify AWS S3 stored assets.  An example below:

                image_uri_list = [
                    'http://domain.com/example/asset1.png',
                    '/home/example/Desktop/example/asset2.jpg',
                    's3://s3.amazon.com/example-bucket-2/asset1-in-bucket-2.tif',
                    {
                        'bucket'          : 'example-bucket-1',
                        'key'             : 'example/asset1.png',
                        'auth_domain'     : None,  # Uses localhost
                        'auth_access_id'  : None,  # Uses system default
                        'auth_secret_key' : None,  # Uses system default
                    },
                    {
                        'bucket' : 'example-bucket-1',
                        'key'    : 'example/asset2.jpg',
                        # if unspecified, auth uses localhost and system defaults
                    },
                    {
                        'bucket'          : 'example-bucket-2',
                        'key'             : 'example/asset1-in-bucket-2.tif',
                        'auth_domain'     : 's3.amazon.com',
                        'auth_access_id'  : '____________________',
                        'auth_secret_key' : '________________________________________',
                    },
                ]

            Note that you cannot specify AWS authentication access ids or secret keys
            using string uri's.  For specific authentication methods, please use the
            latter list of dictionaries.

        image_uuid_list (list of str) : list of image UUIDs to be used in IBEIS IA
        image_width_list (list of int) : list of image widths
        image_height_list (list of int) : list of image heights
        image_orig_name_list (list of str): list of original image names
        image_ext_list (list of str): list of original image names
        image_time_posix_list (list of int): list of image's POSIX timestamps
        image_gps_lat_list (list of float): list of image's GPS latitude values
        image_gps_lon_list (list of float): list of image's GPS longitude values
        image_notes_list (list of str) : optional list of any related notes with
            the images
        **kwargs : key-value pairs passed to the ibs.add_images() function.

    CommandLine:
        python -m ibeis.web.app --test-add_images_json

    Example:
        >>> # WEB_DOCTEST
        >>> from ibeis.control.IBEISControl import *  # NOQA
        >>> import ibeis
        >>> web_instance = ibeis.opendb(db='testdb1')
        >>> _payload = {
        >>>     'image_uri_list': [
        >>>         'https://upload.wikimedia.org/wikipedia/commons/4/49/Zebra_running_Ngorongoro.jpg',
        >>>         {
        >>>             'bucket'          : 'test-asset-store',
        >>>             'key'             : 'caribwhale/20130903-JAC-0002.JPG',
        >>>         },
        >>>     ],
        >>>     'image_uuid_list': [
        >>>         uuid.UUID('7fea8101-7dec-44e3-bf5d-b8287fd231e2'),
        >>>         uuid.UUID('c081119a-e08e-4863-a710-3210171d27d6'),
        >>>     ],
        >>>     'image_width_list': [
        >>>         1992,
        >>>         1194,
        >>>     ],
        >>>     'image_height_list': [
        >>>         1328,
        >>>         401,
        >>>     ],
        >>> }
        >>> gid_list = ibeis.web.app.add_images_json(web_instance, **_payload)
        >>> print(gid_list)
        >>> print(web_instance.get_image_uuids(gid_list))
        >>> print(web_instance.get_image_uris(gid_list))
        >>> print(web_instance.get_image_paths(gid_list))
        >>> print(web_instance.get_image_uris_original(gid_list))
    """
    def _get_standard_ext(gpath):
        ext = splitext(gpath)[1].lower()
        return '.jpg' if ext == '.jpeg' else ext

    def _parse_imageinfo(index):
        def _resolve_uri():
            list_ = image_uri_list
            if list_ is None or index >= len(list_) or list_[index] is None:
                raise ValueError('Must specify all required fields')
            value = list_[index]
            if isinstance(value, dict):
                value = ut.s3_dict_encode_to_str(value)
            return value

        def _resolve(list_, default='', assert_=False):
            if list_ is None or index >= len(list_) or list_[index] is None:
                if assert_:
                    raise ValueError('Must specify all required fields')
                return default
            return list_[index]

        uri = _resolve_uri()
        orig_gname = basename(uri)
        ext = _get_standard_ext(uri)

        uuid_ = _resolve(image_uuid_list, assert_=True)
        if isinstance(uuid_, six.string_types):
            uuid_ = uuid.UUID(uuid_)

        param_tup = (
            uuid_,
            uri,
            uri,
            _resolve(image_orig_name_list, default=orig_gname),
            _resolve(image_ext_list, default=ext),
            int(_resolve(image_width_list, assert_=True)),
            int(_resolve(image_height_list, assert_=True)),
            int(_resolve(image_time_posix_list, default=-1)),
            float(_resolve(image_gps_lat_list, default=-1.0)),
            float(_resolve(image_gps_lon_list, default=-1.0)),
            _resolve(image_notes_list),
        )
        return param_tup

    # TODO: FIX ME SO THAT WE DON'T HAVE TO LOCALIZE EVERYTHING
    kwargs['auto_localize'] = kwargs.get('auto_localize', True)
    kwargs['sanitize'] = kwargs.get('sanitize', False)

    index_list = range(len(image_uri_list))
    params_gen = ut.generate(_parse_imageinfo, index_list, adjust=True,
                             force_serial=True, **kwargs)
    params_gen = list(params_gen)
    gpath_list = [ _[0] for _ in params_gen ]
    gid_list = ibs.add_images(gpath_list, params_list=params_gen, **kwargs)  # NOQA
    return gid_list


@register_api('/api/annot/json/', methods=['POST'])
def add_annots_json(ibs, image_uuid_list, annot_uuid_list, annot_bbox_list,
                    annot_theta_list=None, annot_species_list=None,
                    annot_name_list=None, annot_notes_list=None, **kwargs):
    """
    REST:
        Method: POST
        URL: /api/annot/json/

    Ignore:
        sudo pip install boto

    Args:
        image_uuid_list (list of str) : list of image UUIDs to be used in IBEIS IA
        annot_uuid_list (list of str) : list of annotations UUIDs to be used in IBEIS IA
        annot_bbox_list (list of 4-tuple) : list of bounding box coordinates encoded as
            a 4-tuple of the values (xtl, ytl, width, height) where xtl is the
            'top left corner, x value' and ytl is the 'top left corner, y value'.
        annot_theta_list (list of float) : list of radian rotation around center.
            Defaults to 0.0 (no rotation).
        annot_species_list (list of str) : list of species for the annotation, if known.
            If the list is partially known, use None (null in JSON) for unknown entries.
        annot_name_list (list of str) : list of names for the annotation, if known.
            If the list is partially known, use None (null in JSON) for unknown entries.
        annot_notes_list (list of str) : list of notes to be added to the annotation.
        **kwargs : key-value pairs passed to the ibs.add_annots() function.

    CommandLine:
        python -m ibeis.web.app --test-add_annots_json

    Example:
        >>> import ibeis
        >>> from ibeis.control.IBEISControl import *  # NOQA
        >>> web_instance = ibeis.opendb(db='testdb1')
        >>> _payload = {
        >>>     'image_uuid_list': [
        >>>         uuid.UUID('7fea8101-7dec-44e3-bf5d-b8287fd231e2'),
        >>>         uuid.UUID('c081119a-e08e-4863-a710-3210171d27d6'),
        >>>     ],
        >>>     'annot_uuid_list': [
        >>>         uuid.UUID('fe1547c5-1425-4757-9b8f-b2b4a47f552d'),
        >>>         uuid.UUID('86d3959f-7167-4822-b99f-42d453a50745'),
        >>>     ],
        >>>     'annot_bbox_list': [
        >>>         [0, 0, 1992, 1328],
        >>>         [0, 0, 1194, 401],
        >>>     ],
        >>> }
        >>> aid_list = ibeis.web.app.add_annots_json(web_instance, **_payload)
        >>> print(aid_list)
        >>> print(web_instance.get_annot_image_uuids(aid_list))
        >>> print(web_instance.get_annot_uuids(aid_list))
        >>> print(web_instance.get_annot_bboxes(aid_list))
    """

    image_uuid_list = [
        uuid.UUID(uuid_) if isinstance(uuid_, six.string_types) else uuid_
        for uuid_ in image_uuid_list
    ]
    annot_uuid_list = [
        uuid.UUID(uuid_) if isinstance(uuid_, six.string_types) else uuid_
        for uuid_ in annot_uuid_list
    ]
    gid_list = ibs.get_image_gids_from_uuid(image_uuid_list)
    aid_list = ibs.add_annots(gid_list, annot_uuid_list=annot_uuid_list,  # NOQA
                              bbox_list=annot_bbox_list, theta_list=annot_theta_list,
                              species_list=annot_species_list, name_list=annot_name_list,
                              notes_list=annot_notes_list, **kwargs)
    # return aid_list


@register_api('/api/image/', methods=['POST'])
def image_upload(cleanup=True, **kwargs):
    r"""
    Returns the gid for an uploaded image.

    Args:
        image (image binary): the POST variable containing the binary
            (multi-form) image data
        **kwargs: Arbitrary keyword arguments; the kwargs are passed down to
            the add_images function

    Returns:
        gid (rowids): gid corresponding to the image submitted.
            lexigraphical order.

    RESTful:
        Method: POST
        URL:    /api/image/
    """
    ibs = current_app.ibs
    print('request.files = %s' % (request.files,))

    filestore = request.files.get('image', None)
    if filestore is None:
        raise IOError('Image not given')

    uploads_path = ibs.get_uploadsdir()
    ut.ensuredir(uploads_path)
    current_time = time.strftime('%Y_%m_%d_%H_%M_%S')

    modifier = 1
    upload_filename = 'upload_%s.png' % (current_time)
    while exists(upload_filename):
        upload_filename = 'upload_%s_%04d.png' % (current_time, modifier)
        modifier += 1

    upload_filepath = join(uploads_path, upload_filename)
    filestore.save(upload_filepath)

    gid_list = ibs.add_images([upload_filepath], **kwargs)
    gid = gid_list[0]

    if cleanup:
        ut.remove_dirs(upload_filepath)

    return gid


@register_api('/api/core/helloworld/', methods=['GET', 'POST', 'DELETE', 'PUT'])
def hello_world(*args, **kwargs):
    print('------------------ HELLO WORLD ------------------')
    print('Args:', args)
    print('Kwargs:', kwargs)
    print('request.args:', request.args)
    print('request.form', request.form)


VALID_TURK_MODES = [
    ('turk_viewpoint', 'Viewpoint'),
    ('turk_quality', 'Quality'),
]


@register_route('/group_review/')
def group_review():
    prefill = request.args.get('prefill', '')
    if len(prefill) > 0:
        ibs = current_app.ibs
        aid_list = ibs.get_valid_aids()
        bad_species_list, bad_viewpoint_list = ibs.validate_annot_species_viewpoint_cnn(aid_list)

        GROUP_BY_PREDICTION = True
        if GROUP_BY_PREDICTION:
            grouped_dict = ut.group_items(bad_viewpoint_list, ut.get_list_column(bad_viewpoint_list, 3))
            grouped_list = grouped_dict.values()
            regrouped_items = ut.flatten(ut.sortedby(grouped_list, map(len, grouped_list)))
            candidate_aid_list = ut.get_list_column(regrouped_items, 0)
        else:
            candidate_aid_list = [ bad_viewpoint[0] for bad_viewpoint in bad_viewpoint_list]
    elif request.args.get('aid_list', None) is not None:
        aid_list = request.args.get('aid_list', '')
        if len(aid_list) > 0:
            aid_list = aid_list.replace('[', '')
            aid_list = aid_list.replace(']', '')
            aid_list = aid_list.strip().split(',')
            candidate_aid_list = [ int(aid_.strip()) for aid_ in aid_list ]
        else:
            candidate_aid_list = ''
    else:
        candidate_aid_list = ''

    return ap.template(None, 'group_review', candidate_aid_list=candidate_aid_list, mode_list=VALID_TURK_MODES)


@register_route('/group_review/submit/', methods=['POST'])
def group_review_submit():
    """
    CommandLine:
        python -m ibeis.web.app --exec-group_review_submit

    Example:
        >>> # UNSTABLE_DOCTEST
        >>> from ibeis.web.app import *  # NOQA
        >>> import ibeis
        >>> import ibeis.web
        >>> ibs = ibeis.opendb('testdb1')
        >>> aid_list = ibs.get_valid_aids()[::2]
        >>> ibs.start_web_annot_groupreview(aid_list)
    """
    ibs = current_app.ibs
    method = request.form.get('group-review-submit', '')
    if method.lower() == 'populate':
        redirection = request.referrer
        if 'prefill' not in redirection:
            # Prevent multiple clears
            if '?' in redirection:
                redirection = '%s&prefill=true' % (redirection, )
            else:
                redirection = '%s?prefill=true' % (redirection, )
        return redirect(redirection)
    aid_list = request.form.get('aid_list', '')
    if len(aid_list) > 0:
        aid_list = aid_list.replace('[', '')
        aid_list = aid_list.replace(']', '')
        aid_list = aid_list.strip().split(',')
        aid_list = [ int(aid_.strip()) for aid_ in aid_list ]
    else:
        aid_list = []
    src_ag, dst_ag = ibs.prepare_annotgroup_review(aid_list)
    valid_modes = ut.get_list_column(VALID_TURK_MODES, 0)
    mode = request.form.get('group-review-mode', None)
    assert mode in valid_modes
    return redirect(url_for(mode, src_ag=src_ag, dst_ag=dst_ag))


@register_route('/ajax/annotation/src/<aid>')
def annotation_src(aid=None):
    ibs = current_app.ibs
    gpath = ibs.get_annot_chip_fpath(aid)
    return ap.return_src(gpath)


@register_api('/api/annot/<aid>/', methods=['GET'])
def annotation_src_api(aid=None):
    r"""
    Returns the base64 encoded image of annotation <aid>

    RESTful:
        Method: GET
        URL:    /api/annot/<aid>/
    """
    return annotation_src(aid)


@register_route('/display/sightings')
def display_sightings(html_encode=True):
    ibs = current_app.ibs
    complete = request.args.get('complete', None) is not None
    sightings = ibs.report_sightings_str(complete=complete, include_images=True)
    if html_encode:
        sightings = sightings.replace('\n', '<br/>')
    return sightings


@register_route('/download/sightings')
def download_sightings():
    filename = 'sightings.csv'
    sightings = display_sightings(html_encode=False)
    return ap.send_file(sightings, filename)


@register_route('/graph/sightings')
def graph_sightings():
    return redirect(url_for('view'))


@register_route('/dbinfo')
def dbinfo():
    try:
        ibs = current_app.ibs
        dbinfo_str = ibs.get_dbinfo_str()
    except:
        dbinfo_str = ''
    dbinfo_str_formatted = '<pre>%s</pre>' % (dbinfo_str, )
    return dbinfo_str_formatted


@register_route('/api')
def api():
    rules = current_app.url_map.iter_rules()
    rule_dict = {}
    for rule in rules:
        methods = rule.methods
        url = str(rule)
        if '/api/' in url:
            methods -= set(['HEAD', 'OPTIONS'])
            if len(methods) == 0:
                continue
            if len(methods) > 1:
                print('methods = %r' % (methods,))
            method = list(methods)[0]
            if method not in rule_dict.keys():
                rule_dict[method] = []
            rule_dict[method].append((method, url, ))
    for method in rule_dict.keys():
        rule_dict[method].sort()
    url = '%s/api/core/dbname/' % (current_app.server_url, )
    app_auth = controller_inject.get_url_authorization(url)
    return ap.template(None, 'api',
                       app_url=url,
                       app_name=controller_inject.GLOBAL_APP_NAME,
                       app_secret=controller_inject.GLOBAL_APP_SECRET,
                       app_auth=app_auth,
                       rule_list=rule_dict)


@register_route('/upload')
def upload():
    return ap.template(None, 'upload')


@register_route('/404')
def error404(exception=None):
    import traceback
    exception_str = str(exception)
    traceback_str = str(traceback.format_exc())
    print('[web] %r' % (exception_str, ))
    print('[web] %r' % (traceback_str, ))
    return ap.template(None, '404', exception_str=exception_str,
                       traceback_str=traceback_str)


################################################################################


def start_tornado(ibs, port=None, browser=BROWSER, url_suffix=''):
    """
        Initialize the web server
    """
    def _start_tornado(ibs_, port_):
        # Get Flask app
        app = controller_inject.get_flask_app()
        app.ibs = ibs_
        # Try to ascertain the socket's domain name
        try:
            app.server_domain = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            app.server_domain = '127.0.0.1'
        app.server_port = port_
        # URL for the web instance
        app.server_url = 'http://%s:%s' % (app.server_domain, app.server_port)
        print('[web] Tornado server starting at %s' % (app.server_url,))
        # Launch the web browser to view the web interface and API
        if browser:
            url = app.server_url + url_suffix
            import webbrowser
            print('[web] opening browser with url = %r' % (url,))
            webbrowser.open(url)
        # Start the tornado web handler
        # WSGI = Web Server Gateway Interface
        # WSGI is Python standard described in detail in PEP 3333
        http_server = tornado.httpserver.HTTPServer(
            tornado.wsgi.WSGIContainer(app))
        http_server.listen(app.server_port)
        tornado.ioloop.IOLoop.instance().start()

    # Set logging level
    logging.getLogger().setLevel(logging.INFO)
    # Get the port if unspecified
    if port is None:
        port = DEFAULT_WEB_API_PORT
    # Launch the web handler
    _start_tornado(ibs, port)


def start_from_ibeis(ibs, port=None, browser=BROWSER, precache=None,
                     url_suffix='', start_job_queue=True):
    """
    Parse command line options and start the server.

    CommandLine:
        python -m ibeis --db PZ_MTEST --web
        python -m ibeis --db PZ_MTEST --web --browser
    """
    print('[web] start_from_ibeis()')
    if precache is None:
        precache = ut.get_argflag('--precache')

    if precache:
        print('[web] Pre-computing all image thumbnails (with annots)...')
        ibs.preprocess_image_thumbs()
        print('[web] Pre-computing all image thumbnails (without annots)...')
        ibs.preprocess_image_thumbs(draw_annots=False)
        print('[web] Pre-computing all annotation chips...')
        ibs.check_chip_existence()
        ibs.compute_all_chips()

    if start_job_queue:
        print('[web] opening job manager')
        ibs.load_plugin_module(zmq_task_queue)
        #import time
        #time.sleep(1)
        ibs.initialize_job_manager()
        #time.sleep(10)

    print('[web] starting tornado')
    start_tornado(ibs, port, browser, url_suffix)
    print('[web] closing job manager')
    ibs.close_job_manager()


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis.web.app
        python -m ibeis.web.app --allexamples
        python -m ibeis.web.app --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
