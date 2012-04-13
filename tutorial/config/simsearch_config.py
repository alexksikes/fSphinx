import simsearch
import web

# database parameters
db_params = dict(user='fsphinx', passwd='fsphinx', db='fsphinx')

# list of SQL queries to fetch the features from
sql_features = [
    'select imdb_id as item_id, plot_keyword as feature from plot_keywords',
]

# this is only used for sim_sphinx (see doc)
def sphinx_setup(cl):
    import sphinxapi
    
    # custom sorting function for the search
    cl.SetSortMode(sphinxapi.SPH_SORT_EXPR, 'log_score_attr')
    
    # custom grouping function for the facets
    group_func = 'sum(log_score_attr)'
    
    # setup sorting and ordering of each facet 
    if hasattr(cl, 'facets'):
        for f in cl.facets:
            f.SetGroupFunc(group_func)

# the simsearch index should only be loaded once in memory
web.config.sim_index = simsearch.load_index('./data/sim_index/index.dat', once=web.config.get('sim_index'))

# we wrap a Sphinx client for similarity search
cl = simsearch.simsphinx.SimSphinxWrap(web.config.sim_index)

# set the number of items to match
cl.SetMaxItems(10000)

# special sphinx setup in similarity search mode
cl.SetSphinxSetup(sphinx_setup)
