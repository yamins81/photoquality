import os
import cPickle
import itertools
import functools
import re
import copy
import json
import urllib
import numpy as np
import scipy.io as io
import Image
import ImageOps
import tables as tbl
import tabular as tb
import time
from yamutils.fast import reorder_to

# (NOTE) Use this version: https://github.com/yamins81/scikit-data
import skdata.larray as larray
from skdata.data_home import get_data_home
from skdata.utils.download_and_extract import download_boto, extract

from . import utils
from . import classifier


class TechRehearsalImages(object):

    name = 'TechRehearsal'

    S3_ARCHIVES = []

    S3_FILES = []


    def __init__(self):
        pass

    def home(self, *suffix_paths):
        return os.path.join(get_data_home(), self.name, *suffix_paths)

    def download_image(self):
        pass

    @property
    def meta(self):
        if not hasattr(self, '_meta'):
            self.fetch()
            self._meta = self._get_meta()
        return self._meta

    @property
    def filenames(self):
        return self.meta['filename']

    def _get_meta(self):

        return meta

    def get_images(self, preproc):
        pass

    def get_category_splits(self, *args, **kwargs):
        return get_category_splits(self.meta, *args, **kwargs)

    def get_subset_splits(self, *args, **kwargs):
        return get_subset_splits(self.meta, *args, **kwargs)

    def get_splits(self, *args, **kwargs):
        return get_splits(self.meta, *args, **kwargs)

    @property
    def categories(self):
        return np.unique(self.meta['category'])
        
    @property
    def human_dissimilarity(self):
        path = self.home('kriegeskorte_hvm', 'RDM_hIT_fig1.txt')
        return np.array(map(lambda x: map(float, x.strip().split('  ')),
                             open(path, 'rU').readlines()))

    @property
    def monkey_dissimilarity(self):
        path = self.home('kriegeskorte_hvm', 'RDM_mIT_fig1.txt')
        return np.array(map(lambda x: map(float, x.strip().split('  ')),
                             open(path, 'rU').readlines()))


def get_category_splits(meta, npc_train, npc_tests, num_splits,
                        train_q=None, test_qs=None, test_names=None, npc_validate=0):
    catfunc = lambda x: x['category']
    return get_subset_splits(meta, npc_train, npc_tests, num_splits,
                             catfunc, train_q=train_q, test_qs=test_qs,
                             test_names=test_names,
                             npc_validate=npc_validate)


def get_splits(meta, ntrain, ntests, num_splits, train_q=None, test_qs=None, test_names=None, nvalidate=0):
    catfunc = lambda x : True
    return get_subset_splits(meta,
                             npc_train=ntrain,
                             npc_tests=ntests,
                             num_splits=num_splits,
                             catfunc=catfunc,
                             train_q=train_q,
                             test_qs=test_qs,
                             test_names=test_names,
                             npc_validate=nvalidate)


