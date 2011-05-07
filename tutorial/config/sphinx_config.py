import sphinxapi
import web

from fsphinx import FSphinxClient, Facet, DBFetch, MultiFieldQuery

# connect to database
# IMPORTANT: note that this will re-create a connection each time
# Better import db using from ... import db
db = web.database(dbn='mysql', db='fsphinx', user='fsphinx', passwd='fsphinx')

# show output of mysql statements
db.printing = False

# create sphinx client
cl = FSphinxClient()

# connect to searchd
cl.SetServer('localhost', 9315)

# matching mode (faceted client should be SPH_MATCH_EXTENDED2)
cl.SetMatchMode(sphinxapi.SPH_MATCH_EXTENDED2)

# sorting and possible custom sorting function
cl.SetSortMode(sphinxapi.SPH_SORT_EXPR, '@weight * user_rating_attr * nb_votes_attr * year_attr / 100000')

# some fields could matter more than others
cl.SetFieldWeights({'title' : 30})

# sql query to fetch the hits
db_fetch = DBFetch(db, sql = '''
select 
    imdb_id, filename, title, year, user_rating, nb_votes, type_tv_serie, type_other, 
    release_date, release_date_raw, plot, awards, runtime, 
    color, aspect_ratio, certification, 
    cover_url, gallery_url, trailer_url, release_date_raw, 
    (select group_concat(distinct director_name separator '@#@') from directors as d where d.imdb_id = t.imdb_id) as directors, 
    (select group_concat(distinct actor_name separator '@#@') from casts as c where c.imdb_id = t.imdb_id) as actors, 
    (select group_concat(distinct genre separator '@#@') from genres as g where g.imdb_id = t.imdb_id) as genres, 
    (select group_concat(distinct plot_keyword separator '@#@') from plot_keywords as p where p.imdb_id = t.imdb_id) as plot_keywords 
from titles as t 
where imdb_id in ($id)
order by field(imdb_id, $id)'''
)
cl.AttachDBFetch(db_fetch)

# setup the different facets
cl.AttachFacets(
    Facet('year', sql_table=None),
    Facet('genre'),
    Facet('keyword', attr='plot_keyword_attr', sql_col='plot_keyword', sql_table='plot_keyword_terms'),
    Facet('director'),
    Facet('actor')
)

# for all facets compute count, groupby and this score
group_func = '''
sum(
    if (runtime_attr > 45,
        if (nb_votes_attr > 1000,
            if (nb_votes_attr < 10000, nb_votes_attr * user_rating_attr, 10000 * user_rating_attr),
        1000 * user_rating_attr),
    300 * user_rating_attr)
)'''

# setup sorting and ordering of each facet 
for f in cl.facets:
    f.SetGroupFunc(group_func)
    # order the term alphabetically within each facet
    f.SetOrderBy('@term')
    
# some facets are always precomputed 
cl.facets.preloading = True

# cache the facet computation
cl.facets.caching = True

# the query should always be parsed beforehand 
cl.AttachQueryParser(MultiFieldQuery({
    'genre' : 'genres', 
    'keyword' : 'plot_keywords', 
    'director' : 'directors', 
    'actor' : 'actors'
}))
