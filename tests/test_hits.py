from __init__ import *

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

# make sure directors are returned as a list instead of as a concatenated string
db_fetch.post_processors = [SplitOnSep('directors', sep='@#@')]