# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import utool as ut
import six
from ibeis import _ibeis_object
from ibeis.control.controller_inject import make_ibs_register_decorator
(print, rrr, profile) = ut.inject2(__name__, '[images]')

CLASS_INJECT_KEY, register_ibs_method = make_ibs_register_decorator(__name__)

BASE_TYPE = type


@register_ibs_method
def images(ibs, gids=None, config=None):
    if gids is None:
        gids = ibs.get_valid_gids()
    gids = ut.ensure_iterable(gids)
    return Images(gids, ibs, config)


@register_ibs_method
def imagesets(ibs, gsids=None, text=None):
    if text is not None:
        gsids = ibs.get_imageset_imgsetids_from_text(text)
    if gsids is None:
        gsids = ibs.get_valid_imgsetids()
    gsids = ut.ensure_iterable(gsids)
    return ImageSets(gsids, ibs)


class ImageIBEISPropertyInjector(BASE_TYPE):
    def __init__(metaself, name, bases, dct):
        super(ImageIBEISPropertyInjector, metaself).__init__(name, bases, dct)
        metaself.rrr = rrr
        #misc = [ 'instancelist', 'gids_with_aids', 'lazydict', ]  #
        attrs = ['aids', 'aids_of_species', 'annot_uuids',
                 'annot_uuids_of_species', 'annotation_bboxes',
                 'annotation_thetas', 'contributor_rowid', 'contributor_tag',
                 'datetime', 'datetime_str', 'detect_confidence',
                 'detectpaths', 'enabled', 'exts', 'gid', 'glrids', 'gnames',
                 'gps', 'gsgrids', 'heights', 'imagesettext', 'imgset_uuids',
                 'imgsetids', 'lat', 'location_codes', 'lon', 'missing_uuid',
                 'name_uuids', 'nids', 'notes', 'num_annotations',
                 'orientation', 'orientation_str', 'party_rowids', 'party_tag',
                 'paths', 'reviewed', 'sizes', 'species_rowids',
                 'species_uuids', 'thumbpath', 'thumbtup', 'time_statstr',
                 'timedelta_posix', 'unixtime',
                 'uris',
                 'imgdata',
                 'uris_original', 'uuids', 'widths']
        #inverse_attrs = [
        #     'gids_from_uuid',
        #]
        objname = 'image'
        _ibeis_object._inject_getter_attrs(metaself, objname, attrs, [])


@ut.reloadable_class
@six.add_metaclass(ImageIBEISPropertyInjector)
class Images(_ibeis_object.ObjectList1D):
    """
    Represents a group of annotations. Efficiently accesses properties from a
    database using lazy evaluation.

    CommandLine:
        python -m ibeis.images Images --show

    Example:
        >>> from ibeis.images import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb(defaultdb='testdb1')
        >>> gids = ibs.get_valid_gids()
        >>> g = self = images = Images(gids, ibs)
        >>> print(g.widths)
        >>> print(g)
        <Images(num=13)>
    """
    def __init__(self, gids, ibs, config=None):
        super(Images, self).__init__(gids, ibs, config)

    @property
    def gids(self):
        return self._rowids

    @property
    def annots(self):
        return [self._ibs.annots(aids) for aids in self.aids]

    @property
    def _annot_groups(self):
        return self._ibs._annot_groups(self.annots)


class ImageSetAttrInjector(BASE_TYPE):
    """
    Example:
        >>> # SCRIPT
        >>> from ibeis import _ibeis_object
        >>> import ibeis
        >>> ibs = ibeis.opendb(defaultdb='testdb1')
        >>> objname = 'imageset'
        >>> blacklist = []
        >>> _ibeis_object._find_ibeis_attrs(ibs, objname, blacklist)
    """
    def __init__(metaself, name, bases, dct):
        super(ImageSetAttrInjector, metaself).__init__(name, bases, dct)
        metaself.rrr = rrr
        #misc = [ 'instancelist', 'gids_with_aids', 'lazydict', ]  #
        attrs = ['aids', 'configid', 'custom_filtered_aids', 'duration',
                 'end_time_posix', 'fraction_annotmatch_reviewed',
                 'fraction_imgs_reviewed', 'fraction_names_with_exemplar',
                 'gids', 'gps_lats', 'gps_lons', 'gsgrids', 'image_uuids',
                 'imgsetids_from_text', 'imgsetids_from_uuid', 'isoccurrence',
                 'name_uuids', 'nids', 'note', 'notes', 'num_aids',
                 'num_annotmatch_reviewed', 'num_annots_reviewed', 'num_gids',
                 'num_imgs_reviewed', 'num_names_with_exemplar',
                 'percent_annotmatch_reviewed_str',
                 'percent_imgs_reviewed_str',
                 'percent_names_with_exemplar_str', 'processed_flags',
                 'shipped_flags', 'smart_waypoint_ids', 'smart_xml_contents',
                 'smart_xml_fnames', 'start_time_posix', 'text', 'uuid',
                 'uuids']
        #inverse_attrs = [
        #     'gids_from_uuid',
        #]
        objname = 'imageset'
        _ibeis_object._inject_getter_attrs(metaself, objname, attrs, [])


@ut.reloadable_class
@six.add_metaclass(ImageSetAttrInjector)
class ImageSets(_ibeis_object.ObjectList1D):
    """
    Represents a group of annotations. Efficiently accesses properties from a
    database using lazy evaluation.

    CommandLine:
        python -m ibeis.images ImageSets --show

    Example:
        >>> from ibeis.images import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb(defaultdb='testdb1')
        >>> gsids = ibs._get_all_imgsetids()
        >>> self = ImageSets(gsids, ibs)
        >>> print(self)
        <ImageSets(num=13)>

    """
    def __init__(self, gsids, ibs, config=None):
        super(ImageSets, self).__init__(gsids, ibs, config)

    @property
    def images(self):
        return [self._ibs.images(gids) for gids in self.gids]

    @property
    def annots(self):
        return [self._ibs.annots(aids) for aids in self.aids]

if __name__ == '__main__':
    r"""
    CommandLine:
        python -m ibeis.images
        python -m ibeis.images --allexamples
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
