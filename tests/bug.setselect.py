# This bug has been fixed as of Sphinx 2.0.2-beta (r3019) thanks

# submitted: http://sphinxsearch.com/bugs/view.php?id=792

# Suppose you have an index with an attribute called user_rating_attr with value between 0 and 1.

import sphinxapi

# let's build a Sphinx Client
cl = sphinxapi.SphinxClient()

# assuming searchd is running on 9315
cl.SetServer('localhost', 9315)
cl.SetLimits(0, 1)

query = 'movie'

# Each query run separately

print 'one query at a time'
cl.SetSelect('user_rating_attr, 1*user_rating_attr as @score')
print cl.Query(query)['matches']

# [{'id': 56687L, 'weight': 1L, 'attrs': {'@score': 0.80000001192092896, 'user_rating_attr': 0.80000001192092896}}]

# The score is 0.80 as expected

cl.SetSelect('user_rating_attr, 100*user_rating_attr as @score')
print cl.Query(query)['matches']

# [{'id': 56687L, 'weight': 1L, 'attrs': {'@score': 80.0, 'user_rating_attr': 0.80000001192092896}}]

# The score is 80 as expected

# These are the same queries but run in batch with RunQueries.

print 'all queries at once'
cl.SetSelect('user_rating_attr, 1*user_rating_attr as @score')
cl.AddQuery(query)
cl.SetSelect('user_rating_attr, 100*user_rating_attr as @score')
cl.AddQuery(query)
results = cl.RunQueries()

print results[0]['matches']
print results[1]['matches']

# [{'id': 56687L, 'weight': 1L, 'attrs': {'@score': 80.0, 'user_rating_attr': 0.80000001192092896}}]
# [{'id': 56687L, 'weight': 1L, 'attrs': {'@score': 80.0, 'user_rating_attr': 0.80000001192092896}}]

# The score is 80 for both !!!