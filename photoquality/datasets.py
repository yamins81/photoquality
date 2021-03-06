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

def process_data(data):
    N = len(data)
    ds = [{} for _i in range(N)]
    imgss = [d['answers'][0]['ImgOrder'] for d in data]
    resps = [np.array(d['answers'][0]['Response']).astype('int') for d in data]
    for d, imgs, resp in zip(ds, imgss, resps):
        for (im, r) in zip(imgs, resp):
            for (i, r0) in zip(im, r):
                if i in d:
                    d[i].append(r0)
                else:    
                    d[i] = [r0]
    Ds = [dict([(_k, np.mean(v)) for _k, v in d.items()]) for d in ds]
    return Ds
    
    
def process_data_split_part(data):
    N = len(data)
    ds = [{} for _i in range(N)]
    imgss = [d['answers'][0]['ImgOrder'] for d in data]
    resps = [np.array(d['answers'][0]['Response']).astype('int') for d in data]
    for d, imgs, resp in zip(ds, imgss, resps):
        for (im, r) in zip(imgs, resp):
            for (i, r0) in zip(im, r):
                if i in d:
                    d[i].append(r0)
                else:    
                    d[i] = [r0]
                    
    return ds, imgss
    
    
def process_data_splits(data):
    DSS = [pd.process_data_split_part(ad) for ad in data]
    def dict_append(d1, d2):
        for k in d2:
            if k in d1:
                d1[k].extend(d2[k])
            else:
                d1[k] = d2[k]
        return d
    H = []
    for d in DSS:
        h = {}
        for dd in d[0]:
            dict_append(h, dd)
        H.append(h)

    
def process_data_split_all(data):
    def proc(x):
        return x[0] == '1'
    DD = {}
    for ad in data:
        for _ad in ad:
            for (_p, _a) in zip(_ad['answers'][0]['ImgOrder'], _ad['answers'][0]['Response']):
                if tuple(_p) in DD:
                    DD[tuple(_p)].append(proc(_a))
                elif (_p[1], _p[0]) in DD:
                    DD[(_p[1], _p[0])].append(1 - proc(_a))
                else:
                    DD[tuple(_p)] = [proc(_a)]
                    
    R = np.array(map(np.mean, DD.values()))
    
    DDr = {}
    for k in DD:
        if k[0] in DDr:
            DDr[k[0]].append((np.mean(DD[k]), k[1]))
        else:
            DDr[k[0]] = [(np.mean(DD[k]), k[1])]
        if k[1] in DDr:
            DDr[k[1]].append((np.mean([1 - _d for _d in DD[k]]), k[0]))
        else:
            DDr[k[1]] = [(np.mean([1 - _d for _d in DD[k]]), k[0])]
    #for k in DDr:
    #    DDr[k] = DDr[k].mean()
    return DD, R, DDr
    
    
