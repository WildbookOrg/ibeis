#!/usr/bin/env python2.7
from __future__ import absolute_import, division, print_function
import utool
import pyflann
import numpy as np
from numpy.random import randint
(print, print_, printDBG, rrr, profile) = utool.inject(
    __name__, '[test_pyflann]', DEBUG=False)

"""
remove_points does not currently have bindings
nn_radius has incorrect binindgs

class FLANN:
   __del__(self)
   __init__(self, **kwargs)

   build_index(self, pts, **kwargs)
   delete_index(self, **kwargs)
   add_points(self, pts, rebuild_threshold=2)

   hierarchical_kmeans(self, pts, branch_size, num_branches,
                       max_iterations=None, dtype=None, **kwargs)
   kmeans(self, pts, num_clusters, max_iterations=None, dtype=None, **kwargs)

   nn(self, pts, qpts, num_neighbors=1, **kwargs)
   nn_index(self, qpts, num_neighbors=1, **kwargs)
   nn_radius(self, qpts, radius, **kwargs)

   save_index(self, filename)
   load_index(self, filename, pts)

# in c++ but missing from python docs
removePoint(size_t, point_id)



# Look at /flann/algorithms/dist.h for distance clases

distance_translation = {
    "euclidean"        : 1,
    "manhattan"        : 2,
    "minkowski"        : 3,
    "max_dist"         : 4,
    "hik"              : 5,
    "hellinger"        : 6,
    "chi_square"       : 7,
    "cs"               : 7,
    "kullback_leibler" : 8,
    "kl"               : 8,
    "hamming"          : 9,
    "hamming_lut"      : 10,
    "hamming_popcnt"   : 11,
    "l2_simple"        : 12,
    }

# MAKE SURE YOU EDIT index.py in pyflann
flann_algos = {
    'linear'        : 0,
    'kdtree'        : 1,
    'kmeans'        : 2,
    'composite'     : 3,
    'kdtree_single' : 4,
    'hierarchical'  : 5,
    'lsh'           : 6, # locality sensitive hashing
    'kdtree_cuda'   : 7,
    'saved'         : 254, # dont use
    'autotuned'     : 255,
    }

multikey_dists = {
    #
    # Huristic distances
    ('euclidian', 'l2')        :  1,
    ('manhattan', 'l1')        :  2,
    ('minkowski', 'lp')        :  3, # order=p: lp could be l1, l2, l3, ...
    ('max_dist' , 'linf')      :  4,
    ('hellinger')              :  6,
    ('l2_simple')              : 12, # For low dimensional points
    #
    # Nonparametric test statistics
    ('hik','histintersect')    :  5,
    ('chi_square', 'cs')       :  7,
    #
    # Information-thoery divergences
    ('kullback_leibler', 'kl') :  8,
    ('hamming')                :  9, # xor and bitwise sum
    ('hamming_lut')            : 10, # xor (sums with lookup table;if nosse2)
    ('hamming_popcnt')         : 11, # population count (number of 1 bits)
    }

#Hamming distance functor - counts the bit differences between two strings -
#useful for the Brief descriptor
#bit count of A exclusive XOR'ed with B


pyflann.set_distance_type('hellinger', order=0)
"""


def _make_pts(nPts=53, nDims=11, dtype=np.float64):
    pts = np.array(randint(0, 255, (nPts, nDims)), dtype=dtype)
    return pts


def test_pyflann_hkmeans():
    """
    hkmeans
    Clusters the data by using multiple runs of kmeans to
    recursively partition the dataset.  The number of resulting
    clusters is given by (branch_size-1)*num_branches+1.
    This method can be significantly faster when the number of
    desired clusters is quite large (e.g. a hundred or more).
    Higher branch sizes are slower but may give better results.
    If dtype is None (the default), the array returned is the same
    type as pts.  Otherwise, the returned array is of type dtype.

    #>>> from vtool.tests.test_pyflann import * # NOQA
    #>>> test_pyflann_hkmeans()  #doctest: +ELLIPSIS
    #HKmeans...
    """

    # Test parameters
    flann = pyflann.FLANN()

    branch_size = 5
    num_branches = 7
    print('HKmeans')
    pts = _make_pts(nPts=1009)
    hkmean_centroids = flann.hierarchical_kmeans(pts, branch_size, num_branches,
                                                 max_iterations=1000, dtype=None)
    print(utool.truncate_str(str(hkmean_centroids)))
    print('hkmean_centroids.shape = %r' % (hkmean_centroids.shape,))
    nHKMeansCentroids = (branch_size - 1) * num_branches + 1
    target_shape = (nHKMeansCentroids, pts.shape[1])
    test_shape = hkmean_centroids.shape
    assert test_shape == target_shape, repr(test_shape) + ' != ' + repr(target_shape)


