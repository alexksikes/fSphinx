"""This module adds facet computation to Sphinx."""

__all__ = ['Facet', 'FacetGroup']

import sphinxapi
import weakref

import utils
from hits import DBFetch
from hits import DB

try:
    import cache
except ImportError:
    cache = None


class Facet(object):
    """Creates a new facet of a given "facet_name".

    The facet must have a corresponding attribute declared in the Sphinx conf.
    The attribute may be either single or multi-valued and its name defaults to
    "facet_name_attr".

    Suppose we had a director facet, the attribute would look like this:

    # needed to create the director facet
    sql_attr_multi =
        uint director_attr from query;
        select imdb_id, imdb_director_id from directors

    Additionaly there must be a corresponding MySQL table (except for numerical
    facets) which maps ids to terms.
    The MySQL name defaults to "facet_name_terms" with an id and "facet_name"
    column.

    Again the director table terms would look like this:

    select * from director_terms limit 5;
    +----+------------------+
    | id | director         |
    +----+------------------+
    |  5 | Ingmar Bergman   |
    | 19 | Federico Fellini |
    | 33 | Alfred Hitchcock |
    | 36 | Buster Keaton    |
    | 37 | Gene Kelly       |
    +----+------------------+

    If the facet values are numerical (for example to refine by year) such a table
    isn't needed and sql_table = None must be explicitely passed.

    There are a lot of optional keyword arguments which are mainly used to
    overwrite the defaults:

    sql_table: name of the corresponsing MySQL table
    (defaults to "facet_name_terms").

    sql_col: name of the column field (defaults to "facet_name").
    sql_query: the full SQL query which will be called to retrieve the facet terms.

    attr: name of the corresponding Sphinx attribute (defaults to "facet_name_attr").
    func: grouping function (defaults to sphinxapi.SPH_GROUPBY_ATTR).
    group_sort: group sorting function (defaults to @count).
    sph_field: name of the corresponding Sphinx search field (defaults to "name")

    order_by: a lambda function used to order the returned facet values.
    max_num_values: maximum number of facet values (defaults 15).
    cutoff: threshold amount of matches to stop computing (defaults to 0)
    augment: augment the number of facet values if one is selected (defaults False).
    """
    def __init__(self, name, **kwargs):
        self.name = name

        # sql parameters
        self._sql_col = kwargs.get('sql_col', name)
        self._sql_table = kwargs.get('sql_table', name + '_terms')
        if self._sql_table:
            sql_query = \
                'select %s from %s ' % (self._sql_col, self._sql_table) + \
                'where id in ($id) order by field(id, $id)'
        else:
            sql_query = None
        self._sql_query = kwargs.get('sql_query', sql_query)

        # sphinx variables
        self._attr = kwargs.get('attr', self._sql_col + '_attr')
        self._func = kwargs.get('func', sphinxapi.SPH_GROUPBY_ATTR)
        self._group_sort = kwargs.get('group_sort', '@count desc')
        self._set_select = kwargs.get('set_select', '@groupby, @count')
        self._sph_field = kwargs.get('sph_field', name)

        # facets variables
        self._id = kwargs.get('id', name)
        self._enable = kwargs.get('enable', True)
        self._order_by = kwargs.get('order_by', lambda v: v['@term'])
        self._order_by_desc = False
        self._max_num_values = kwargs.get('max_num_values', 15)
        self._cutoff = kwargs.get('cutoff', 0)
        self._matches = kwargs.get('matches', 0)
        self._augment = kwargs.get('augment', True)

        # sphinx and db clients
        cl = kwargs.get('cl')
        if cl:
            self._cl = weakref.ref(cl)()
        self._db = kwargs.get('db')

        self._InitResults()

    def _InitResults(self):
        # the returning values
        self.results = utils.storage(time=0, total_found=0, error='', warning='', matches=[])
        self.query = ''

    def AttachSphinxClient(self, cl, db=None):
        """Attach a SphinxClient and a database to perform the computation and
        to retrieve the results from the database.

        If the facet terms are numerical, db is optional.
        """
        self._cl = cl
        self._db = db or self._db or cl.db_fetch._db or DB

    def SetGroupBy(self, attr, func, group_sort='@count desc'):
        """Set grouping attribute, function and grouping sorting clause.

        attr must refer to the facet attribute as declared in your Sphinx config file.
        More info: http://sphinxsearch.com/docs/manual-2.0.1.html#api-func-setgroupby.
        """
        self._attr = attr
        self._func = func
        self._group_sort = group_sort or self._group_sort

    def SetGroupSort(self, group_sort='@count desc'):
        """Set group sorting close.

        Note that this must be a clause not a custom grouping function.
        """
        self._group_sort = group_sort

    def SetGroupFunc(self, group_func, alias='@groupfunc', order='desc'):
        """Set a custom group sorting function.

        The value of the function is in '@groupfunc' or specified by the alias.
        """
        self._set_select = '@groupby, @count, %s as %s' % (group_func, alias)
        self._group_sort = '%s %s' % (alias, order)

    def SetOrderBy(self, key, order='desc'):
        """Set the ordering of the returned facet values.

        Possible ordering could be by '@count', '@groupby' or '@groupfunc'.
        """
        self._order_by = lambda v: v[key]
        self._order_by_desc = (order == 'desc')

    def SetMaxNumValues(self, max_num_values):
        """Set the maximum number of facet values returned.
        """
        self._max_num_values = max_num_values

    def SetCutOff(self, cutoff):
        """Set threshold amount of matches to stop computing.

        More info: http://sphinxsearch.com/docs/manual-2.0.1.html#api-func-setlimits
        """
        self._cutoff = cutoff

    def SetAugment(self, augment):
        """Set whether to compute one more facet value if a facet value is already selected.
        """
        self._augment = augment

    def Compute(self, query):
        """Compute the facet for a given query.

        query could be a string or MultifieldQuery object.
        """
        if self._enable:
            self._Prepare(query, self._cl)
            results = self._cl.RunQueries()[0]
            self._SetValues(query, results, self._db)
            self._OrderValues()
        else:
            self._InitResults()

    def SetEnable(self, enable=True):
        """A facet could be enabled / disabled meaning that it will or will not be computed.
        """
        self._enable = enable

    def _Prepare(self, query, cl):
        """Used internally to prepare the facet for computation for a given query
        using a given SphinxClient.
        """
        def SaveSphinxOpts():
            return utils.save_attrs(cl,
                ['_offset', '_limit', '_cutoff', '_select', '_groupby',
                 '_groupfunc', '_groupsort'])

        def LoadSphinxOpts(opts):
            utils.load_attrs(cl, opts)

        if self._augment:
            more = query.count(self._sph_field)
        else:
            more = 0
        self.query = query

        opts = SaveSphinxOpts()
        cl.SetLimits(0, self._max_num_values + more, cutoff=self._cutoff)
        cl.SetSelect(self._set_select)
        cl.SetGroupBy(self._attr, self._func, self._group_sort)
        cl.AddQuery(getattr(query, 'sphinx', query))
        LoadSphinxOpts(opts)

    def _SetValues(self, query, sphinx_results, db):
        """Used internally to set the facet terms and additional values in this facet.
        """
        # reset the facet values and stats
        self.results = utils.storage(time=0, total_found=0, error='', warning='', matches=[])
        
        # fetch the facet terms from the db
        db_fetch = DBFetch(db, self._sql_query, getter=lambda x: x['attrs']['@groupby'])
        hits = db_fetch.Fetch(sphinx_results)
        
        # let's get the stats from the results
        for k in self.results.keys():
            if k != 'matches':
                self.results[k] = hits[k]

        # finally let's setup the facet values
        for match in hits.matches:
            # get all virtual attributes
            value = dict((k, v) for k, v in match['attrs'].items() if k.startswith('@'))
            # get the facet term
            value['@term'] = match['@hit'][match['@hit'].keys()[-1]]
            # get the value of the grouping func
            value['@groupfunc'] = value.get('@groupfunc', value['@count'])
            # and whether the facet has been selected
            value['@selected'] = '@%s %s' % (self._sph_field, value['@term']) in query
            # append each value
            self.results.matches.append(value)

    def _OrderValues(self):
        """Used internally to order the facet values returned.
        """
        self.results.matches = sorted(self, key=self._order_by, reverse=self._order_by_desc)

    def __str__(self):
        """A string representation of this facet showing the number of results,
        time taken and the facet values returned.
        """
        stats = '(%s/%s values group sorted by "%s" in %s sec.)' % (
            self._max_num_values, self.results.total_found, self._group_sort, self.results.time)
        s = '%s: %s\n' % (self.name, stats)
        for i, value in enumerate(self):
            s += '\t%s. %s, ' % (i + 1, value['@term'])
            s += '@count=%s, @groupby=%s' % (value['@count'], value['@groupby']) + ', '
            s += ', '.join('%s=%s' % (k, v) for k, v in value.items()
                if k not in ['@term', '@count', '@groupby']) + '\n'
        return s.encode('utf-8')

    def __iter__(self):
        """Iterate over the computed facet values only.
        """
        for v in self.results.matches:
            yield v


