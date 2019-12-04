# -*- coding: utf-8 -*-
"""
VTool - Computer vision tools

Autogenerate Command:
    mkinit vtool_ibeis -i
"""
# flake8: noqa
from __future__ import absolute_import, division, print_function
__version__ = '2.0.0'


__submodules__ = [
    'histogram',
    'features',
    'linalg',
    'blend',
    'image_shared',
    'image',
    'exif',
    'distance',
    'keypoint',
    'ellipse',
    'patch',
    'chip',
    'spatial_verification',
    'trig',
    'util_math',
    'matching',
    'geometry',
    'nearest_neighbors',
    'clustering2',
    'other',
    'numpy_utils',
    'confusion',
    'score_normalization',
    'symbolic',
    'demodata',
]

from vtool_ibeis import histogram
from vtool_ibeis import features
from vtool_ibeis import linalg
from vtool_ibeis import blend
from vtool_ibeis import image_shared
from vtool_ibeis import image
from vtool_ibeis import exif
from vtool_ibeis import distance
from vtool_ibeis import keypoint
from vtool_ibeis import ellipse
from vtool_ibeis import patch
from vtool_ibeis import chip
from vtool_ibeis import spatial_verification
from vtool_ibeis import trig
from vtool_ibeis import util_math
from vtool_ibeis import matching
from vtool_ibeis import geometry
from vtool_ibeis import nearest_neighbors
from vtool_ibeis import clustering2
from vtool_ibeis import other
from vtool_ibeis import numpy_utils
from vtool_ibeis import confusion
from vtool_ibeis import score_normalization
from vtool_ibeis import symbolic
from vtool_ibeis import demodata

# TODO: de-utoolificaiton: replace utool with ubelt
from vtool_ibeis import histogram as htool
from vtool_ibeis import linalg as ltool
from vtool_ibeis import image as gtool
from vtool_ibeis import exif as exiftool
from vtool_ibeis import keypoint as ktool
from vtool_ibeis import ellipse as etool
from vtool_ibeis import patch as ptool
from vtool_ibeis import chip as ctool
from vtool_ibeis import spatial_verification as svtool
from vtool_ibeis import clustering2 as clustertool
from vtool_ibeis import trig
from vtool_ibeis import util_math as mtool

import sys

"""
break
"""

# <AUTOGEN_INIT>
from vtool_ibeis import histogram
from vtool_ibeis import features
from vtool_ibeis import linalg
from vtool_ibeis import blend
from vtool_ibeis import image_shared
from vtool_ibeis import image
from vtool_ibeis import exif
from vtool_ibeis import distance
from vtool_ibeis import keypoint
from vtool_ibeis import ellipse
from vtool_ibeis import patch
from vtool_ibeis import chip
from vtool_ibeis import spatial_verification
from vtool_ibeis import trig
from vtool_ibeis import util_math
from vtool_ibeis import matching
from vtool_ibeis import geometry
from vtool_ibeis import nearest_neighbors
from vtool_ibeis import clustering2
from vtool_ibeis import other
from vtool_ibeis import numpy_utils
from vtool_ibeis import confusion
from vtool_ibeis import score_normalization
from vtool_ibeis import symbolic
from vtool_ibeis import demodata

from vtool_ibeis.histogram import (argsubextrema2, argsubmax, argsubmax2,
                             argsubmaxima, argsubmaxima2, argsubmin2,
                             argsubminima2, get_histinfo_str, hist_argmaxima,
                             hist_argmaxima2, hist_edges_to_centers,
                             interpolate_submaxima, interpolated_histogram,
                             linear_interpolation, maxima_neighbors,
                             maximum_parabola_point, show_hist_submaxima,
                             show_ori_image, show_ori_image_ondisk,
                             subbin_bounds, wrap_histogram,)
from vtool_ibeis.features import (detect_opencv_keypoints,
                            extract_feature_from_patch, extract_features,
                            get_extract_features_default_params, test_mser,)
from vtool_ibeis.linalg import (TRANSFORM_DTYPE, add_homogenous_coordinate,
                          affine_around_mat3x3, affine_mat3x3, det_ltri,
                          dot_ltri, gauss2d_pdf, inv_ltri, normalize,
                          normalize_rows, random_affine_args,
                          random_affine_transform,
                          remove_homogenous_coordinate,
                          rotation_around_bbox_mat3x3, rotation_around_mat3x3,
                          rotation_mat2x2, rotation_mat3x3,
                          scale_around_mat3x3, scale_mat3x3, shear_mat3x3, svd,
                          transform_around, transform_points_with_homography,
                          translation_mat3x3, whiten_xy_points,)
from vtool_ibeis.blend import (blend_images, blend_images_average,
                         blend_images_average_stack, blend_images_mult_average,
                         blend_images_multiply, ensure_alpha_channel,
                         ensure_grayscale, gamma_adjust,
                         gridsearch_addWeighted, gridsearch_image_function,
                         overlay_alpha_images, testdata_blend,)