def test_pyflann_kmeans():
    """
    kmeans(self, pts, num_clusters, max_iterations=None, dtype=None, **kwargs)
        Runs kmeans on pts with num_clusters centroids.  Returns a
        numpy array of size num_clusters x dim.
        If max_iterations is not None, the algorithm terminates after
        the given number of iterations regardless of convergence.  The
        default is to run until convergence.
        If dtype is None (the default), the array returned is the same
        type as pts.  Otherwise, the returned array is of type dtype.
    #>>> from vtool.tests.test_pyflann import * # NOQA
    #>>> test_pyflann_kmeans()  #doctest: +ELLIPSIS
    #Kmeans...
    """
    print('Kmeans')
    flann = pyflann.FLANN()
    num_clusters = 7
    pts = _make_pts(nPts=1009)
    kmeans_centroids = flann.kmeans(pts, num_clusters, max_iterations=None,
                                    dtype=None)
    print(utool.truncate_str(str(kmeans_centroids)))
    print('kmeans_centroids.shape = %r' % (kmeans_centroids.shape,))
    target_shape = (num_clusters, pts.shape[1])
    test_shape = kmeans_centroids.shape
    assert test_shape == target_shape, repr(test_shape) + ' != ' + repr(target_shape)


def test_pyflann_add_point():
    """
    #>>> from vtool.tests.test_pyflann import * # NOQA
    #>>> test_pyflann_add_point()
    """
    # Test parameters
    num_neighbors = 3
    pts = _make_pts(nPts=1009)
    qpts = _make_pts(nPts=7)
    newpts = _make_pts(nPts=1013)

    # build index
    print('Build Index')
    flann = pyflann.FLANN()
    _build_params = flann.build_index(pts)
    print(_build_params)

    print('NN_Index')
    indicies1, dists1 = flann.nn_index(qpts, num_neighbors=num_neighbors)
    print(utool.hz_str('indicies1, dists1 = ', indicies1,  dists1))

    print('Adding points')
    flann.add_points(newpts, rebuild_threshold=2)

    print('NN_Index')
    indicies2, dists2 = flann.nn_index(qpts, num_neighbors=num_neighbors)
    print(utool.hz_str('indicies2, dists2 = ', indicies2,  dists2))


def test_pyflann_searches():
    """
    #>>> from vtool.tests.test_pyflann import * # NOQA
    #>>> test_pyflann_searches()
    """
    try:
        num_neighbors = 3
        pts = _make_pts(nPts=5743, nDims=2)
        qpts = _make_pts(nPts=7, nDims=2)
        from vtool import linalg
        # sample a radius
        radius = linalg.L2(pts[0:1], qpts[0:1])[0] * 2 + 1

        flann = pyflann.FLANN()

        print('NN_OnTheFly')
        # build nn_index on the fly
        indicies1, dists1 = flann.nn(pts, qpts, num_neighbors, algorithm='hierarchical')
        print(utool.hz_str('indicies1, dists1 = ', indicies1,  dists1))

        _build_params = flann.build_index(pts, algorithm='kmeans')
        del _build_params

        print('NN_Index')
        indicies2, dists2 = flann.nn_index(qpts, num_neighbors=num_neighbors)
        print(utool.hz_str('indicies2, dists2 = ', indicies2,  dists2))

        # this can only be called on one query point at a time
        # because the output size is unknown
        print('NN_Radius, radius=%r' % (radius,))
        indicies3, dists3  = flann.nn_radius(pts[0], radius)
        print('indicies3 = %r ' % (indicies3,))
        print('dists3 = %r ' % (dists3,))

        assert np.all(dists3 < radius)
    except Exception as ex:
        utool.printex(ex, key_list=[
            'query',
            'query.shape',
            'pts.shape',
        ], separate=True)
        #utool.embed()
        raise


