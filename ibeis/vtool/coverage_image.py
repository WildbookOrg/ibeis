from __future__ import absolute_import, division, print_function
from six.moves import zip, range, map  # NOQA
import cv2
import numpy as np
import utool as ut
from vtool import patch as ptool
from vtool import keypoint as ktool
print, print_,  printDBG, rrr, profile = ut.inject(__name__, '[cov]', DEBUG=False)


def show_coverage_map(chip, mask, patch, kpts, fnum=None, ell_alpha=.6,
                      show_mask_kpts=False):
    import plottool as pt
    masked_chip = (chip * mask[:, :, None]).astype(np.uint8)
    if fnum is None:
        fnum = pt.next_fnum()
    pnum_ = pt.get_pnum_func(nRows=2, nCols=2)
    pt.imshow((patch * 255).astype(np.uint8), fnum=fnum, pnum=pnum_(0), title='patch')
    #ut.embed()
    pt.imshow((mask * 255).astype(np.uint8), fnum=fnum, pnum=pnum_(1), title='mask')
    if show_mask_kpts:
        pt.draw_kpts2(kpts, rect=True, ell_alpha=ell_alpha)
    pt.imshow(chip, fnum=fnum, pnum=pnum_(2), title='chip')
    pt.draw_kpts2(kpts, rect=True, ell_alpha=ell_alpha)
    pt.imshow(masked_chip, fnum=fnum, pnum=pnum_(3), title='masked chip')
    #pt.draw_kpts2(kpts)


def iter_reduce_ufunc(ufunc, arr_iter):
    """ constant memory iteration and reduction """
    from six import next
    out = next(arr_iter).copy()
    for arr in arr_iter:
        ufunc(out, arr, out=out)
    return out


@profile
def warp_patch_into_kpts(kpts, patch, chip_shape, fx2_score=None,
                         scale_factor=1.0, mode='max', **kwargs):
    r"""
    Overlays the source image onto a destination image in each keypoint location

    Args:
        kpts (ndarray[float32_t, ndim=2]):  keypoints
        patch (ndarray): patch to warp (like gaussian)
        chip_shape (tuple):
        fx2_score (ndarray): score for every keypoint
        scale_factor (float):

    Returns:
        ndarray: mask

    CommandLine:
        python -m vtool.coverage_image --test-warp_patch_into_kpts
        python -m vtool.coverage_image --test-warp_patch_into_kpts --show
        python -m vtool.coverage_image --test-warp_patch_into_kpts --show --hole
        python -m vtool.coverage_image --test-warp_patch_into_kpts --show --square
        python -m vtool.coverage_image --test-warp_patch_into_kpts --show --square --hole

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool.coverage_image import *  # NOQA
        >>> import vtool as vt
        >>> import pyhesaff
        >>> img_fpath    = ut.grab_test_imgpath('carl.jpg')
        >>> (kpts, vecs) = pyhesaff.detect_kpts(img_fpath)
        >>> kpts = kpts[0:3]
        >>> chip = vt.imread(img_fpath)
        >>> kwargs = {}
        >>> chip_shape = chip.shape
        >>> fx2_score = np.ones(len(kpts))
        >>> scale_factor = 1.0
        >>> srcshape = (19, 19)
        >>> radius = srcshape[0] / 2.0
        >>> sigma = 0.4 * radius
        >>> SQUARE = ut.get_argflag('--square')
        >>> HOLE = ut.get_argflag('--hole')
        >>> if SQUARE:
        >>>     patch = np.ones(srcshape)
        >>> else:
        >>>     patch = ptool.gaussian_patch(shape=srcshape, sigma=sigma) #, norm_01=False)
        >>>     patch = patch / patch.max()
        >>> if HOLE:
        >>>     patch[int(patch.shape[0] / 2), int(patch.shape[1] / 2)] = 0
        >>> # execute function
        >>> dstimg = warp_patch_into_kpts(kpts, patch, chip_shape, fx2_score, scale_factor)
        >>> # verify results
        >>> print('dstimg stats %r' % (ut.get_stats_str(dstimg, axis=None)),)
        >>> print('patch stats %r' % (ut.get_stats_str(patch, axis=None)),)
        >>> #print(patch.sum())
        >>> assert np.all(ut.inbounds(dstimg, 0, 1, eq=True))
        >>> # show results
        >>> if ut.get_argflag('--show'):
        >>>     import plottool as pt
        >>>     mask = dstimg
        >>>     show_coverage_map(chip, mask, patch, kpts)
        >>>     pt.show_if_requested()
    """
    #if len(kpts) == 0:
    #    return None
    if fx2_score is None:
        fx2_score = np.ones(len(kpts))
    chip_scale_h = int(np.ceil(chip_shape[0] * scale_factor))
    chip_scale_w = int(np.ceil(chip_shape[1] * scale_factor))
    dsize = (chip_scale_w, chip_scale_h)
    shape = dsize[::-1]
    # Allocate destination image
    patch_shape = patch.shape
    # Scale keypoints into destination image
    M_list = ktool.get_transforms_from_patch_image_kpts(kpts, patch_shape, scale_factor)
    affmat_list = M_list[:, 0:2, :]
    # cv2 warpAffine flags
    USE_BIG_KEYPOINT_PENALTY = True
    def warped_patch_generator():
        """
        nested generator that warps the gaussian patches onto an image using
        constant memory.

        References:
          http://docs.opencv.org/modules/imgproc/doc/geometric_transformations.html#warpaffine
        """
        #warpAffine is weird. If the shape of the dst is the same as src we can
        #use the dst outvar. I dont know why it needs that.  It seems that this
        #will not operate in place even if a destination array is passed in when
        #src.shape != dst.shape.
        patch_h, patch_w = patch_shape
        # If we pad the patch we can use dst
        padded_patch = np.zeros(shape, dtype=np.float32)
        warped = np.zeros(shape, dtype=np.float32)
        # each score is spread across its contributing pixels
        for (M, score) in zip(affmat_list, fx2_score):
            np.multiply(patch, score, out=padded_patch[:patch.shape[0], :patch.shape[1]] )
            cv2.warpAffine(padded_patch, M, dsize, dst=warped,
                           flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                           borderValue=0)
            if USE_BIG_KEYPOINT_PENALTY:
                total_weight = np.sqrt(warped.sum()) * .1
                if total_weight > 1:
                    # Whatever the size of the keypoint is it should
                    # contribute a total of 1 score
                    np.divide(warped, total_weight, out=warped)
            yield warped
    # For each keypoint
    # warp a gaussian scaled by the feature score into the image
    # Either max or sum
    if mode == 'max':
        dstimg = iter_reduce_ufunc(np.maximum, warped_patch_generator())
        #for warped in warped_patch_generator():
        #    print(ut.get_resource_usage_str())
        #    np.maximum(dstimg, warped, out=dstimg)
        #    #np.maximum(warped, dstimg, out=dstimg)
        #    #dstimg = np.dstack((warped.T, dstimg)).max(axis=2)
    elif mode == 'sum':
        dstimg = iter_reduce_ufunc(np.add, warped_patch_generator())
        #dstimg = np.zeros(shape, dtype=np.float32)
        #for warped in warped_patch_generator():
        #    np.add(dstimg, warped, out=dstimg)
        # HACK FOR SUM: DO NOT DO THIS FOR MAX
        dstimg[dstimg > 1.0] = 1.0
    else:
        raise AssertionError('Unknown mode=%r' % (mode,))
    return dstimg


