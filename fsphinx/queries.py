"""An advanced multi-field query object for Sphinx."""

__all__ = ['MultiFieldQuery', 'QueryTerm']

import re
import utils

QUERY_PATTERN = re.compile('''
    @(?P<status>[+-]?)(?P<field>\w+|\*)\s+(?P<term>[^@()]+)
    |
    (?P<all>[^@()]+)''', 
    re.I|re.U|re.X)

class MultiFieldQuery(object):
    """Creates multi-field query to let the user search within specific fields
    and therefore refine by facet values.
    
    The dictionnary user_sph_map provides a mapping between the user field search 
    and the sphinx field search.
    
    If passed to a sphinx client, match mode be set to extended2 as shown below:
    
    # setting cl to extended matching mode
    cl.SetMatchMode(sphinxapi.SPH_MATCH_EXTENDED2)
    
    The class variable ALLOW_EMPTY controls whether to interpret an empty query 
    as '' leading Sphinx to full scan mode.
    """
    
    ALLOW_EMPTY = False
    
    def __init__(self, user_sph_map={}):
        self.user_sph_map = dict((k.lower(), v.lower()) for k, v in user_sph_map.items())
        self._qts = []
        self._qts_dict = {}
        self.raw = ''
        
    def Parse(self, query):
        """Parse a query string.
        
        Every query passed to a facet or to a sphinx client must have been parsed
        beforehand.
        """
        self.raw = query
        self._qts = []
        self._qts_dict = {}
        for m in QUERY_PATTERN.finditer(query):
            qt = QueryTerm.FromMatchObject(m, self.user_sph_map)
            if qt:
                self._AddQueryTerm(qt)
        
    def _AddQueryTerm(self, qt):
        """Used internally to add a query term as a QueryTerm object.
        """
        if qt in self:
            self._qts.remove(qt)
        self._qts.append(qt)
        self._qts_dict[qt] = qt
        
    @property   
    def user(self):
        """A representation of this query as manipulated by the user.
        """
        return ' '.join(qt.user for qt in self)
    
    @property   
    def sphinx(self):
        """The string representation of this query which should be sent to sphinx.
        """
        s = utils.strips(' '.join(qt.sphinx for qt in self))
        if not s and not self.ALLOW_EMPTY:
            s = ' '
        return s
            
    @property   
    def uniq(self):
        """A canonical / unique string representation of this query.
        
        SQLCache will look for this variable when caching the query results.
        """
        return utils.strips(' '.join(qt.uniq for qt in sorted(self)))

    def Toggle(self, query_term):
        """Toggle a query term in this query on or off.
        """
        qt = self.GetQueryTerm(query_term)
        qt.status = qt.status != '-' and '-' or ''
            
    def ToggleOn(self, query_term):
        """Toggle a query term on.
        """
        qt = self.GetQueryTerm(query_term)
        if qt:
            qt.status = '+'
        
    def ToggleOff(self, query_term):
        """Toggle a query term on.
        """
        qt = self.GetQueryTerm(query_term)
        if qt:
            qt.status = '-'
        
    def GetQueryTerm(self, query_term):
        """Return a QueryTerm object from the query.
        query_term could be a string or QueryTerm object.
        """
        if isinstance(query_term, basestring):
            qt = QueryTerm.FromString(query_term, self.user_sph_map)
        elif isinstance(query_term, QueryTerm):
            qt = query_term 
        else:
            qt = None
        if qt in self._qts_dict:
            return self._qts_dict[qt]
    
    def __getitem__(self, query_term):
        return self.GetQueryTerm(query_term)
        
    def __contains__(self, query_term):
        return bool(self.GetQueryTerm(query_term))
    
    def count(self, field):
        """Returns a count of how many times this field appears is in the query.
        """
        return sum(1 for qt in self if field.lower() in (qt.user_field, qt.sph_field))
    
    def __iter__(self):
        """Iterates over query terms in order.
        """
        for qt in self._qts:
            yield qt
    
    def __str__(self):
        return self.user
    
    def __repr__(self):
        return repr(self._qts)
    
class QueryTerm(object):
    """Used internally by a multi-field query.
    
    Query terms may be created from a match object or its string representation. 
    """
    def __init__(self, status, field, term, user_sph_map={}):
        self.status = status
        self.term = utils.strips(term)
        field = field.strip().lower()
        self.user_field = utils.dictreverse(user_sph_map).get(field, field).lower()
        self.sph_field = user_sph_map.get(field, field).lower()
        
    @classmethod
    def FromMatchObject(cls, m, user_sph_map={}):
        """Create a QueryTerm from a match object.
        """
        if not m: 
            return None
        status, field, term, all = m.groups()
        if all and not all.strip():
            return None
        if all:
            term, field = all, '*'
        if status != '-':
            status = ''
        if field.strip():
            return cls(status, field, term, user_sph_map)
        
    @classmethod
    def FromString(cls, s, user_sph_map={}):
        """Create a QueryTerm from a string.
        """
        m = QUERY_PATTERN.search(s)
        return cls.FromMatchObject(m, user_sph_map)
    
    @property
    def user(self):
        """A representation of this query term as manipulated by the user.
        """
        return '(@%s%s %s)' % (self.status, self.user_field, self.term)
    
    @property
    def sphinx(self):
        """The string representation of this query term which should be sent to 
        sphinx.
        """
        if self.status in ('', '+'):
            return '(@%s %s)' % (self.sph_field, self.term)
        else:
            return ''
            
    @property
    def uniq(self):
        """A canonical / unique string representation of this query term.
        """
        return self.sphinx.strip().lower()
    
    def __str__(self):
        return self.user

    def __repr__(self):
        return '<%s>' % vars(self)
    
    def __cmp__(self, qt):
        """Two query terms are considered equal case insensitively of their term 
        value.
        """
        return cmp((self.user_field, self.term.lower()), (qt.user_field, qt.term.lower()))

    def __hash__(self):
        """Used by MultiFieldQuery.__contains__. 
        """
        return hash((self.user_field, self.term.lower()))