from vtool_ibeis.image_shared import (open_pil_image, print_image_checks,)
from vtool_ibeis.image import (EXIF_TAG_DATETIME, EXIF_TAG_GPS, LINE_AA,
                         affine_warp_around_center, clipwhite,
                         clipwhite_ondisk, combine_offset_lists,
                         convert_colorspace, convert_image_list_colorspace,
                         crop_out_imgfill, cvt_BGR2L, cvt_BGR2RGB, draw_text,
                         embed_channels, embed_in_square_image,
                         ensure_3channel, ensure_4channel,
                         filterflags_valid_images, find_pixel_value_index,
                         get_num_channels, get_pixel_dist,
                         get_round_scaled_dsize, get_scale_factor, get_size,
                         imread, imread_remote_s3, imread_remote_url, imwrite,
                         imwrite_fallback, infer_vert,
                         make_channels_comparable, make_white_transparent,
                         montage, open_image_size, pad_image, pad_image_ondisk,
                         padded_resize, perlin_noise, rectify_to_float01,
                         rectify_to_square, rectify_to_uint8, resize,
                         resize_image_by_scale, resize_mask, resize_thumb,
                         resize_to_maxdims, resize_to_maxdims_ondisk,
                         resized_clamped_thumb_dims, resized_dims_and_ratio,
                         rotate_image, rotate_image_ondisk, shear,
                         stack_image_list, stack_image_list_special,
                         stack_image_recurse, stack_images, stack_multi_images,
                         stack_multi_images2, stack_square_images,
                         subpixel_values, testdata_imglist, warpAffine,
                         warpHomog,)
from vtool_ibeis.exif import (DATETIMEORIGINAL_TAGID, EXIF_TAG_TO_TAGID,
                        GPSDATE_CODE, GPSINFO_CODE, GPSLATITUDEREF_CODE,
                        GPSLATITUDE_CODE, GPSLONGITUDEREF_CODE,
                        GPSLONGITUDE_CODE, GPSTIME_CODE, GPS_TAG_TO_GPSID,
                        ORIENTATION_000, ORIENTATION_090, ORIENTATION_180,
                        ORIENTATION_270, ORIENTATION_CODE, ORIENTATION_DICT,
                        ORIENTATION_DICT_INVERSE, ORIENTATION_ORDER_LIST,
                        ORIENTATION_UNDEFINED, SENSITIVITYTYPE_CODE,
                        check_exif_keys, convert_degrees, get_exif_dict,
                        get_exif_dict2, get_exif_tagids, get_exist,
                        get_lat_lon, get_orientation, get_orientation_str,
                        get_unixtime, get_unixtime_gps,
                        make_exif_dict_human_readable, parse_exif_unixtime,
                        parse_exif_unixtime_gps, read_all_exif_tags, read_exif,
                        read_exif_tags, read_one_exif_tag,)
from vtool_ibeis.distance import (L1, L2, L2_root_sift, L2_sift, L2_sift_sqrd,
                            L2_sqrd, TEMP_VEC_DTYPE, VALID_DISTS, bar_L2_sift,
                            bar_cos_sift, closest_point, compute_distances,
                            cos_sift, cosine_dist, cyclic_distance,
                            det_distance, emd, haversine, hist_isect,
                            nearest_point, ori_distance, pdist_argsort,
                            pdist_indicies, safe_pdist, signed_cyclic_distance,
                            signed_ori_distance, testdata_hist, testdata_sift2,
                            understanding_pseudomax_props, wrapped_distance,)
from vtool_ibeis.keypoint import (GRAVITY_THETA, KPTS_DTYPE, LOC_DIMS, ORI_DIM,
                            SCAX_DIM, SCAY_DIM, SHAPE_DIMS, SKEW_DIM, XDIM,
                            YDIM, augment_2x2_with_translation, cast_split,
                            convert_kptsZ_to_kpts, decompose_Z_to_RV_mats2x2,
                            decompose_Z_to_V_2x2, decompose_Z_to_invV_2x2,
                            decompose_Z_to_invV_mats2x2,
                            flatten_invV_mats_to_kpts, get_RV_mats2x2,
                            get_RV_mats_3x3, get_V_mats, get_Z_mats,
                            get_even_point_sample, get_grid_kpts,
                            get_invVR_mats2x2, get_invVR_mats3x3,
                            get_invVR_mats_oris, get_invVR_mats_shape,
                            get_invVR_mats_sqrd_scale, get_invVR_mats_xys,
                            get_invV_mats, get_invV_mats2x2, get_invV_mats3x3,
                            get_invVs, get_kpts_dlen_sqrd,
                            get_kpts_eccentricity, get_kpts_image_extent,
                            get_kpts_strs, get_kpts_wh,
                            get_match_spatial_squared_error, get_ori_mats,
                            get_ori_strs, get_oris, get_scales, get_shape_strs,
                            get_sqrd_scales,
                            get_transforms_from_patch_image_kpts,
                            get_uneven_point_sample, get_xy_strs, get_xys,
                            invert_invV_mats, kp_cpp_infostr, kpts_docrepr,
                            kpts_repr, offset_kpts, rectify_invV_mats_are_up,
                            transform_kpts, transform_kpts_to_imgspace,
                            transform_kpts_xys,)
