"""Provides all the functionalities of fSphinx into on client."""

__all__ = ['FSphinxClient']

import os
import sys
import weakref

import utils
from sphinxapi import SphinxClient
from facets import FacetGroup
from facets import Facet
from hits import Hits
import cache


# NOTE: batch queries with AddQuery and RunQueries are not implemented.

class FSphinxClient(SphinxClient):
    def __init__(self):
        """Creates a sphinx client but with all of fSphinx additional functionalities.
        """
        # the possible options
        self.query_parser = None
        self.default_index = '*'
        self.db_fetch = None
        self.cache = None
        self.sort_mode_options = []

        # the returned results
        self.query = ''
        self.hits = Hits()
        self.facets = FacetGroup()

        SphinxClient.__init__(self)

    def AttachQueryParser(self, query_parser):
        """Attach a query parser so every query will be parsed using it.
        """
        self.query_parser = query_parser

    def AttachDBFetch(self, db_fetch):
        """Attach a DBFetch object to retrieve hits from the database.
        """
        self.db_fetch = db_fetch

    def AttachFacets(self, *facets, **kwargs):
        """Attach a list of facet which will be computed.

        The facets are put into a FacetGroup for performance.
        """
        # if not found get db from db_fetch
        db = kwargs.get('db')
        if not db and hasattr(self, 'db_fetch'):
            db = self.db_fetch._db

        # avoid memory leak and circular references to cl
        cl = kwargs.get('cl')
        if not cl:
            cl = weakref.proxy(self)

        # set the facets and the Sphinx client
        self.facets = FacetGroup(*facets)
        self.facets.AttachSphinxClient(cl, db)

    def AttachCache(self, cache):
        """Attach a RedisCache to cache the results.

        If facets are attached, this will also cache the facets.
        """
        self.cache = cache

    def SetDefaultIndex(self, index):
        """Sets a default index so we don't have to pass it to Query each time.

        By default Sphinx searches all indexes served by searchd.
        """
        self.default_index = index

    def SetSortModeOptions(self, options, reset=True):
        if reset:
            self.sort_mode_options = options
        else:
            self.sort_mode_options.update(options)

    def SetSortMode(self, mode, clause=''):
        if mode in self.sort_mode_options:
            sort_mode = self.sort_mode_options[mode]
        else:
            sort_mode = (mode, clause)
        SphinxClient.SetSortMode(self, *sort_mode)

    def RunQueries(self, caching=None):
        if not self.cache or caching is False:
            return SphinxClient.RunQueries(self)
        else:
            return cache.CacheSphinx(self.cache, self)

    def Query(self, query, index='', comment=''):
        """Processes the query as Sphinx normally would.

        If specified, parse the query, retrieve the hits and compute the facets.
        """
        # first let's parse the query if possible
        if self.query_parser and isinstance(query, basestring):
            query = self.query_parser.Parse(query)
        self.query = query

        # check the default index
        index = index or self.default_index

        # let's perform a normal query
        results = SphinxClient.Query(self, getattr(query, 'sphinx', query), index, comment)
     
        # let's fetch the hits from the DB if possible
        if self.db_fetch and results and results['total_found']:
            self.hits = self.db_fetch.Fetch(results)
        else:
            self.hits = Hits(results)

        # let's compute the facets if possible
        if self.facets and results and results['total_found']:
            self.facets.Compute(query)

        # keep expected return of SphinxClient
        return self.hits

    @classmethod
    def FromConfig(cls, path):
        """Creates a client from a config file.

        A configuration file is a plain python file which creates a client
        called "cl" in its local namespace.
        """
        # if path is a module
        if hasattr(path, '__file__'):
            path = os.path.splitext(path.__file__)[0] + '.py'

        for d in utils.get_all_sub_dirs(path)[::-1]:
            sys.path.insert(0, d)
        cf = {'sys':sys}; execfile(path, cf, cf)
        return cf['cl']

    def Clone(self, memo={}):
        """Creates a copy of this client.

        This makes sure a new connection is not reiniated on the db and to the cache.
        It will also initialize the returned results (query, hits, facet results).
        """
        return self.__deepcopy__(memo)

    def __deepcopy__(self, memo):
        cl = self.__class__()

        attrs = utils.save_attrs(self,
            [a for a in self.__dict__ if a not in ['query', 'hits', 'facets', 'db_fetch', 'cache']])
        utils.load_attrs(cl, attrs)

        if self.db_fetch:
            cl.AttachDBFetch(self.db_fetch)

        if self.facets:
            facets = []
            for f in self.facets:
                attrs = utils.save_attrs(f,
                    [a for a in f.__dict__ if a not in ['_db', 'results', 'query']])
                f = Facet(f.name)
                utils.load_attrs(f, attrs)
                facets.append(f)
            cl.AttachFacets(*facets)

        if self.cache:
            cl.AttachCache(self.cache)

        return cl
