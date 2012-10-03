"""This module adds caching to Sphinx."""

__all__ = ['RedisCache', 'CacheSphinx', 'CacheIO']

import redis
import hashlib
import simplejson as json

from sphinxapi import SphinxClient


class RedisCache(object):
    """Creates a cache using Redis which can be attached to a fSphinx client.
    """
    def __init__(self, **kwargs):
        # default is 200MB
        self.maxmemory = kwargs.pop('maxmemory', 1024 * 1024 * 200)
        # default is volatile-lru cf http://antirez.com/post/redis-as-LRU-cache.html
        self.maxmemory_policy = kwargs.pop('maxmemory_policy', 'volatile-lru')
        # default is 3 samples
        self.maxmemory_samples = kwargs.pop('maxmemory_samples', 3)
        # expire on new keys default is we let maxmemory-policy do the job
        self.expire = kwargs.pop('expire', 10 ** 10)
        # initialize redis cache
        self.c = redis.StrictRedis(**kwargs)
        self.c.config_set('maxmemory', self.maxmemory)
        self.c.config_set('maxmemory-policy', self.maxmemory_policy)
        self.c.config_set('maxmemory-samples', self.maxmemory_samples)

    def _MakeKey(self, key):
        if not isinstance(key, basestring):
            key = repr(key)
        return hashlib.md5(key).hexdigest()

    def Set(self, key, value, expire=0, _raw=False):
        if not _raw:
            key = self._MakeKey(key)
            value = json.dumps(value)
        self.c.set(key, value)

        expire = expire or self.expire
        if expire == -1:
            self.c.persist(key)
        else:
            self.c.expire(key, expire)

    def Get(self, key):
        value = self.c.get(self._MakeKey(key))
        if value:
            value = json.loads(value)
        return value

    def GetSet(self, key, func):
        if key in self:
            val = self.Get(key)
        else:
            val = func()
            self.Set(key, val)
        return val

    def Dumps(self, to_file):
        to_file = open(to_file, 'w')
        for k in self.c.keys('*'):
            to_file.write('%s@@@@@%s\n' % (k, self.c.get(k)))

    def Loads(self, from_file, expire=0):
        for l in open(from_file):
            if '@@@@@' not in l:
                print 'Warning: skipping %s' % l
            k, v = l.split('@@@@@')
            self.Set(k, v, expire, _raw=True)

    def Flush(self):
        self.c.flushdb()

    def __contains__(self, key):
        return self.c.exists(self._MakeKey(key))


def CacheSphinx(cache, cl):
    """Caches the request of a Sphinx client.
    """
    # there are requests and to be computed results
    reqs = [req for req in cl._reqs]
    results = [None] * len(reqs)
    comp_reqs = []
    comp_results = []

    # get results from cache
    for i, req in enumerate(reqs):
        if req in cache:
            results[i] = cache.Get(req)
            results[i]['time'] = 0
        else:
            comp_reqs.append(req)

    # get results that need to be computed
    if comp_reqs:
        cl._reqs = comp_reqs
        comp_results = SphinxClient.RunQueries(cl)
    else:
        cl._reqs = []

    # return None on IO failure
    if comp_results == None:
        return None

    # cache computed results and Get results
    for req, result in zip(comp_reqs, comp_results):
        if result != None:
            cache.Set(req, result)
        results[results.index(None)] = result

    return results


def CacheIO(func):
    """Decorator used to memoize the return value of an instance method.
    The instance is assumed to have a RedisCache.
    """
    # assumes object has a redis cache
    def Wrapper(self, *args, **kwargs):
        key = (func.__name__, args, kwargs)

        def Lazy():
            return func(self, *args, **kwargs)
        if hasattr(self, 'cache') and isinstance(self.cache, RedisCache):
            return self.cache.GetSet(key, Lazy)
        else:
            return Lazy()
    return Wrapper