from vtool_ibeis.ellipse import (adaptive_scale, check_kpts_in_bounds,
                           circular_distance, expand_kpts, expand_scales,
                           expand_subscales, extrema_neighbors, find_maxima,
                           find_maxima_with_neighbors, gradient_magnitude,
                           homogenous_circle_pts, interpolate_between,
                           interpolate_maxima, interpolate_peaks,
                           interpolate_peaks2, kpts_matrices,
                           sample_ell_border_pts, sample_ell_border_vals,
                           sample_uniform, subscale_peaks,)
from vtool_ibeis.patch import (GaussianBlurInplace, draw_kp_ori_steps,
                         find_dominant_kp_orientations, find_kpts_direction,
                         find_patch_dominant_orientations,
                         gaussian_average_patch, gaussian_patch,
                         gaussian_weight_patch, generate_to_patch_transforms,
                         get_cross_patch, get_no_symbol,
                         get_orientation_histogram, get_star2_patch,
                         get_star_patch, get_stripe_patch, get_test_patch,
                         get_unwarped_patch, get_unwarped_patches,
                         get_warped_patch, get_warped_patches, gradient_fill,
                         intern_warp_single_patch, inverted_sift_patch,
                         make_test_image_keypoints,
                         patch_gaussian_weighted_average_intensities,
                         patch_gradient, patch_mag, patch_ori,
                         show_gaussian_patch,
                         show_patch_orientation_estimation,
                         test_ondisk_find_patch_fpath_dominant_orientations,
                         test_show_gaussian_patches,
                         test_show_gaussian_patches2, testdata_patch,)
from vtool_ibeis.chip import (ScaleStrat, apply_filter_funcs, compute_chip,
                        extract_chip_from_gpath,
                        extract_chip_from_gpath_into_square,
                        extract_chip_from_img, extract_chip_into_square,
                        get_extramargin_measures, get_image_to_chip_transform,
                        get_scaled_size_with_dlen, gridsearch_chipextract,
                        testshow_extramargin_info,)
from vtool_ibeis.spatial_verification import (HAVE_SVER_C_WRAPPER, INDEX_DTYPE,
                                        SV_DTYPE, VERBOSE_SVER,
                                        build_affine_lstsqrs_Mx6,
                                        build_lstsqrs_Mx9, compute_affine,
                                        compute_homog,
                                        estimate_refined_transform,
                                        get_affine_inliers,
                                        get_best_affine_inliers,
                                        get_best_affine_inliers_,
                                        get_normalized_affine_inliers,
                                        refine_inliers, spatially_verify_kpts,
                                        test_affine_errors, test_homog_errors,
                                        testdata_matching_affine_inliers,
                                        testdata_matching_affine_inliers_normalized,
                                        try_svd, unnormalize_transform,)
from vtool_ibeis.trig import (atan2,)
from vtool_ibeis.util_math import (TAU, beaton_tukey_loss, beaton_tukey_weight,
                             breakup_equal_streak, ensure_monotone_decreasing,
                             ensure_monotone_increasing,
                             ensure_monotone_strictly_decreasing,
                             ensure_monotone_strictly_increasing, eps,
                             gauss_func1d, gauss_func1d_unnormalized,
                             gauss_parzen_est, group_consecutive, iceil,
                             interpolate_nans, iround, logistic_01, logit,
                             non_decreasing, non_increasing,
                             strictly_decreasing, strictly_increasing,
                             test_language_modulus,)
from vtool_ibeis.matching import (AnnotPairFeatInfo, AssignTup, MatchingError,
                            NORM_CHIP_CONFIG, PSEUDO_MAX_DIST,
                            PSEUDO_MAX_DIST_SQRD, PSEUDO_MAX_VEC_COMPONENT,
                            PairwiseMatch, SUM_OPS, VSONE_ASSIGN_CONFIG,
                            VSONE_DEFAULT_CONFIG, VSONE_FEAT_CONFIG,
                            VSONE_PI_DICT, VSONE_RATIO_CONFIG,
                            VSONE_SVER_CONFIG, assign_symmetric_matches,
                            assign_unconstrained_matches,
                            asymmetric_correspondence, csum, demodata_match,
                            empty_assign, empty_neighbors,
                            ensure_metadata_dlen_sqrd, ensure_metadata_feats,
                            ensure_metadata_flann, ensure_metadata_normxy,
                            ensure_metadata_vsone, flag_sym_slow,
                            flag_symmetric_matches, invsum,
                            normalized_nearest_neighbors,
                            symmetric_correspondence, testdata_annot_metadata,)
