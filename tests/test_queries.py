from __init__ import *

# sql_table is optional and defaults to (facet_name)_terms
factor = Facet('actor', sql_table='actor_terms')

# the sphinx client is what will perform the computation
factor.AttachSphinxClient(cl, db)

# let's set the number of facet values returned to 5
factor.SetMaxNumValues(5)

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