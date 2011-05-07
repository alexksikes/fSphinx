"""Provides all the functionalities of fSphinx into on client."""

__all__ = ['FSphinxClient']

import re
import types

from sphinxapi import SphinxClient

from facets import FacetGroup
from hits import Hits
from queries import MultiFieldQuery

# NOTE: batch queries with AddQuery and RunQueries are not implemented.

class FSphinxClient(SphinxClient):
    """Creates a sphinx client but with all of fSphinx additional functionalities.
    """
    def AttachQueryParser(self, query_parser=MultiFieldQuery):
        """Attach a query parser so every will be parsed using it.
        
        The query parser must be inherit from MultiFieldQuery.
        """
        self.query_parser = query_parser
        
    def AttachDBFetch(self, db_fetch):
        """Attach a DBFetch object to retrieve hits from the database.
        """
        self.db_fetch = db_fetch
        self.hits = Hits()
    
    def AttachFacets(self, *facets, **kwargs):
        """Attach a list of facet which will be computed.
        
        The facets are put into a FacetGroup for performance.
        """
        db = kwargs.get('db')
        if not db and hasattr(self, 'db_fetch'):
            db = self.db_fetch._db
        self.facets = FacetGroup(*facets)
        self.facets.AttachSphinxClient(self, db)
        
    def Query(self, query, index='*', comment=''):
        """Processes the query as Sphinx normally would.
        
        If specified, parse the query, retrieve the hits and compute the facets.
        """
        # first let's parse the query if possible
        if not isinstance(query, MultiFieldQuery) and hasattr(self, 'query_parser'):
            self.query_parser.Parse(query)
            query = self.query_parser
        self.query = query
        
        # let's perform a normal query
        results = SphinxClient.Query(self, 
            getattr(query, 'sphinx', query), 
            getattr(self, 'default_index', index), 
            comment
        )
        
        # let's fetch the hits from the DB if possible
        if hasattr(self, 'db_fetch') and results and results['total_found']:
            self.hits = self.db_fetch.Fetch(results)
        
        # let's compute the facets if possible
        if hasattr(self, 'facets') and results and results['total_found']:
            self.facets.Compute(query)
        
        # keep expected return of SphinxClient
        if hasattr(self, 'hits'):
            return self.hits
        else:
            return results
        
    def SetDefaultIndex(self, index):
        """Sets a default index so we don't have to pass it to Query each time.
        
        By default Sphinx searches all indexes served by searchd.
        """
        self.default_index = index
    
    @classmethod
    def FromConfig(cls, path):
        """Creates a client from a config file.
        
        A configuration file is a plain python file which creates a client 
        called "cl" in its local namespace.
        The configuration file may be passed as a module or as path to the 
        configuration file.
        """
        if isinstance(path, types.ModuleType):
            reload(path)
            return path.cl
        import sys, utils
        for d in utils.get_all_sub_dirs(path)[::-1]:
            sys.path.insert(0, d)
        cf = {'sys':sys}; execfile(path, cf, cf)
        return cf['cl']