from vtool_ibeis.geometry import (bbox_center, bbox_from_center_wh, bbox_from_extent,
                            bbox_from_verts, bbox_from_xywh,
                            bboxes_from_vert_list, closest_point_on_bbox,
                            closest_point_on_line,
                            closest_point_on_line_segment,
                            closest_point_on_vert_segments,
                            cvt_bbox_xywh_to_pt1pt2, distance_to_lineseg,
                            draw_border, draw_verts, extent_from_bbox,
                            extent_from_verts, get_pointset_extent_wh,
                            get_pointset_extents, point_inside_bbox,
                            scale_bbox, scale_extents, scaled_verts_from_bbox,
                            scaled_verts_from_bbox_gen, union_extents,
                            verts_from_bbox, verts_list_from_bboxes_list,)
from vtool_ibeis.nearest_neighbors import (AnnoyWrapper, ann_flann_once,
                                     assign_to_centroids, flann_augment,
                                     flann_cache, flann_index_time_experiment,
                                     get_flann_cfgstr, get_flann_fpath,
                                     get_flann_params, get_flann_params_cfgstr,
                                     get_kdtree_flann_params, invertible_stack,
                                     test_annoy, test_cv2_flann, tune_flann,)
from vtool_ibeis.clustering2 import (AnnoyWraper, apply_grouping, apply_grouping_,
                               apply_grouping_iter, apply_grouping_iter2,
                               apply_jagged_grouping, example_binary,
                               find_duplicate_items, group_indices, groupby,
                               groupby_dict, groupby_gen, groupedzip,
                               invert_apply_grouping, invert_apply_grouping2,
                               invert_apply_grouping3, jagged_group,
                               plot_centroids, sorted_indices_ranges,
                               tune_flann2, uniform_sample_hypersphere,
                               unsupervised_multicut_labeling,)
from vtool_ibeis.other import (and_lists, argsort_groups, argsort_records,
                         assert_zipcompress, asserteq, atleast_3channels,
                         atleast_nd, atleast_shape,
                         calc_error_bars_from_sample,
                         calc_sample_from_error_bars, check_sift_validity,
                         clipnorm, colwise_operation, compare_implementations,
                         compare_matrix_columns, compare_matrix_to_rows,
                         componentwise_dot, compress2,
                         compute_ndarray_unique_rowids_unsafe,
                         compute_unique_arr_dataids, compute_unique_data_ids,
                         compute_unique_data_ids_,
                         compute_unique_integer_data_ids, ensure_rng,
                         ensure_shape, find_best_undirected_edge_indexes,
                         find_elbow_point, find_first_true_indices,
                         find_k_true_indicies, find_next_true_indices,
                         flag_intersection, fromiter_nd, get_covered_mask,
                         get_crop_slices, get_uncovered_mask,
                         get_undirected_edge_ids, grab_webcam_image,
                         greedy_setcover, inbounds, index_partition,
                         intersect1d_reduce, intersect2d_flags,
                         intersect2d_indices, intersect2d_numpy,
                         intersect2d_structured_numpy, iter_reduce_ufunc,
                         list_compress_, list_take_, make_video, make_video2,
                         median_abs_dev, mult_lists, multigroup_lookup,
                         multigroup_lookup_naive, nearest_point,
                         nonunique_row_flags, nonunique_row_indexes, norm01,
                         or_lists, pad_vstack, rebuild_partition,
                         rowwise_operation, safe_argmax, safe_cat, safe_div,
                         safe_extreme, safe_max, safe_min, safe_vstack,
                         significant_shape, structure_rows, take2,
                         take_col_per_row, to_undirected_edges, trytake,
                         unique_rows, unstructure_rows,
                         weighted_average_scoring, weighted_geometic_mean,
                         weighted_geometic_mean_unnormalized, zipcat,
                         zipcompress, zipcompress_safe, ziptake, zstar_value,)
from vtool_ibeis.numpy_utils import (atleast_nd, ensure_shape, fromiter_nd,
                               index_to_boolmask, iter_reduce_ufunc,
                               multiaxis_reduce, unique_row_indexes,)
from vtool_ibeis.confusion import (ConfusionMetrics, draw_precision_recall_curve,
                             draw_roc_curve, interact_roc_factory,
                             interpolate_precision_recall,
                             interpolate_replbounds, nan_to_num,
                             testdata_scores_labels,)