class FacetGroup(object):
    """A FacetGroup is a set of facets which is used for performance and caching.

    Only one query to searchd is performed.
    Caching is performed using a fSphinx client with a RedisCache attached.
    """
    def __init__(self, *facets, **kwargs):
        # facet variables
        self.facets = facets
        self.time = 0
        self.query = ''
        self.cache = None

        # sphinx variables
        cl = kwargs.get('cl')
        db = kwargs.get('db', DB)
        if cl or db:
            self.AttachSphinxClient(cl, db)

    def AttachSphinxClient(self, cl, db=None):
        """Attach a SphinxClient and a database to perform the computation and
        to retrieve the results from the database.

        If all the facets are numerical, db is optional.
        """
        self._cl = cl
        self._db = db or self._db or cl.db_fetch._db or DB

    def AttachCache(self, cache):
        """Attach a RedisCache to cache the facet computation.
        """
        self.cache = cache

    def Compute(self, query, caching=None):
        """Compute all the facet in this gorup for a given query.

        query could be a string or MultifieldQuery object.
        """
        self._Prepare(query)
        results = self._RunQueries(caching)
        self._SetValues(query, results)

    def GetFacet(self, facet_id):
        for f in self.facets:
            if f._id == facet_id:
                return f

    def SetFacetEnable(self, facet_id, enable=True):
        """Enable / disable the computation of a given facet.
        """
        self.GetFacet(facet_id).SetEnable(enable)

    def _Prepare(self, query):
        """Used internally to prepare all the facets in this group for computation
        for a given query.
        """
        self.time = 0
        for f in self.facets:
            if f._enable:
                f._Prepare(query, self._cl)
            else:
                f._InitResults()
        self.query = query

    def _RunQueries(self, caching=None):
        """Used internally to run the queries all at once and possibly perform caching.

        If set the caching parameter is set to False, caching never occurs.
        """
        if not self.cache or caching is False:
            # it could still be cached if cl has a cache ..
            if hasattr(self._cl, 'cache'):
                return self._cl.RunQueries(caching)
            else:
                return self._cl.RunQueries()
        else:
            return cache.CacheSphinx(self.cache, self._cl)

    def _SetValues(self, query, results):
        """Used internally to set all the facet terms and additional values in the facets
        in this group.
        """
        for f in self.facets:
            if f._enable:
                f._SetValues(query, results.pop(0), self._db)
                f._OrderValues()
                self.time += float(f.results.time)

    def __len__(self):
        return len(self.facets)

    def __str__(self):
        """A string representation all of the facets in the group.
        """
        s = 'facets: (%s facets in %s sec.)\n' % (len(self.facets), self.time)
        for i, f in enumerate(self.facets):
            s += '%s. %s' % (i + 1, f)
        return s[:-1]

    def __iter__(self):
        """Iterate over the facets of the group.
        """
        for f in self.facets:
            yield f
