﻿#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 27 16:19:14 2017

@authors: Derek Pisner & Ryan Hammonds

"""
import numpy as np
import time
try:
    import cPickle as pickle
except ImportError:
    import _pickle as pickle
from pathlib import Path
from pynets.core import thresholding
import networkx as nx


def test_binarize():
    """
    Test binarize functionality
    """
    base_dir = str(Path(__file__).parent/"examples")
    x = np.load(base_dir + '/002/fmri/002_Default_est_cov_raw_mat.npy')
    s = thresholding.binarize(thresholding.threshold_proportional(x, .41))
    assert np.sum(s) == 2.0


def test_normalize():
    """
    Test normalize functionality
    """
    base_dir = str(Path(__file__).parent/"examples")
    x = np.load(base_dir + '/002/fmri/002_Default_est_cov_raw_mat.npy')
    s = thresholding.normalize(thresholding.threshold_proportional(x, .79))
    assert np.max(s) <= 1
    assert np.min(s) >= 0


def test_threshold_absolute():
    """
    Test threshold_absolute functionality
    """
    base_dir = str(Path(__file__).parent/"examples")
    x = np.load(base_dir + '/002/fmri/002_Default_est_cov_raw_mat.npy')
    s = thresholding.threshold_absolute(x, 0.1)
    assert np.round(np.sum(s), 1) <= np.sum(x)


def test_invert():
    """
    Test invert functionality
    """
    base_dir = str(Path(__file__).parent/"examples")
    x = np.load(base_dir + '/002/fmri/002_Default_est_cov_raw_mat.npy')
    s = thresholding.invert(thresholding.threshold_proportional(x, .9))
    assert np.round(np.sum(s), 1) >= np.sum(x)


def test_autofix():
    """
    Test autofix functionality
    """
    base_dir = str(Path(__file__).parent/"examples")
    x = np.load(base_dir + '/002/fmri/002_Default_est_cov_raw_mat.npy')
    x[1][1] = np.inf
    x[2][1] = np.nan
    s = thresholding.autofix(x)
    assert (np.nan not in s) and (np.inf not in s)


def test_density_thresholding():
    """
    Test density_thresholding functionality
    """
    base_dir = str(Path(__file__).parent/"examples")
    x = np.genfromtxt(
        base_dir + '/002/fmri/whole_brain_cluster_labels_PCA200/002_est_sps_raw_mat.txt')
    l = thresholding.est_density((thresholding.density_thresholding(x, 0.01)))
    h = thresholding.est_density((thresholding.density_thresholding(x, 0.04)))
    assert np.equal(l, 0.009748743718592965)
    assert np.equal(h, 0.037487437185929645)


def test_est_density():
    """
    Test est_density functionality
    """
    base_dir = str(Path(__file__).parent/"examples")
    x = np.genfromtxt(
        base_dir + '/002/fmri/whole_brain_cluster_labels_PCA200/002_est_sps_raw_mat.txt')
    d = thresholding.est_density(x)
    assert np.round(d, 1) == 0.1


def test_thr2prob():
    """
    Test thr2prob functionality
    """
    base_dir = str(Path(__file__).parent/"examples")
    x = np.load(base_dir + '/002/fmri/002_Default_est_cov_raw_mat.npy')
    s = thresholding.normalize(x)
    s[0][0] = 0.0000001
    t = thresholding.thr2prob(s)
    assert float(len(t[np.logical_and(t < 0.001, t > 0)])) == float(0.0)


def test_thresh_func():
    """
    Test thresh_func functionality
    """
    base_dir = str(Path(__file__).parent/"examples")
    dir_path = base_dir + '/002/fmri'
    dens_thresh = False
    thr = 0.95
    smooth = 2
    c_boot = 3
    conn_matrix = np.random.rand(3, 3)
    conn_model = 'cov'
    network = 'Default'
    min_span_tree = False
    ID = '002'
    disp_filt = False
    roi = None
    parc = False
    node_size = 'TEST'
    hpass = 0.10
    prune = 1
    norm = 1
    binary = False
    atlas = 'whole_brain_cluster_labels_PCA200'
    uatlas = None
    labels_file_path = dir_path + '/whole_brain_cluster_labels_PCA200/Default_func_labelnames_wb.pkl'
    labels_file = open(labels_file_path, 'rb')
    labels = pickle.load(labels_file)
    coord_file_path = dir_path + '/whole_brain_cluster_labels_PCA200/Default_func_coords_wb.pkl'
    coord_file = open(coord_file_path, 'rb')
    coords = pickle.load(coord_file)

    start_time = time.time()
    [conn_matrix_thr, edge_threshold, est_path, _, _, _, _, _, _, _, _, _, _,
     _, _, _, _, _, _, _] = thresholding.thresh_func(dens_thresh, thr, conn_matrix, conn_model,
                                                     network, ID, dir_path, roi, node_size, min_span_tree, smooth, disp_filt,
                                                     parc, prune, atlas, uatlas, labels, coords, c_boot, norm, binary, hpass)
    print("%s%s%s" % ('thresh_and_fit (Functional, proportional thresholding) --> finished: ',
                      np.round(time.time() - start_time, 1), 's'))

    assert conn_matrix_thr is not None
    assert edge_threshold is not None
    assert est_path is not None


# def test_thresh_diff():
#     # Set example inputs
#     base_dir = str(Path(__file__).parent/"examples")
#
#     dir_path = base_dir + '/002/fmri'
#     dens_thresh = False
#     thr = 0.95
#     conn_matrix=np.random.rand(3,3)
#     conn_model = 'cov'
#     network = 'Default'
#     min_span_tree = False
#     ID = '997'
#     roi = None
#     node_size = 'parc'
#     parc = True
#     disp_filt = False
#     atlas = 'whole_brain_cluster_labels_PCA200'
#     uatlas = None
#     labels_file_path = dir_path + '/whole_brain_cluster_labels_PCA200/Default_func_labelnames_wb.pkl'
#     labels_file = open(labels_file_path, 'rb')
#     labels = pickle.load(labels_file)
#     coord_file_path = dir_path + '/whole_brain_cluster_labels_PCA200/Default_func_coords_wb.pkl'
#     coord_file = open(coord_file_path, 'rb')
#     coords = pickle.load(coord_file)
#
#     start_time = time.time()
#     [conn_matrix_thr, edge_threshold, est_path, _, _, _, _, _, _, _, _, _] = thresholding.thresh_diff(dens_thresh, thr, conn_model, network, ID, dir_path,
#     roi, node_size, conn_matrix, parc, min_span_tree, disp_filt, atlas,
#     uatlas, labels, coords)
#     print("%s%s%s" %
#     ('thresh_and_fit (Functional, density thresholding) --> finished: ',
#     str(np.round(time.time() - start_time, 1)), 's'))
#
#     assert conn_matrix_thr is not None
#     assert est_path is not None
#     assert edge_threshold is not None

def test_disparity_filter():
    """
    Test disparity_filter functionality
    """
    import random

    G = nx.gnm_random_graph(10, 10)
    for (u, v, w) in G.edges(data=True):
        w['weight'] = random.randint(0, 10)

    # Test undirected graphs
    N = thresholding.disparity_filter(G, weight='weight')

    assert N is not None


def test_disparity_filter_alpha_cut():
    """
    Test disparity_filter_alpha_cut functionality
    """
    import random

    G = nx.gnm_random_graph(10, 10)
    for (u, v, w) in G.edges(data=True):
        w['weight'] = random.randint(0, 10)

    # Test undirected graphs
    N = thresholding.disparity_filter_alpha_cut(G, weight='weight')

    assert N is not None


def test_knn():
    """
    Test knn functionality
    """
    # Generate connectivity matrix with 100 nodes and random weights
    conn_matrix = np.random.rand(100, 100)

    # NaN's across diagonal of connectivity matrix
    for idx, val in enumerate(conn_matrix):
        conn_matrix[idx][idx] = np.nan

    # Test range of nearest neighbors, k
    for k in range(1, 11):
        gra = thresholding.knn(conn_matrix, k)
        assert gra is not None


def test_local_thresholding_prop():
    """
    Test local_thresholding_prop functionality
    """
    # Generate connectivity matrix with 10 nodes and random weights
    conn_matrix = np.random.rand(10, 10)

    # NaN's across diagonal of connectivity matrix
    # Create list of coords = nodes
    coords = []
    labels = []
    for idx, val in enumerate(conn_matrix):
        conn_matrix[idx][idx] = np.nan
        coords.append(idx)
        labels.append('ROI_' + str(idx))

    # Test range of thresholds
    for val in range(0, 11):
        thr = round(val*0.1, 1)
        conn_matrix_thr = thresholding.local_thresholding_prop(conn_matrix, coords, labels, thr)
        assert conn_matrix_thr is not None


def test_weight_conversion():
    """
    Test weight_conversion functionality
    """
    # Note: wcm='Normalize' is listed as option in input but not implemented.

    # Generate connectivity matrix with 10 nodes and random weights
    W = np.random.rand(10, 10)

    # NaN's across diagonal of connectivity matrix
    for idx, val in enumerate(W):
        W[idx][idx] = np.nan

    # Cross test all wcm and copy combinations
    for wcm in ['binarize', 'lengths']:
        for copy in [True, False]:
            w = thresholding.weight_conversion(W, wcm, copy)
            assert w is not None


def test_weight_to_distance():
    """
    Test weight_to_distance functionality
    """
    # Generate connectivity matrix with 10 nodes and random weights
    conn_matrix = np.random.rand(10, 10)

    # NaN's across diagonal of connectivity matrix
    for idx, val in enumerate(conn_matrix):
        conn_matrix[idx][idx] = np.nan

    # Create graph using knn
    k = 10
    G = thresholding.knn(conn_matrix, k)
    G = nx.from_numpy_matrix(conn_matrix)

    g = thresholding.weight_to_distance(G)
    assert g is not None
