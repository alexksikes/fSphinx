from __init__ import *

# let's fetch the results from the DB
db_fetch = DBFetch(db, sql = 
'''select 
    imdb_id, filename, title, year, plot,    
    (select group_concat(distinct director_name separator '@#@') from directors as d 
    where d.imdb_id = t.imdb_id) as directors
    from titles as t 
    where imdb_id in ($id)
    order by field(imdb_id, $id)
''')

# sql_table is optional and defaults to (facet_name)_terms
fyear = Facet('year', sql_table=None)

# sql_table is optional and defaults to (facet_name)_terms
factor = Facet('actor', sql_table='actor_terms')

# the sphinx client is what will perform the computation
factor.AttachSphinxClient(cl, db)

# let's set the number of facet values returned to 5
factor.SetMaxNumValues(5)

# creating a multi-field query
query = MultiFieldQuery({'actor':'actors', 'genre':'genres'})

# parsing a multi-field query
query.Parse('@year 1999 @genre drama @actor harrison ford')

## Putting Everything Together

# creating a sphinx client
cl = FSphinxClient()

# it behaves exactly like a normal SphinxClient
cl.SetServer('localhost', 9315)

# get the results from the db
cl.AttachDBFetch(db_fetch)

# attach the facets
cl.AttachFacets(fyear, factor)

# running the query
cl.Query('movie')

# or pass a MultiFieldQuery
cl.Query(query)
    
## Playing With Configuration Files

# as a module
#from config import sphinx_config
#cl = FSphinxClient.FromConfig(sphinx_config)

# or as a path to a configuration file
cl = FSphinxClient.FromConfig('../tutorial/config/sphinx_config.py')

# querying for "movie"
cl.Query('movie')