@profile
def make_coverage_mask(kpts, chip_shape, fx2_score=None, mode=None, **kwargs):
    r"""
    Returns a intensity image denoting which pixels are covered by the input
    keypoints

    Args:
        kpts (ndarray[float32_t, ndim=2][ndims=2]):  keypoints
        chip_shape (tuple):

    Returns:
        tuple (ndarray, ndarray): dstimg, patch

    CommandLine:
        python -m vtool.patch --test-test_show_gaussian_patches2 --show
        python -m vtool.coverage_image --test-make_coverage_mask --show
        python -m vtool.coverage_image --test-make_coverage_mask

    Example:
        >>> # ENABLE_DOCTEST
        >>> from vtool.coverage_image import *  # NOQA
        >>> import vtool as vt
        >>> import plottool as pt
        >>> import pyhesaff
        >>> #img_fpath = ut.grab_test_imgpath('carl.jpg')
        >>> img_fpath = ut.grab_test_imgpath('lena.png')
        >>> (kpts, vecs) = pyhesaff.detect_kpts(img_fpath)
        >>> kpts = kpts[::10]
        >>> chip = vt.imread(img_fpath)
        >>> kwargs = {}
        >>> chip_shape = chip.shape
        >>> # execute function
        >>> dstimg, patch = make_coverage_mask(kpts, chip_shape)
        >>> # show results
        >>> if ut.get_argflag('--show'):
        >>>     # FIXME:  params
        >>>     srcshape = (5, 5)
        >>>     sigma = 1.6
        >>>     #srcshape = (75, 75)
        >>>     mask = dstimg
        >>>     show_coverage_map(chip, mask, patch, kpts)
        >>>     pt.show_if_requested()
    """
    #srcshape = (7, 7)
    #srcshape = (3, 3)
    #srcshape = (5, 5)
    srcshape = (19, 19)
    #sigma = 1.6
    # Perdoch uses roughly .95 of the radius
    USE_PERDOCH_VALS = True
    if USE_PERDOCH_VALS:
        radius = srcshape[0] / 2.0
        sigma = 0.3 * radius
        #sigma = 0.2 * radius
        #sigma = 0.95 * radius
    #srcshape = (75, 75)
    # Similar to SIFT's computeCircularGaussMask in helpers.cpp
    # uses smmWindowSize=19 in hesaff for patch size. and 1.6 for sigma
    # Create gaussian image to warp
    patch = ptool.gaussian_patch(shape=srcshape, sigma=sigma)
    norm_01 = True
    if mode is None:
        mode = 'max'
    if norm_01:
        patch /= patch.max()
    scale_factor = .25
    dstimg = warp_patch_into_kpts(kpts, patch, chip_shape, mode=mode,
                                  fx2_score=fx2_score, scale_factor=scale_factor,
                                  **kwargs)
    cv2.GaussianBlur(dstimg, ksize=(17, 17,), sigmaX=5.0, sigmaY=5.0,
                     dst=dstimg, borderType=cv2.BORDER_CONSTANT)
    dsize = tuple(chip_shape[0:2][::-1])
    dstimg = cv2.resize(dstimg, dsize)
    #print(dstimg)
    return dstimg, patch


if __name__ == '__main__':
    """
    CommandLine:
        python -m vtool.coverage_image
        python -m vtool.coverage_image --allexamples
        python -m vtool.coverage_image --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
