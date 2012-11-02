"""A MySQL read only storage layer for Sphinx to retrieve hits."""

__all__ = ['Hits', 'DBFetch', 'DB', 'SplitOnSep', 'BuildExcerpts', 'Highlight']

from operator import itemgetter
import utils

DB = None


class DBFetch(object):
    """Creates a DBFetch object to retrieve hits from the database.

    The sql parameter is a SQL statement with the special variable $id which
    will be replaced by the ids that Sphinx returns.
    The db parameter is a handle to your database created with utils.database.

    # let's have a handle to our fsphinx database
    db = utils.database(dbn='mysql', db='fsphinx', user='fsphinx', passwd='fsphinx')

    # let's create a fetcher
    db_fetch = DBFetch(db, sql =
    '''select
        imdb_id, filename, title, year, plot,
        (select group_concat(distinct director_name separator '@#@') from directors as d
        where d.imdb_id = t.imdb_id) as directors
    '''

    Addtionnally functions to post process the hits could be added.
    """
    def __init__(self, db=DB, sql='', getter=itemgetter('id'), post_processors=[]):
        self._db = db
        self._sql = sql
        self._getter = getter
        self._post_processors = post_processors

    def _FetchInternal(self, hits):
        ids = [self._getter(m) for m in hits.matches]
        if ids:
            s_ids = ','.join(map(str, ids))
            if not self._sql:
                values = (utils.storage(id=str(id)) for id in ids)
            else:
                values = self._db.query(self._sql.replace('$id', s_ids))
            for value, match in zip(values, hits.matches):
                match['@hit'] = value
            for p in self._post_processors:
                p(hits)
        hits.ids = ids

    def Fetch(self, sphinx_results):
        """Returns a Hits object for the given Sphinx results.
        """
        return Hits(sphinx_results, self)


class Hits(utils.storage):
    """Returned by DBFetch or create an empty Hits object.

    A Hits object behaves like a normal sphinx results but each match has an additional
    field called "@hit" for each field value retrieved.
    """
    def __init__(self, sphinx_results=None, db_fetch=None):
        utils.storage.__init__(self,
            dict(status=0, time=0, total=0, total_found=0, error='', warning='', matches=[],
                 fields=[], words=[], ids=[], attrs=[]))
        if sphinx_results:
            self.update(sphinx_results)
        if self['warning']:
            print self['warning']
        if self['error']:
            raise Exception(self['error'])
        if not db_fetch:
            db_fetch = DBFetch(None, '', getter=itemgetter('id'))
        db_fetch._FetchInternal(self)

    def __str__(self):
        """A string representation of these hits showing the number of results,
        time taken and the hits retrieved.
        """
        s = 'matches: (%(total)i/%(total_found)i documents in %(time)s sec.)\n' % self
        for i, match in enumerate(self['matches']):
            s += '%s. ' % (i + 1)
            s += 'document=%(id)s, weight=%(weight)s\n' % match
            s += ', '.join('%s=%s' % (k, utils._unicode(v))
                for k, v in match['attrs'].items()) + '\n'
            for k, v in match['@hit'].items():
                if isinstance(v, list):
                    v = ', '.join(v)
                s += '\t%s=%s\n' % (k, utils._unicode(v))
        s += '\nwords:\n'
        for i, word in enumerate(self['words']):
            s += '%s. ' % (i + 1)
            s += '"%(word)s": %(docs)s documents, %(hits)s hits\n' % word
        return s.encode('utf-8')

    def __iter__(self):
        """Iterate over every match only.
        """
        for match in self.matches:
            yield match


class SplitOnSep(object):
    """A post processor to split multi value fields which have concatenated using a
    separator.
    """
    def __init__(self, *on_fields, **opts):
        self._on_fields = on_fields
        self._suffix = opts.get('suffix', '')
        self._sep = opts.get('sep', '@#@')

    def __call__(self, hits):
        for match in hits.matches:
            hit = match['@hit']
            for f in self._on_fields:
                if isinstance(hit[f], basestring):
                    hit[f + self._suffix] = hit[f].split(self._sep)


class BuildExcerpts(object):
    """A post processor to build excerpts using Sphinx BuildExcerpts function.
    """
    def __init__(self, cl, *on_fields, **opts):
        self._cl = cl
        self._on_fields = on_fields
        self._suffix = opts.get('suffix', '_excerpts')
        self._index = opts.get('index', getattr(cl, 'default_index', '*'))
        self._opts = opts
        #self._opts['query_mode'] = opts.get('query_mode', True)

    def __call__(self, hits):
        words = getattr(self._cl.query, 'sphinx', self._cl.query)

        docs = []
        for match in hits.matches:
            docs.extend([utils._unicode(match['@hit'][f]) for f in self._on_fields])

        all_excerpts = self._cl.BuildExcerpts(docs, self._index, words, self._opts)
        print all_excerpts
        for match, excerpts in zip(hits.matches, utils.group(all_excerpts, len(self._on_fields))):
            for f, excerpt in zip(self._on_fields, excerpts):
                match['@hit'][f + self._suffix] = excerpt or match['@hit'][f]


class Highlight(BuildExcerpts):
    """A post processor to highlight the results returned.
    """
    def __init__(self, cl, *on_fields, **opts):
        opts['suffix'] = opts.get('suffix', '_highlighted')
        opts['limits'] = 2048
        BuildExcerpts.__init__(self, cl, *on_fields, **opts)
