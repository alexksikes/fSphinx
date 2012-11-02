"""An advanced multi-field query object for Sphinx."""

__all__ = ['MultiFieldQuery', 'QueryTerm', 'QueryParser']

import copy
import re
import utils

QUERY_PATTERN = re.compile('''
    @(?P<status>[+-]?)(?P<field>\w+|\*)\s+(?P<term>[^@()]+)
    |
    (?P<all>[^@()]+)''',
    re.I | re.U | re.X)


def ChangeQuery(func):
    def Wrapper(self, query):
        if isinstance(query, basestring):
            query = MultiFieldQuery(query, user_sph_map=self.user_sph_map)
        elif isinstance(query, QueryTerm):
            query_term = copy.deepcopy(query)
            query = MultiFieldQuery(user_sph_map=self.user_sph_map)
            query.AddQueryTerm(query_term)
        return func(self, query)
    return Wrapper


def ChangeQueryTerm(func):
    def Wrapper(self, query_term):
        if isinstance(query_term, basestring):
            query_term = QueryTerm.FromString(query_term, user_sph_map=self.user_sph_map)
        return func(self, query_term)
    return Wrapper


class QueryParser(object):
    """Creates a query parser of the given type. Returns a ParsedQuery.
    """
    def __init__(self, type, **kwargs):
        self.type = type
        self.kwargs = kwargs

    def Parse(self, query):
        q = self.type(**self.kwargs)
        q.Parse(query)
        return q
        

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

    def __init__(self, query='', user_sph_map={}):
        self.user_sph_map = dict((k.lower(), v.lower()) for k, v in user_sph_map.items())
        self._qts = []
        if query:
            self.Parse(query)

    def Parse(self, query):
        """Parse a query string.

        Every query passed to a facet or to a sphinx client must have been parsed
        beforehand.
        """
        self._qts = []
        for m in QUERY_PATTERN.finditer(query):
            query_term = QueryTerm.FromMatchObject(m, self.user_sph_map)
            if query_term:
                self.AddQueryTerm(query_term)

    @ChangeQueryTerm
    def AddQueryTerm(self, query_term):
        """Used internally to add a query term as a QueryTerm object.
        """
        if query_term in self:
            self._qts.remove(query_term)
        if query_term:
            self._qts.append(query_term)

    @ChangeQueryTerm
    def RemoveQueryTerm(self, query_term):
        """Used internally to remove a query term as a QueryTerm object.
        """
        if query_term in self:
            self._qts.remove(query_term)

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
        if s == '(@* "")':
            s = ''
        if not s and not self.ALLOW_EMPTY:
            s = ' '
        return s

    @property
    def uniq(self):
        """A canonical / unique string representation of this query.
        """
        return utils.strips(' '.join(qt.uniq for qt in sorted(self)))

    def count(self, field):
        """Returns a count of how many times this field appears is in the query.
        """
        return sum(1 for qt in self if (field.lower() in (qt.user_field, qt.sph_field) and qt.status != '-'))

    @ChangeQueryTerm
    def __getitem__(self, query_term):
        if isinstance(query_term, int):
            return self._qts[query_term]
        return self._qts[self._qts.index(query_term)]

    @ChangeQueryTerm
    def __contains__(self, query_term):
        return query_term in self._qts

    def __iter__(self):
        """Iterates over query terms in order.
        """
        for qt in self._qts:
            yield qt

    def __str__(self):
        return self.user

    def __repr__(self):
        return repr(self._qts)

    @ChangeQuery
    def __and__(self, query):
        q = self - self  # hack to permit subclassing
        for query_term in query:
            if query_term in self and query_term in query:
                q.AddQueryTerm(query_term)
        return q

    @ChangeQuery
    def __or__(self, query):
        return self + query

    @ChangeQuery
    def __sub__(self, query):
        q = copy.deepcopy(self)
        for query_term in query:
            q.RemoveQueryTerm(query_term)
        return q

    @ChangeQuery
    def __add__(self, query):
        q = copy.deepcopy(self)
        for query_term in query:
            q.AddQueryTerm(query_term)
        return q

    def __len__(self):
        return len(self._qts)

    @ChangeQueryTerm
    def GetQueryToggle(self, query_term):
        query = copy.deepcopy(self)
        query[query_term].Toggle()
        return query

    def GetQueryFilter(self, ffilter):
        query = self - self  # permit subclassing
        for qt in self:
            if ffilter(qt):
                query.AddQueryTerm(qt)
        return query

    def ToPrettyUrl(self, **kwargs):
        from pretty_url import QueryToPrettyUrl
        return QueryToPrettyUrl(self, **kwargs)


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
        # bug in sphinx: make science-fiction -> science fiction
        term = re.sub('(\w)(-)(\w)', '\\1 \\3', self.term, re.U)
        if self.status in ('', '+'):
            return '(@%s %s)' % (self.sph_field, term)
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

    def Toggle(self):
        self.status = self.status != '-' and '-' or ''

    def ToggleOn(self):
        self.status = ''

    def ToggleOff(self):
        self.status = '-'
