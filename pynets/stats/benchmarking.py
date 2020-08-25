#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 10:40:07 2017
Copyright (C) 2018
@authors: Derek Pisner
"""
from sklearn.metrics.pairwise import (
    cosine_distances,
    haversine_distances,
    manhattan_distances,
    euclidean_distances,
)
from sklearn.utils import check_X_y
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
import pandas as pd
import re
import glob
import dill
import numpy as np
import itertools
import warnings
from sklearn.preprocessing import StandardScaler
from pynets.stats.prediction import make_subject_dict, cleanNullTerms, \
    get_ensembles_top, build_grid

warnings.filterwarnings("ignore")


def build_hp_dict(file_renamed, modality, hyperparam_dict, hyperparams):
    """
    A function to build a hyperparameter dictionary by parsing a given
    file path.
    """

    for hyperparam in hyperparams:
        if (
            hyperparam != "smooth"
            and hyperparam != "hpass"
            and hyperparam != "track_type"
            and hyperparam != "directget"
            and hyperparam != "tol"
            and hyperparam != "minlength"
            and hyperparam != "samples"
            and hyperparam != "nodetype"
            and hyperparam != "template"

        ):
            if hyperparam not in hyperparam_dict.keys():
                hyperparam_dict[hyperparam] = [
                    file_renamed.split(hyperparam + "-")[1].split("_")[0]
                ]
            else:
                hyperparam_dict[hyperparam].append(
                    file_renamed.split(hyperparam + "-")[1].split("_")[0]
                )

    if modality == "func":
        if "smooth-" in file_renamed:
            if "smooth" not in hyperparam_dict.keys():
                hyperparam_dict["smooth"] = [file_renamed.split(
                    "smooth-")[1].split("_")[0].split("fwhm")[0]]
            else:
                hyperparam_dict["smooth"].append(
                    file_renamed.split("smooth-"
                                       )[1].split("_")[0].split("fwhm")[0])
            hyperparams.append("smooth")
        if "hpass-" in file_renamed:
            if "hpass" not in hyperparam_dict.keys():
                hyperparam_dict["hpass"] = [file_renamed.split(
                    "hpass-")[1].split("_")[0].split("Hz")[0]]
            else:
                hyperparam_dict["hpass"].append(
                    file_renamed.split("hpass-"
                                       )[1].split("_")[0].split("Hz")[0])
            hyperparams.append("hpass")
        if "extract-" in file_renamed:
            if "extract" not in hyperparam_dict.keys():
                hyperparam_dict["extract"] = [
                    file_renamed.split("extract-")[1].split("_")[0]
                ]
            else:
                hyperparam_dict["extract"].append(
                    file_renamed.split("extract-")[1].split("_")[0]
                )
            hyperparams.append("extract")

    elif modality == "dwi":
        if "directget-" in file_renamed:
            if "directget" not in hyperparam_dict.keys():
                hyperparam_dict["directget"] = [
                    file_renamed.split("directget-")[1].split("_")[0]
                ]
            else:
                hyperparam_dict["directget"].append(
                    file_renamed.split("directget-")[1].split("_")[0]
                )
            hyperparams.append("directget")
        if "minlength-" in file_renamed:
            if "minlength" not in hyperparam_dict.keys():
                hyperparam_dict["minlength"] = [
                    file_renamed.split("minlength-")[1].split("_")[0]
                ]
            else:
                hyperparam_dict["minlength"].append(
                    file_renamed.split("minlength-")[1].split("_")[0]
                )
            hyperparams.append("minlength")
        if "tol-" in file_renamed:
            if "tol" not in hyperparam_dict.keys():
                hyperparam_dict["tol"] = [
                    file_renamed.split("tol-")[1].split("_")[0]
                ]
            else:
                hyperparam_dict["tol"].append(
                    file_renamed.split("tol-")[1].split("_")[0]
                )
            hyperparams.append("tol")

    for key in hyperparam_dict:
        hyperparam_dict[key] = list(set(hyperparam_dict[key]))

    return hyperparam_dict, hyperparams


def discr_stat(
        X,
        Y,
        dissimilarity="euclidean",
        remove_isolates=True,
        return_rdfs=True):
    """
    Computes the discriminability statistic.

    Parameters
    ----------
    X : array, shape (n_samples, n_features) or (n_samples, n_samples)
        Input data. If dissimilarity=='precomputed', the input should be the
         dissimilarity matrix.
    Y : 1d-array, shape (n_samples)
        Input labels.
    dissimilarity : str, {"euclidean" (default), "precomputed"} Dissimilarity
        measure can be 'euclidean' (pairwise Euclidean distances between points
        in the dataset) or 'precomputed' (pre-computed dissimilarities).
    remove_isolates : bool, optional, default=True
        Whether to remove data that have single label.
    return_rdfs : bool, optional, default=False
        Whether to return rdf for all data points.

    Returns
    -------
    stat : float
        Discriminability statistic.
    rdfs : array, shape (n_samples, max{len(id)})
        Rdfs for each sample. Only returned if ``return_rdfs==True``.

    """
    check_X_y(X, Y, accept_sparse=True)

    uniques, counts = np.unique(Y, return_counts=True)
    if remove_isolates:
        idx = np.isin(Y, uniques[counts != 1])
        labels = Y[idx]

        if (
            dissimilarity == "euclidean"
            or dissimilarity == "cosine"
            or dissimilarity == "haversine"
            or dissimilarity == "manhattan"
            or dissimilarity == "mahalanobis"
        ):
            X = X[idx]
        else:
            X = X[np.ix_(idx, idx)]
    else:
        labels = Y

    if dissimilarity == "euclidean":
        dissimilarities = euclidean_distances(X)
    elif dissimilarity == "cosine":
        dissimilarities = cosine_distances(X)
    elif dissimilarity == "haversine":
        dissimilarities = haversine_distances(X)
    elif dissimilarity == "manhattan":
        dissimilarities = manhattan_distances(X)
    else:
        dissimilarities = X

    rdfs = _discr_rdf(dissimilarities, labels)
    rdfs[rdfs < 0.5] = np.nan
    stat = np.nanmean(rdfs)

    if return_rdfs:
        return stat, rdfs
    else:
        return stat


def _discr_rdf(dissimilarities, labels):
    """
    A function for computing the reliability density function of a dataset.

    Parameters
    ----------
    dissimilarities : array, shape (n_samples, n_features)
        Input data. If dissimilarity=='precomputed', the input should be the
        dissimilarity matrix.
    labels : 1d-array, shape (n_samples)
        Input labels.

    Returns
    -------
    out : array, shape (n_samples, max{len(id)})
        Rdfs for each sample. Only returned if ``return_rdfs==True``.

    """
    check_X_y(dissimilarities, labels, accept_sparse=True)
    rdfs = []

    for i, label in enumerate(labels):
        di = dissimilarities[i]

        # All other samples except its own label
        idx = labels == label
        Dij = di[~idx]

        # All samples except itself
        idx[i] = False
        Dii = di[idx]

        rdf = [1 - ((Dij < d).sum() + 0.5 * (Dij == d).sum()) /
               Dij.size for d in Dii]
        rdfs.append(rdf)

    out = np.full((len(rdfs), max(map(len, rdfs))), np.nan)
    for i, rdf in enumerate(rdfs):
        out[i, : len(rdf)] = rdf

    return out


def reshape_graphs(graphs):
    n, v1, v2 = np.shape(graphs)
    return np.reshape(graphs, (n, v1 * v2))


def CronbachAlpha(itemscores):
    itemscores = np.asarray([i for i in itemscores if np.nan not in i])
    itemvars = itemscores.var(axis=0, ddof=1)
    tscores = itemscores.sum(axis=1)
    nitems = itemscores.shape[1]
    try:
        calpha = (nitems / float(nitems - 1) *
                  (float(1 - itemvars.sum()) / float(tscores.var(ddof=1))))
    except:
        calpha = 0

    return calpha


if __name__ == "__main__":
    __spec__ = "ModuleSpec(name='builtins', loader=<class '_" \
               "frozen_importlib.BuiltinImporter'>)"
    base_dir = '/scratch/04171/dpisner/HNU/HNU_outs'
    thr_type = "MST"
    icc = True
    disc = True

    #embedding_types = ['topology']
    embedding_types = ['topology', 'OMNI', 'ASE']
    modalities = ['dwi', 'func']
    template = 'MNI152_T1'
    mets = ["global_efficiency", "average_clustering",
            "average_shortest_path_length", "average_local_efficiency_nodewise",
            "average_betweenness_centrality",
            "average_eigenvector_centrality"]

    hyperparams_func = ["rsn", "res", "model", 'hpass', 'extract', 'smooth']
    hyperparams_dwi = ["rsn", "res", "model", 'directget', 'minlength', 'tol']

    sessions = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']

    subject_dict, modality_grids = make_subject_dict(modalities, base_dir,
                                                     thr_type, mets,
                                                     embedding_types,
                                                     template,
                                                     sessions)
    sub_dict_clean = cleanNullTerms(subject_dict)

    subject_dict_file_path = f"{base_dir}/pynets_subject_dict.pkl"

    with open(subject_dict_file_path, 'wb') as f:
        dill.dump(sub_dict_clean, f)
    f.close()

    # with open(subject_dict_file_path, 'rb') as f:
    #     sub_dict_clean = dill.load(f)
    # f.close()

    rsns = ['SalVentAttnA', 'DefaultA', 'ContB']

    if icc is True and disc is False:
        df_summary = pd.DataFrame(columns=['grid', 'modality', 'embedding', 'icc'])
    elif icc is False and disc is True:
        df_summary = pd.DataFrame(columns=['grid', 'modality', 'embedding', 'discriminability'])
    elif icc is True and disc is True:
        df_summary = pd.DataFrame(columns=['grid', 'modality', 'embedding', 'discriminability', 'icc'])

    embedding_types = ['topology']
    modalities = ['dwi']
    for modality in modalities:
        hyperparams = eval(f"hyperparams_{modality}")
        hyperparam_dict = {}

        ensembles, df_top = get_ensembles_top(modality, thr_type,
                                              f"{base_dir}/pynets")

        grid = build_grid(modality, hyperparam_dict,
                          sorted(list(set(hyperparams))), ensembles)[1]

        for alg in embedding_types:
            ix = 0
            for comb in grid:
                if modality == 'func':
                    try:
                        extract, hpass, model, res, atlas, smooth = comb
                    except:
                        print(comb)
                        extract, hpass, model, res, atlas = comb
                        smooth = 0
                    comb_tuple = (atlas, extract, hpass, model, res, smooth)
                else:
                    try:
                        directget, minlength, model, res, atlas, tol = comb
                    except:
                        print(comb)
                        directget, minlength, model, res, atlas = comb
                    comb_tuple = (atlas, directget, minlength, model, res)

                df_summary.at[ix, "grid"] = comb_tuple
                df_summary.at[ix, "modality"] = modality
                df_summary.at[ix, "embedding"] = alg

                # icc
                if icc is True:
                    id_list = []
                    icc_list = []
                    for ID in sub_dict_clean.keys():
                        ses_list = []
                        for ses in sub_dict_clean[ID].keys():
                            id_list.append(ID)
                            ses_list.append(
                                sub_dict_clean[ID][ses][modality][comb_tuple][alg]
                            )
                        meas = np.hstack(ses_list)
                        if np.isnan(meas).all():
                            continue
                        else:
                            icc_out = CronbachAlpha(meas)
                            icc_list.append(icc_out)
                            df_summary.at[ix, "icc"] = np.nanmean(icc_list)
                            del icc_out, ses_list
                    del icc_list

                if disc is True:
                    id_list = []
                    vect_all = []
                    for ID in sub_dict_clean.keys():
                        vects = []
                        for ses in sub_dict_clean[ID].keys():
                            id_list.append(ID)
                            vects.append(
                                sub_dict_clean[ID][ses][modality][comb_tuple][alg]
                            )
                        vect_all.append(np.concatenate(vects, axis=1))
                        del vects
                    X_top = np.swapaxes(np.hstack(vect_all), 0, 1)
                    Y = np.array(id_list)
                    if np.isnan(X_top).all() or len(Y) < 3 or \
                        (np.unique(Y, return_counts=True)[1] != 1).all() == 1:
                        continue
                    else:
                        bad_ixs = [i[1] for i in np.argwhere(np.isnan(X_top))]
                        for m in set(bad_ixs):
                            if (X_top.shape[0] - bad_ixs.count(m)
                            ) / X_top.shape[0] < 0.50:
                                X_top = np.delete(X_top, m, axis=1)
                        imp = IterativeImputer(max_iter=50, random_state=42)
                        X_top = imp.fit_transform(X_top)
                        scaler = StandardScaler()
                        X_top = scaler.fit_transform(X_top)
                        discr_stat_val, rdf = discr_stat(X_top, Y)
                        df_summary.at[ix, "discriminability"] = discr_stat_val
                        print(discr_stat_val)
                        # print(rdf)
                        del discr_stat_val
                ix += 1

    if icc is True and disc is False:
        df_summary = df_summary.sort_values("icc", ascending=False)
        # df_summary = df_summary[df_summary.topological_icc >
        #                         df_summary.icc.quantile(.50)]
    elif icc is False and disc is True:
        df_summary = df_summary.sort_values(
            "discriminability", ascending=False)
        # df_summary = df_summary[df_summary.discriminability >
        #                         df_summary.discriminability.quantile(.50)]
    elif icc is True and disc is True:
        df_summary = df_summary.sort_values(
            by=["discriminability", "icc"], ascending=False
        )

    df_summary.to_csv(f"{base_dir}/{base_dir}/grid_clean.csv")