def get_subset_splits(meta, npc_train, npc_tests, num_splits,
                      catfunc, train_q=None, test_qs=None, test_names=None, npc_validate=0):
    train_inds = np.arange(len(meta)).astype(np.int)
    if test_qs is None:
        test_qs = [test_qs]
    if test_names is None:
        assert len(test_qs) == 1
        test_names = ['test']
    else:
        assert len(test_names) == len(test_qs)
        assert 'train' not in test_names
    test_ind_list = [np.arange(len(meta)).astype(np.int) for _ in range(len(test_qs))]
    if train_q is not None:
        sub = np.array(map(train_q, meta)).astype(np.bool)
        train_inds = train_inds[sub]
    for _ind, test_q in enumerate(test_qs):
        if test_q is not None:
             sub = np.array(map(test_q, meta)).astype(np.bool)
             test_ind_list[_ind] = test_ind_list[_ind][sub]

    all_test_inds = list(itertools.chain(*test_ind_list))
    all_inds = np.sort(np.unique(train_inds.tolist() + all_test_inds))
    categories = np.array(map(catfunc, meta))
    ucategories = np.unique(categories[all_inds]) 
    utestcategorylist = [np.unique(categories[_t]) for _t in test_ind_list]
    utraincategories = np.unique(categories[train_inds])
    rng = np.random.RandomState(0)  #or do you want control over the seed?
    splits = [dict([('train', [])] + [(tn, []) for tn in test_names]) for _ in range(num_splits)]
    validations = [[] for _ in range(len(test_qs))]
    for cat in ucategories:
        cat_validates = []
        ctils = []
        for _ind, test_inds in enumerate(test_ind_list):
            cat_test_inds = test_inds[categories[test_inds] == cat]
            ctils.append(len(cat_test_inds))
            if npc_validate > 0:
                assert len(cat_test_inds) >= npc_validate, 'not enough to validate'
                pv = rng.permutation(len(cat_test_inds))
                cat_validate = cat_test_inds[pv[:npc_validate]]
                validations[_ind] += cat_validate.tolist()
            else:
                cat_validate = []
            cat_validates.extend(cat_validate)
        cat_validates = np.sort(np.unique(cat_validates))
        for split_ind in range(num_splits):
            cat_train_inds = train_inds[categories[train_inds] == cat]
            if len(cat_train_inds) < np.mean(ctils):
                cat_train_inds = train_inds[categories[train_inds] == cat]
                cat_train_inds = np.array(list(set(cat_train_inds).difference(cat_validates)))
                if cat in utraincategories:
                    assert len(cat_train_inds) >= npc_train, 'not enough train for %s, %d, %d' % (cat, len(cat_train_inds), npc_train)
                cat_train_inds.sort()
                p = rng.permutation(len(cat_train_inds))
                cat_train_inds_split = cat_train_inds[p[:npc_train]]
                splits[split_ind]['train'] += cat_train_inds_split.tolist()
                for _ind, (test_inds, utc) in enumerate(zip(test_ind_list, utestcategorylist)):
                    npc_test = npc_tests[_ind]
                    cat_test_inds = test_inds[categories[test_inds] == cat]
                    cat_test_inds_c = np.array(list(
                             set(cat_test_inds).difference(cat_train_inds_split).difference(cat_validates)))
                    if cat in utc:
                        assert len(cat_test_inds_c) >= npc_test, 'not enough test for %s %d %d' % (cat, len(cat_test_inds_c), npc_test)
                    p = rng.permutation(len(cat_test_inds_c))
                    cat_test_inds_split = cat_test_inds_c[p[: npc_test]]
                    name = test_names[_ind]
                    splits[split_ind][name] += cat_test_inds_split.tolist()
            else:
                all_cat_test_inds = []
                for _ind, (test_inds, utc) in enumerate(zip(test_ind_list, utestcategorylist)):
                    npc_test = npc_tests[_ind]
                    cat_test_inds = test_inds[categories[test_inds] == cat]
                    cat_test_inds_c = np.sort(np.array(list(
                             set(cat_test_inds).difference(cat_validates))))
                    if cat in utc:
                        assert len(cat_test_inds_c) >= npc_test, 'not enough test for %s %d %d' % (cat, len(cat_test_inds_c), npc_test)
                    p = rng.permutation(len(cat_test_inds_c))
                    cat_test_inds_split = cat_test_inds_c[p[: npc_test]]
                    name = test_names[_ind]
                    splits[split_ind][name] += cat_test_inds_split.tolist()
                    all_cat_test_inds.extend(cat_test_inds_split)
                cat_train_inds = np.array(list(set(cat_train_inds).difference(all_cat_test_inds).difference(cat_validates)))
                if cat in utraincategories:
                    assert len(cat_train_inds) >= npc_train, 'not enough train for %s, %d, %d' % (cat, len(cat_train_inds), npc_train)
                cat_train_inds.sort()
                p = rng.permutation(len(cat_train_inds))
                cat_train_inds_split = cat_train_inds[p[:npc_train]]
                splits[split_ind]['train'] += cat_train_inds_split.tolist()

    return splits, validations


class ImgLoaderResizer(object):
    """
    """
    def __init__(self,
                 inshape,
                 shape=None,
                 ndim=None,
                 dtype='float32',
                 normalize=True,
                 mode='L'
                 ):
        self.inshape = inshape
        shape = tuple(shape)
        self._shape = shape
        if ndim is None:
            self._ndim = None if (shape is None) else len(shape)
        else:
            self._ndim = ndim
        self._dtype = dtype
        self.normalize = normalize
        self.mode = mode

    def rval_getattr(self, attr, objs):
        if attr == 'shape' and self._shape is not None:
            return self._shape
        if attr == 'ndim' and self._ndim is not None:
            return self._ndim
        if attr == 'dtype':
            return self._dtype
        raise AttributeError(attr)

    def __call__(self, file_path):
        im = Image.open(file_path)
        if im.mode != self.mode:
            im = im.convert(self.mode)
        assert im.size == self.inshape[:2]
        if max(im.size) != self._shape[0]:
            m = self._shape[0]/float(max(im.size))
            new_shape = (int(round(im.size[0]*m)), int(round(im.size[1]*m)))
            im = im.resize(new_shape, Image.ANTIALIAS)
        rval = np.asarray(im, self._dtype)
        if self.normalize:
            rval -= rval.mean()
            rval /= max(rval.std(), 1e-3)
        else:
            if 'float' in str(self._dtype):
                rval /= 255.0
        assert rval.shape == self._shape
        return rval

