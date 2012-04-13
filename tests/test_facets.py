from __init__ import *

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

# @groupfunc holds the value of the custom grouping function
factor.SetOrderBy('@groupfunc', order='desc')

# computing the actor facet for the query "drama"
factor.Compute('drama')

# let's what we get
print factor

# sql_table is optional and defaults to (facet_name)_terms
fyear = Facet('year', sql_table=None)

# let's put the facets in a group for faster computation
facets = FacetGroup(fyear, factor)

# as always Sphinx is what carries the computation
facets.AttachSphinxClient(cl, db)

# finally compute these two facets at once
facets.Compute("drama", caching=False)

# turning caching on
facets.AttachCache(cache)

# computing facets twice with caching on
facets.Compute('drama')
facets.Compute('drama')
assert(facets.time == 0)

# this makes sure the facet computation is not fetched from the cache
facets.Compute('drama', caching=False)
assert(facets.time > 0)