from vtool_ibeis.score_normalization import (ScoreNormVisualizeClass,
                                       ScoreNormalizer, check_unused_kwargs,
                                       estimate_pdf, find_clip_range,
                                       flatten_scores, get_left_area,
                                       get_right_area, inspect_pdfs,
                                       learn_score_normalization,
                                       normalize_scores, partition_scores,
                                       plot_postbayes_pdf, plot_prebayes_pdf,
                                       test_score_normalization,
                                       testdata_score_normalier,)
from vtool_ibeis.symbolic import (check_expr_eq, custom_sympy_attrs, evalprint,
                            symbolic_randcheck, sympy_latex_repr, sympy_mat,
                            sympy_numpy_repr,)
from vtool_ibeis.demodata import (DEFAULT_DTYPE, dummy_img, dummy_seed,
                            force_kpts_feasibility, get_dummy_dpts,
                            get_dummy_invV_mats, get_dummy_kpts,
                            get_dummy_kpts_pair, get_dummy_matching_kpts,
                            get_dummy_xy, get_kpts_dummy_img,
                            get_testdata_kpts, make_dummy_fm, perterb_kpts,
                            perterbed_grid_kpts, testdata_binary_scores,
                            testdata_dummy_matches, testdata_dummy_sift,
                            testdata_nonmonotonic, testdata_ratio_matches,)

