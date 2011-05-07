"""A MySQL read only storage layer for Sphinx to retrieve hits."""

__all__ = ['Hits', 'DBFetch', 'DB']

from operator import itemgetter

from utils import storage
from utils import _unicode

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
    """
    def __init__(self, db=DB, sql='', getter=itemgetter('id')):
        self._db = db
        self._sql = sql
        self._getter = getter
    
    def _FetchInternal(self, hits):
        ids = [self._getter(m) for m in hits.matches]
        if ids:
            s_ids = ','.join(map(str, ids))
            if not self._sql:
                values = (storage(id=str(id)) for id in ids)
            else:
                values = self._db.query(self._sql.replace('$id', s_ids))
            for hit, match in zip(values, hits.matches):
                match['@hit'] = hit
        hits.ids = ids
        
    def Fetch(self, sphinx_results):
        """Returns a Hits object for the given Sphinx results. 
        """
        return Hits(sphinx_results, self)

class Hits(storage):
    """Returned by DBFetch or create an empty Hits object. 
    
    A Hits object behaves like a normal sphinx results but each match has an additional 
    field called "@hit" for each field value retrieved.
    """
    def __init__(self, sphinx_results=None, db_fetch=None):
        storage.__init__(self, 
            dict(time=0, total=0, total_found=0, error='', warning='', matches=[], words=[], ids=[]))
        if sphinx_results:
            self.update(sphinx_results)
        if self['warning']:
            print self['warning']
        if self['error']:
            raise self['error']
        if not db_fetch:
            db_fetch = DBFetch(None, '', getter=itemgetter('id'))
        db_fetch._FetchInternal(self)    
    
    def __str__(self):
        """A string representation of these hits showing the number of results, 
        time taken and the hits retrieved.
        """
        s = 'matches: (%(total)i/%(total_found)i documents in %(time)s sec.)\n' % self
        for i, match in enumerate(self['matches']):
            s += '%s. ' % (i+1)
            s += 'document=%(id)s, weight=%(weight)s\n' % match
            s += ', '.join('%s=%s' % (k, v) 
                for k, v in match['attrs'].items()) + '\n'
            for k, v in match['@hit'].items():
                s += '\t%s=%s\n' % (k, _unicode(v))
        s += '\nwords:\n'
        for i, word in enumerate(self['words']):
            s += '%s. ' % (i+1)
            s += '"%(word)s": %(docs)s documents, %(hits)s hits\n' % word
        return s.encode('utf-8')
    
    def __iter__(self):
        """Iterate over every match only.
        """
        for match in self.matches:
            yield match