class TechRehearsalImages(object):

    name = 'TechRehearsal'

    S3_ARCHIVES = []

    S3_FILES = [('human_data/01_Mongolian_Test_Data_01.pkl', '62a6e5a8e9d788f7dd9c510bec20c501ead8602d'),
                ('human_data/04_Snow_Dragon_Mountain_Test_Data_01.pkl', '5cef50e9bafebaa0dbcfb4d5d878323c2e67fdec'),
                ('human_data/01_Mongolian_Test_Data_01_binary.pkl', '32d89d4170f6deb763e402d697294aaf7df9dc25'),
                ('human_data/01_Mongolian_Test_Data_01_binary_splits.pkl', '3da6161770d5de538be8dccf5192c0ae844fbf44'),
                ('human_data/03_Lantern_Test_Data_01_binary_splits.pkl', '3c45913634a8120b536861917851969fc94cb371'),
                ('human_data/06_Just_You_Test_Data_01_binary_splits.pkl', '349312ae3b4d49c8495133a9f3374029791cce68'), 
                ('human_data/07_Misa_Test_Data_01_binary_splits.pkl', 'e8a3e74d343b9f6adb419a5e7d7d47bb6ad2c702'), 
                ('human_data/11_Basket_Test_Data_01_binary_splits.pkl', 'c58183b54923bc98e7431245342abbc11487ab8e')]
                
    human_data = ['01_Mongolian_Test_Data_01', 
                  '04_Snow_Dragon_Mountain_Test_Data_01',
                  '01_Mongolian_Test_Data_01_binary',
                  '01_Mongolian_Test_Data_01_binary_splits',
                  '03_Lantern_Test_Data_01_binary_splits',
                  '06_Just_You_Test_Data_01_binary_splits',
                  '07_Misa_Test_Data_01_binary_splits',
                  '11_Basket_Test_Data_01_binary_splits']

    insize = (4256, 2832)

    def __init__(self, credentials=None):
        if credentials is None:
            self.conn = boto.connect_s3()
        else:
            self.conn = boto.connect_s3(*credentials)
        self.credentials = credentials
        self.bucket = self.conn.get_bucket('pics-from-sam')
        resource_home  = self.home('resources')
        if not os.path.exists(resource_home):
            os.makedirs(resource_home)

    def home(self, *suffix_paths):
        return os.path.join(get_data_home(), self.name, *suffix_paths)

    def download_image(self):
        pass
        
    def fetch(self):
        """Download and extract the dataset."""
        home = self.home()
        if not os.path.exists(home):
            os.makedirs(home)
        for b in self.S3_ARCHIVES:
            if len(b) == 2:
                base, sha1 = b
                dirn = home
            else:
                base, sha1, dn = b
                dirn = os.path.join(home, dn)
            archive_filename = os.path.join(home, base.split('/')[-1])
            if not os.path.exists(archive_filename):
                #credentials have to be properly set in ~/.boto
                #or environment variables
                url = 'http://pics-from-sam.s3.amazonaws.com/' + base
                print ('downloading %s' % url)
                download_boto(url, self.credentials, archive_filename, sha1=sha1)
                extract(archive_filename, dirn, sha1=sha1, verbose=True)
        for x, sha1 in self.S3_FILES:
            dirn = os.path.join(home, '/'.join(x.split('/')[:-1]))
            if not os.path.isdir(dirn):
                os.makedirs(dirn)
            filename = os.path.join(home, x)
            if not os.path.exists(filename):
                url = 'http://pics-from-sam.s3.amazonaws.com/' + x
                print ('downloading %s' % url)
                download_boto(url, self.credentials, filename, sha1=sha1)

    def load_human_data(self):
        self.fetch()
        hd = {}
        for x in self.human_data:
            fn = self.home('human_data', x+ '.pkl')
            hd[x]  = cPickle.load(open(fn))
            for _h in hd[x]:
                if hasattr(_h, 'keys'):
                    _h = [_h]
                for _hh in _h:
                    _hh['answers'] = json.loads(_hh['answers'][0])
        return hd        
                    
    def analyze_human_data(self):
        hd = self.load_human_data()
        A = {}
        DSS = {}
        for k in hd:
            data = hd[k]
            if hasattr(data[0], 'keys'):
                Ds = process_data(data)
                DSS[k] = Ds
                A[k] = np.array([ds.values() for ds in Ds])
            else:
                A[k] = process_data_split_all(data)
        return A, DSS
            
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

    def get_subsets_random(self, k, n=None):
        meta = self.meta
        events = np.unique(meta['event'])
        subset_d = {}
        for e in events:
            m = meta[meta['event'] == e]
            if n is None:
                n = len(m)
            filenames = m['filename']
            subsets = []
            for ind in range(n):
                p = np.random.RandomState(seed=ind).permutation(len(m))[:k]
                subsets.append(filenames[p].tolist())
            subset_d[e] = subsets
        return subset_d

    def get_subsets(self, k, n=None, ns=0):
        meta = self.meta
        events = np.unique(meta['event'])
        subset_d = {}
        for e in events:
            m = meta[meta['event'] == e]
            fns = m['filename']
            if n is None:
                n = len(m)
            ndict = thing(n, k, len(fns), ns=ns)
            subsets = []
            for p in ndict.values():
                subsets.append(fns[p].tolist())
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


from yamutils.basic import dict_inverse
def thing(R, L, N, ns=0):
    S = range(R)
    nums = dict(zip(range(R), [0]*R))
    ndict = {}
    K = R * L / N
    for n in range(N):
        inds0 = np.random.RandomState(n + ns * N).permutation(len(S))[:K]
        inds = [S[_i] for _i in inds0]
        for ind in inds:
            nums[ind] += 1
            if nums[ind] >= L:
                S.remove(ind)
        ndict[n] = inds   
    ndict = dict_inverse(ndict)
    cv = 0
    for iv, kv in enumerate(ndict):
        if len(ndict[kv]) < L:
            j = range(cv, cv + L - len(ndict[kv]))
            jj = [_j % N for _j in j]
            ndict[kv].extend(jj)
            cv += len(j)
        
    return ndict
                