__all__ = ['AnnotPairFeatInfo', 'AnnoyWraper', 'AnnoyWrapper', 'AssignTup',
           'ConfusionMetrics', 'DATETIMEORIGINAL_TAGID', 'DEFAULT_DTYPE',
           'EXIF_TAG_DATETIME', 'EXIF_TAG_GPS', 'EXIF_TAG_TO_TAGID',
           'GPSDATE_CODE', 'GPSINFO_CODE', 'GPSLATITUDEREF_CODE',
           'GPSLATITUDE_CODE', 'GPSLONGITUDEREF_CODE', 'GPSLONGITUDE_CODE',
           'GPSTIME_CODE', 'GPS_TAG_TO_GPSID', 'GRAVITY_THETA',
           'GaussianBlurInplace', 'HAVE_SVER_C_WRAPPER', 'INDEX_DTYPE',
           'KPTS_DTYPE', 'L1', 'L2', 'L2_root_sift', 'L2_sift', 'L2_sift_sqrd',
           'L2_sqrd', 'LINE_AA', 'LOC_DIMS', 'MatchingError',
           'NORM_CHIP_CONFIG', 'ORIENTATION_000', 'ORIENTATION_090',
           'ORIENTATION_180', 'ORIENTATION_270', 'ORIENTATION_CODE',
           'ORIENTATION_DICT', 'ORIENTATION_DICT_INVERSE',
           'ORIENTATION_ORDER_LIST', 'ORIENTATION_UNDEFINED', 'ORI_DIM',
           'PSEUDO_MAX_DIST', 'PSEUDO_MAX_DIST_SQRD',
           'PSEUDO_MAX_VEC_COMPONENT', 'PairwiseMatch', 'SCAX_DIM', 'SCAY_DIM',
           'SENSITIVITYTYPE_CODE', 'SHAPE_DIMS', 'SKEW_DIM', 'SUM_OPS',
           'SV_DTYPE', 'ScaleStrat', 'ScoreNormVisualizeClass',
           'ScoreNormalizer', 'TAU', 'TEMP_VEC_DTYPE', 'TRANSFORM_DTYPE',
           'VALID_DISTS', 'VERBOSE_SVER', 'VSONE_ASSIGN_CONFIG',
           'VSONE_DEFAULT_CONFIG', 'VSONE_FEAT_CONFIG', 'VSONE_PI_DICT',
           'VSONE_RATIO_CONFIG', 'VSONE_SVER_CONFIG', 'XDIM', 'YDIM',
           'adaptive_scale', 'add_homogenous_coordinate',
           'affine_around_mat3x3', 'affine_mat3x3',
           'affine_warp_around_center', 'and_lists', 'ann_flann_once',
           'apply_filter_funcs', 'apply_grouping', 'apply_grouping_',
           'apply_grouping_iter', 'apply_grouping_iter2',
           'apply_jagged_grouping', 'argsort_groups', 'argsort_records',
           'argsubextrema2', 'argsubmax', 'argsubmax2', 'argsubmaxima',
           'argsubmaxima2', 'argsubmin2', 'argsubminima2',
           'assert_zipcompress', 'asserteq', 'assign_symmetric_matches',
           'assign_to_centroids', 'assign_unconstrained_matches',
           'asymmetric_correspondence', 'atan2', 'atleast_3channels',
           'atleast_nd', 'atleast_nd', 'atleast_shape',
           'augment_2x2_with_translation', 'bar_L2_sift', 'bar_cos_sift',
           'bbox_center', 'bbox_from_center_wh', 'bbox_from_extent',
           'bbox_from_verts', 'bbox_from_xywh', 'bboxes_from_vert_list',
           'beaton_tukey_loss', 'beaton_tukey_weight', 'blend', 'blend_images',
           'blend_images_average', 'blend_images_average_stack',
           'blend_images_mult_average', 'blend_images_multiply',
           'breakup_equal_streak', 'build_affine_lstsqrs_Mx6',
           'build_lstsqrs_Mx9', 'calc_error_bars_from_sample',
           'calc_sample_from_error_bars', 'cast_split', 'check_exif_keys',
           'check_expr_eq', 'check_kpts_in_bounds', 'check_sift_validity',
           'check_unused_kwargs', 'chip', 'circular_distance', 'clipnorm',
           'clipwhite', 'clipwhite_ondisk', 'closest_point',
           'closest_point_on_bbox', 'closest_point_on_line',
           'closest_point_on_line_segment', 'closest_point_on_vert_segments',
           'clustering2', 'colwise_operation', 'combine_offset_lists',
           'compare_implementations', 'compare_matrix_columns',
           'compare_matrix_to_rows', 'componentwise_dot', 'compress2',
           'compute_affine', 'compute_chip', 'compute_distances',
           'compute_homog', 'compute_ndarray_unique_rowids_unsafe',
           'compute_unique_arr_dataids', 'compute_unique_data_ids',
           'compute_unique_data_ids_', 'compute_unique_integer_data_ids',
           'confusion', 'convert_colorspace', 'convert_degrees',
           'convert_image_list_colorspace', 'convert_kptsZ_to_kpts',
           'cos_sift', 'cosine_dist', 'crop_out_imgfill', 'csum',
           'custom_sympy_attrs', 'cvt_BGR2L', 'cvt_BGR2RGB',
           'cvt_bbox_xywh_to_pt1pt2', 'cyclic_distance',
           'decompose_Z_to_RV_mats2x2', 'decompose_Z_to_V_2x2',
           'decompose_Z_to_invV_2x2', 'decompose_Z_to_invV_mats2x2',
           'demodata', 'demodata_match', 'det_distance', 'det_ltri',
           'detect_opencv_keypoints', 'distance', 'distance_to_lineseg',
           'dot_ltri', 'draw_border', 'draw_kp_ori_steps',
           'draw_precision_recall_curve', 'draw_roc_curve', 'draw_text',
           'draw_verts', 'dummy_img', 'dummy_seed', 'ellipse',
           'embed_channels', 'embed_in_square_image', 'emd', 'empty_assign',
           'empty_neighbors', 'ensure_3channel', 'ensure_4channel',
           'ensure_alpha_channel', 'ensure_grayscale',
           'ensure_metadata_dlen_sqrd', 'ensure_metadata_feats',
           'ensure_metadata_flann', 'ensure_metadata_normxy',
           'ensure_metadata_vsone', 'ensure_monotone_decreasing',
           'ensure_monotone_increasing', 'ensure_monotone_strictly_decreasing',
           'ensure_monotone_strictly_increasing', 'ensure_rng', 'ensure_shape',
           'ensure_shape', 'eps', 'estimate_pdf', 'estimate_refined_transform',
           'evalprint', 'example_binary', 'exif', 'expand_kpts',
           'expand_scales', 'expand_subscales', 'extent_from_bbox',
           'extent_from_verts', 'extract_chip_from_gpath',
           'extract_chip_from_gpath_into_square', 'extract_chip_from_img',
           'extract_chip_into_square', 'extract_feature_from_patch',
           'extract_features', 'extrema_neighbors', 'features',
           'filterflags_valid_images', 'find_best_undirected_edge_indexes',
           'find_clip_range', 'find_dominant_kp_orientations',
           'find_duplicate_items', 'find_elbow_point',
           'find_first_true_indices', 'find_k_true_indicies',
           'find_kpts_direction', 'find_maxima', 'find_maxima_with_neighbors',
           'find_next_true_indices', 'find_patch_dominant_orientations',
           'find_pixel_value_index', 'flag_intersection', 'flag_sym_slow',
           'flag_symmetric_matches', 'flann_augment', 'flann_cache',
           'flann_index_time_experiment', 'flatten_invV_mats_to_kpts',
           'flatten_scores', 'force_kpts_feasibility', 'fromiter_nd',
           'fromiter_nd', 'gamma_adjust', 'gauss2d_pdf', 'gauss_func1d',
           'gauss_func1d_unnormalized', 'gauss_parzen_est',
           'gaussian_average_patch', 'gaussian_patch', 'gaussian_weight_patch',
           'generate_to_patch_transforms', 'geometry', 'get_RV_mats2x2',
           'get_RV_mats_3x3', 'get_V_mats', 'get_Z_mats', 'get_affine_inliers',
           'get_best_affine_inliers', 'get_best_affine_inliers_',
           'get_covered_mask', 'get_crop_slices', 'get_cross_patch',
           'get_dummy_dpts', 'get_dummy_invV_mats', 'get_dummy_kpts',
           'get_dummy_kpts_pair', 'get_dummy_matching_kpts', 'get_dummy_xy',
           'get_even_point_sample', 'get_exif_dict', 'get_exif_dict2',
           'get_exif_tagids', 'get_exist',
           'get_extract_features_default_params', 'get_extramargin_measures',
           'get_flann_cfgstr', 'get_flann_fpath', 'get_flann_params',
           'get_flann_params_cfgstr', 'get_grid_kpts', 'get_histinfo_str',
           'get_image_to_chip_transform', 'get_invVR_mats2x2',
           'get_invVR_mats3x3', 'get_invVR_mats_oris', 'get_invVR_mats_shape',
           'get_invVR_mats_sqrd_scale', 'get_invVR_mats_xys', 'get_invV_mats',
           'get_invV_mats2x2', 'get_invV_mats3x3', 'get_invVs',
           'get_kdtree_flann_params', 'get_kpts_dlen_sqrd',
           'get_kpts_dummy_img', 'get_kpts_eccentricity',
           'get_kpts_image_extent', 'get_kpts_strs', 'get_kpts_wh',
           'get_lat_lon', 'get_left_area', 'get_match_spatial_squared_error',
           'get_no_symbol', 'get_normalized_affine_inliers',
           'get_num_channels', 'get_ori_mats', 'get_ori_strs',
           'get_orientation', 'get_orientation_histogram',
           'get_orientation_str', 'get_oris', 'get_pixel_dist',
           'get_pointset_extent_wh', 'get_pointset_extents', 'get_right_area',
           'get_round_scaled_dsize', 'get_scale_factor',
           'get_scaled_size_with_dlen', 'get_scales', 'get_shape_strs',
           'get_size', 'get_sqrd_scales', 'get_star2_patch', 'get_star_patch',
           'get_stripe_patch', 'get_test_patch', 'get_testdata_kpts',
           'get_transforms_from_patch_image_kpts', 'get_uncovered_mask',
           'get_undirected_edge_ids', 'get_uneven_point_sample',
           'get_unixtime', 'get_unixtime_gps', 'get_unwarped_patch',
           'get_unwarped_patches', 'get_warped_patch', 'get_warped_patches',
           'get_xy_strs', 'get_xys', 'grab_webcam_image', 'gradient_fill',
           'gradient_magnitude', 'greedy_setcover', 'gridsearch_addWeighted',
           'gridsearch_chipextract', 'gridsearch_image_function',
           'group_consecutive', 'group_indices', 'groupby', 'groupby_dict',
           'groupby_gen', 'groupedzip', 'haversine', 'hist_argmaxima',
           'hist_argmaxima2', 'hist_edges_to_centers', 'hist_isect',
           'histogram', 'homogenous_circle_pts', 'iceil', 'image',
           'image_shared', 'imread', 'imread_remote_s3', 'imread_remote_url',
           'imwrite', 'imwrite_fallback', 'inbounds', 'index_partition',
           'index_to_boolmask', 'infer_vert', 'inspect_pdfs',
           'interact_roc_factory', 'intern_warp_single_patch',
           'interpolate_between', 'interpolate_maxima', 'interpolate_nans',
           'interpolate_peaks', 'interpolate_peaks2',
           'interpolate_precision_recall', 'interpolate_replbounds',
           'interpolate_submaxima', 'interpolated_histogram',
           'intersect1d_reduce', 'intersect2d_flags', 'intersect2d_indices',
           'intersect2d_numpy', 'intersect2d_structured_numpy', 'inv_ltri',
           'invert_apply_grouping', 'invert_apply_grouping2',
           'invert_apply_grouping3', 'invert_invV_mats', 'inverted_sift_patch',
           'invertible_stack', 'invsum', 'iround', 'iter_reduce_ufunc',
           'iter_reduce_ufunc', 'jagged_group', 'keypoint', 'kp_cpp_infostr',
           'kpts_docrepr', 'kpts_matrices', 'kpts_repr',
           'learn_score_normalization', 'linalg', 'linear_interpolation',
           'list_compress_', 'list_take_', 'logistic_01', 'logit',
           'make_channels_comparable', 'make_dummy_fm',
           'make_exif_dict_human_readable', 'make_test_image_keypoints',
           'make_video', 'make_video2', 'make_white_transparent', 'matching',
           'maxima_neighbors', 'maximum_parabola_point', 'median_abs_dev',
           'montage', 'mult_lists', 'multiaxis_reduce', 'multigroup_lookup',
           'multigroup_lookup_naive', 'nan_to_num', 'nearest_neighbors',
           'nearest_point', 'nearest_point', 'non_decreasing',
           'non_increasing', 'nonunique_row_flags', 'nonunique_row_indexes',
           'norm01', 'normalize', 'normalize_rows', 'normalize_scores',
           'normalized_nearest_neighbors', 'numpy_utils', 'offset_kpts',
           'open_image_size', 'open_pil_image', 'or_lists', 'ori_distance',
           'other', 'overlay_alpha_images', 'pad_image', 'pad_image_ondisk',
           'pad_vstack', 'padded_resize', 'parse_exif_unixtime',
           'parse_exif_unixtime_gps', 'partition_scores', 'patch',
           'patch_gaussian_weighted_average_intensities', 'patch_gradient',
           'patch_mag', 'patch_ori', 'pdist_argsort', 'pdist_indicies',
           'perlin_noise', 'perterb_kpts', 'perterbed_grid_kpts',
           'plot_centroids', 'plot_postbayes_pdf', 'plot_prebayes_pdf',
           'point_inside_bbox', 'print_image_checks', 'random_affine_args',
           'random_affine_transform', 'read_all_exif_tags', 'read_exif',
           'read_exif_tags', 'read_one_exif_tag', 'rebuild_partition',
           'rectify_invV_mats_are_up', 'rectify_to_float01',
           'rectify_to_square', 'rectify_to_uint8', 'refine_inliers',
           'remove_homogenous_coordinate', 'resize', 'resize_image_by_scale',
           'resize_mask', 'resize_thumb', 'resize_to_maxdims',
           'resize_to_maxdims_ondisk', 'resized_clamped_thumb_dims',
           'resized_dims_and_ratio', 'rotate_image', 'rotate_image_ondisk',
           'rotation_around_bbox_mat3x3', 'rotation_around_mat3x3',
           'rotation_mat2x2', 'rotation_mat3x3', 'rowwise_operation',
           'safe_argmax', 'safe_cat', 'safe_div', 'safe_extreme', 'safe_max',
           'safe_min', 'safe_pdist', 'safe_vstack', 'sample_ell_border_pts',
           'sample_ell_border_vals', 'sample_uniform', 'scale_around_mat3x3',
           'scale_bbox', 'scale_extents', 'scale_mat3x3',
           'scaled_verts_from_bbox', 'scaled_verts_from_bbox_gen',
           'score_normalization', 'shear', 'shear_mat3x3',
           'show_gaussian_patch', 'show_hist_submaxima', 'show_ori_image',
           'show_ori_image_ondisk', 'show_patch_orientation_estimation',
           'signed_cyclic_distance', 'signed_ori_distance',
           'significant_shape', 'sorted_indices_ranges',
           'spatial_verification', 'spatially_verify_kpts', 'stack_image_list',
           'stack_image_list_special', 'stack_image_recurse', 'stack_images',
           'stack_multi_images', 'stack_multi_images2', 'stack_square_images',
           'strictly_decreasing', 'strictly_increasing', 'structure_rows',
           'subbin_bounds', 'subpixel_values', 'subscale_peaks', 'svd',
           'symbolic', 'symbolic_randcheck', 'symmetric_correspondence',
           'sympy_latex_repr', 'sympy_mat', 'sympy_numpy_repr', 'take2',
           'take_col_per_row', 'test_affine_errors', 'test_annoy',
           'test_cv2_flann', 'test_homog_errors', 'test_language_modulus',
           'test_mser', 'test_ondisk_find_patch_fpath_dominant_orientations',
           'test_score_normalization', 'test_show_gaussian_patches',
           'test_show_gaussian_patches2', 'testdata_annot_metadata',
           'testdata_binary_scores', 'testdata_blend',
           'testdata_dummy_matches', 'testdata_dummy_sift', 'testdata_hist',
           'testdata_imglist', 'testdata_matching_affine_inliers',
           'testdata_matching_affine_inliers_normalized',
           'testdata_nonmonotonic', 'testdata_patch', 'testdata_ratio_matches',
           'testdata_score_normalier', 'testdata_scores_labels',
           'testdata_sift2', 'testshow_extramargin_info',
           'to_undirected_edges', 'transform_around', 'transform_kpts',
           'transform_kpts_to_imgspace', 'transform_kpts_xys',
           'transform_points_with_homography', 'translation_mat3x3', 'trig',
           'try_svd', 'trytake', 'tune_flann', 'tune_flann2',
           'understanding_pseudomax_props', 'uniform_sample_hypersphere',
           'union_extents', 'unique_row_indexes', 'unique_rows',
           'unnormalize_transform', 'unstructure_rows',
           'unsupervised_multicut_labeling', 'util_math', 'verts_from_bbox',
           'verts_list_from_bboxes_list', 'warpAffine', 'warpHomog',
           'weighted_average_scoring', 'weighted_geometic_mean',
           'weighted_geometic_mean_unnormalized', 'whiten_xy_points',
           'wrap_histogram', 'wrapped_distance', 'zipcat', 'zipcompress',
           'zipcompress_safe', 'ziptake', 'zstar_value']
