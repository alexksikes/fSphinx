from __init__ import *

## Full text search is fine, how about item based search!

# we assume you have SimSearch configured 
from config import simsearch_config

# and wrap cl to give it similarity search abilities
cl = simsearch_config.cl.Wrap(cl)

# looking for movies similar to Terminator (movie id = 88247)
cl.Query('(@similar 88247) movie')