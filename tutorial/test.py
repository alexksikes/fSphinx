﻿## Setting up

# importing required modules
import sphinxapi
from fsphinx import *

# let's build a Sphinx Client
cl = sphinxapi.SphinxClient()

# assuming searchd is running on 9315
cl.SetServer('localhost', 9315)

# let's have a handle to our fsphinx database
db = utils.database(dbn='mysql', db='fsphinx', user='fsphinx', passwd='fsphinx')

## Playing with Facets

# sql_table is optional and defaults to (facet_name)_terms
factor = Facet('actor', sql_table='actor_terms')

# the sphinx client is what will perform the computation
factor.AttachSphinxClient(cl, db)

# let's set the number of facet values returned to 5
factor.SetMaxNumValues(5)

# computing the actor facet for the query "drama"
factor.Compute('drama')

# let's see how this looks like
print factor

# setting up a custom sorting function
factor.SetGroupFunc('sum(user_rating_attr * nb_votes_attr)')

# @groupfunc holds the value of the custom function
factor.SetOrderBy('@groupfunc', order='desc')

# computing the actor facet for the query "drama"
factor.Compute('drama')

# let's what we get
print factor

## Performance, Caching and Multiple Facets

# sql_table is optional and defaults to (facet_name)_terms
fyear = Facet('year', sql_table=None)

# let's put the facets in a group for faster computation
facets = FacetGroup(fyear, factor)

# as always Sphinx is what carries the computation
facets.AttachSphinxClient(cl, db)

# finally compute these two facets at once
facets.Compute("drama", caching=False)

# turning caching on
facets.caching = True

# computing facets twice with caching on
facets.Compute('drama')
facets.Compute('drama')
assert(facets.time == 0)

# this always overrides facets.caching
facets.Compute('drama', caching=False)
assert(facets.time > 0)

# turning preloading on and caching off
facets.preloading = True
facets.caching = False

# preloading the facets for the query: "drama"
facets.Preload('drama')

# this takes the value from the cache
facets.Compute('drama')
assert(facets.time == 0)

## Playing With Multi-field Queries

# creating a multi-field query
query = MultiFieldQuery({'actor':'actors', 'genre':'genres'})

# parsing a multi-field query
query.Parse('@year 1999 @genre drama @actor harrison ford')

# the query the user will see: '(@year 1999) (@genre drama) (@actor harrison ford)'
print query.user

# the query that should be passed to Sphinx: '(@genres drama) (@actors harrison ford)'
print query.sphinx

# let's toggle the year field off
query.ToggleOff('@year 1999')

# the query the user will see: '(@-year 1999) (@genre drama) (@actor harrison ford)'
print query.user

# the query that should be sent to sphinx: '(@genres drama) (@actors harrison ford)'
print query.sphinx

# is the query term '@year 1999' in query
assert('@year 1999' in query)

# a connical form of this query: (@actors harrison ford) (@genres drama)
print query.uniq

# setting cl to extended matching mode
cl.SetMatchMode(sphinxapi.SPH_MATCH_EXTENDED2)

# and now passing a multi-field query object
factor.Compute(query)

# and looking at the results
print factor

## Retrieving Results

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

# let's perform a simple query
results = cl.Query('movie')

# and fetch the results form the DB
hits = db_fetch.Fetch(results)

# looking at the hits
print hits

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
from config import sphinx_config
cl = FSphinxClient.FromConfig(sphinx_config)

# or as a path to a configuration file
cl = FSphinxClient.FromConfig('./config/sphinx_config.py')

# querying for "movie"
cl.Query('movie')