def test_pyflann_tune():
    """
    #>>> from vtool.tests.test_pyflann import * # NOQA
    #>>> test_pyflann_tune()
    """
    print('Create random qpts and database data')
    pts = _make_pts(nPts=1009)
    qpts = _make_pts(nPts=7)
    num_neighbors = 3
    #num_data = len(data)
    # untuned query

    flann = pyflann.FLANN()
    index_untuned, dist_untuned = flann.nn(pts, qpts, num_neighbors)

    # tuned query
    flannkw = dict(
        algorithm='autotuned',
        target_precision=.01,
        build_weight=0.01,
        memory_weight=0.0,
        sample_fraction=0.001
    )
    flann_tuned = pyflann.FLANN()
    tuned_params = flann_tuned.build_index(pts, **flannkw)
    index_tuned, dist_tuned = flann_tuned.nn_index(qpts, num_neighbors=num_neighbors)

    print(utool.hz_str('index_tuned, dist_tuned     = ', index_tuned,  dist_tuned))
    print('')
    print(utool.hz_str('index_untuned, dist_untuned = ', index_untuned,  dist_untuned))

    print(dist_untuned >= dist_tuned)

    return tuned_params


def test_pyflann_io():
    # Test parameters
    """
    #>>> from vtool.tests.test_pyflann import * # NOQA
    #>>> test_pyflann_io()
    """
    # Create qpts and database data
    print('Create random qpts and database data')
    num_neighbors = 3
    pts = _make_pts(nPts=1009)
    qpts = _make_pts(nPts=31)

    # Create flann object
    print('Create flann object')
    flann = pyflann.FLANN()

    # Build kd-tree index over the data
    print('Build the kd tree')
    _build_params = flann.build_index(pts)  # noqa

    # Find the closest few points to num_neighbors
    print('Find nn_index nearest neighbors')
    indicies1, dists1 = flann.nn_index(qpts, num_neighbors=num_neighbors)

    # Save the data to disk
    print('Save the data to the disk')
    np.savez('test_pyflann_ptsdata.npz', pts)
    npload_pts = np.load('test_pyflann_ptsdata.npz')
    pts2 = npload_pts['arr_0']

    print('Save and delete the FLANN index')
    flann.save_index('test_pyflann_index.flann')
    flann.delete_index()

    print('Reload the data')
    flann2 = pyflann.FLANN()
    flann2.load_index('test_pyflann_index.flann', pts2)
    indicies2, dists2 = flann2.nn_index(qpts, num_neighbors=num_neighbors)
    #print(utool.hz_str('indicies2, dists2 = ', indicies2,  dists2))

    print('Find the same nearest neighbors?')

    if np.all(indicies1 == indicies2) and np.all(dists1 == dists2):
        print('...data is the same! SUCCESS!')
    else:
        raise AssertionError('...data is the different! FAILURE!')


if __name__ == '__main__':
    """
    build_index(self, pts, **kwargs) method of pyflann.index.FLANN instance
        This builds and internally stores an index to be used for
        future nearest neighbor matchings.  It erases any previously
        stored indexes, so use multiple instances of this class to
        work with multiple stored indices.  Use nn_index(...) to find
        the nearest neighbors in this index.

        pts is a 2d numpy array or matrix. All the computation is done
        in float32 type, but pts may be any type that is convertable
        to float32.

    delete_index(self, **kwargs) method of pyflann.index.FLANN instance
        Deletes the current index freeing all the momory it uses.
        The memory used by the dataset that was indexed is not freed.

    """
    np.random.seed(1)
    tests = [
        test_pyflann_io,
        test_pyflann_hkmeans,
        test_pyflann_kmeans,
        test_pyflann_add_point,
        test_pyflann_searches,
        test_pyflann_tune,
    ]
    passed = 0
    for test in tests:
        passed += not (False is utool.run_test(test))
    print('%d/%d passed in test_pyflann' % (passed, len(tests)))
