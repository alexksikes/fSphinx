# This bug has been fixed as of Sphinx 2.0.2-beta (r3019) thanks

from __init__ import *

# sql_table is optional and defaults to facet_name_terms
factor = Facet('actor', sql_table='actor_terms')

# the sphinx client is what will perform the computation
factor.AttachSphinxClient(cl, db)

# setting up a custom sorting function
factor.SetGroupFunc('avg(nb_votes_attr*user_rating_attr)')

# let's set the number of facet values (defaults to 15)
factor.SetMaxNumValues(1)

factor.Compute('drama')
print factor

# sql_table is optional and defaults to facet_name_terms
fyear = Facet('year', sql_table=None)

# the sphinx client is what will perform the computation
fyear.AttachSphinxClient(cl, db)

# setting up a custom sorting function
fyear.SetGroupFunc('avg(100*user_rating_attr)')

# let's set the number of facet values (defaults to 15)
fyear.SetMaxNumValues(1)

fyear.Compute('drama')
print fyear

# let's build a Sphinx Client
cl = sphinxapi.SphinxClient()

# assuming searchd is running on 9315
cl.SetServer('localhost', 9315)

# let's put the facets in a group for faster computation
facets = FacetGroup(factor, fyear)

# as always Sphinx is what carries the computation
facets.AttachSphinxClient(cl, db)

facets.Compute('drama')
print facets