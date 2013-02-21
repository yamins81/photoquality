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

import boto

class TechRehearsalImages(object):

    name = 'TechRehearsal'

    S3_ARCHIVES = []

    S3_FILES = []

    insize = (4256, 2832)

    def __init__(self, credentials=None):
        if credentials is None:
            self.conn = boto.connect_s3()
        else:
            self.conn = boto.connect_s3(*credentials)
        self.bucket = self.conn.get_bucket('pics-from-sam')
        resource_home  = self.home('resources')
        if not os.path.exists(resource_home):
            os.makedirs(resource_home)

    def home(self, *suffix_paths):
        return os.path.join(get_data_home(), self.name, *suffix_paths)

    def download_image(self):
        pass
        
    def fetch(self):
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
        L = filter(lambda x: x.name.startswith('Tech Rehearsal/') and x.name.endswith('.JPG'), 
                   list(self.bucket.list()))
        tr_orientations = cPickle.loads(self.bucket.get_key('tr_orientations.pkl').get_contents_as_string())
        
        recs = []
        for l in L:
            ls = l.name.split('/')
            if len(ls) == 4:
                _, event, sam_rank, fname = l.name.split('/')
                sam_rank = sam_rank.lower()
            else:
                _, event, fname = l.name.split('/')
                sam_rank = 'good'
            sname = '/'.join(l.name.split('/')[1:])
            orientation = tr_orientations.get(sname, '-')
            recs.append((event, sam_rank, fname, l.name, orientation))
        
        meta = tb.tabarray(records=recs, names=['event', 'sam_rank', 'name', 'filename', 'orientation'])
        return meta

    def get_images(self, preproc):
        dtype = preproc['dtype']
        mode = preproc['mode']
        size = tuple(preproc['size'])
        normalize = preproc['normalize']
        resource_home = self.home('resources')
        return larray.lmap(ImgDownloaderResizer(resource_home,
                                            self.bucket, 
                                            inshape=self.insize,
                                            shape=size,
                                            dtype=dtype,
                                            normalize=normalize,
                                            mode=mode),
                                self.filenames)


    def get_subset_splits(self, *args, **kwargs):
        return get_subset_splits(self.meta, *args, **kwargs)

    def get_splits(self, *args, **kwargs):
        return get_splits(self.meta, *args, **kwargs)

    def get_subsets(self, k):
        meta = self.meta
        events = np.unique(meta['event'])
        subset_d = {}
        for e in events:
            m = meta[meta['event'] == e]
            n = len(m)
            filenames = m['filename']
            subsets = []
            for ind in range(n):
                p = np.random.RandomState(seed=ind).permutation(n)[:k]
                subsets.append(filenames[p].tolist())
            subset_d[e] = subsets
        return subset_d


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


class ImgDownloaderResizer(object):
    """
    """
    def __init__(self,
                 download_dir,
                 bucket,
                 inshape,
                 shape=None,
                 ndim=None,
                 dtype='float32',
                 normalize=True,
                 mode='L'
                 ):
        self.download_dir = download_dir
        self.bucket = bucket
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
        lpath = os.path.join(self.download_dir, file_path)
        dirname = os.path.dirname(lpath)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        if not os.path.isfile(lpath):
            k = self.bucket.get_key(file_path)
            k.get_contents_to_filename(lpath)
        im = Image.open(lpath)
        if im.mode != self.mode:
            im = im.convert(self.mode)
        if not im.size == self.inshape[:2]:
            im = im.transpose(Image.ROTATE_270)
        assert im.size == self.inshape[:2], (im.size, self.inshape[:2])
        if im.size != self._shape[0]:
            m0 = self._shape[0]/float(im.size[0])
            m1 = self._shape[1]/float(im.size[1])
            new_shape = (int(round(im.size[0]*m0)), int(round(im.size[1]*m1)))
            im = im.resize(new_shape, Image.ANTIALIAS)
        rval = np.asarray(im, self._dtype).swapaxes(0, 1)
        if self.normalize:
            rval -= rval.mean()
            rval /= max(rval.std(), 1e-3)
        else:
            if 'float' in str(self._dtype):
                rval /= 255.0
        assert rval.shape == self._shape, (rval.shape, self._shape)
        return rval

