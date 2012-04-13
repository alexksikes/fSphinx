## Setting up

# importing required modules
import sphinxapi
from fsphinx import *

# let's build a Sphinx Client
cl = sphinxapi.SphinxClient()

# assuming searchd is running on 9315
cl.SetServer('localhost', 9315)

# let's have a handle to our fsphinx database
db = utils.database(dbn='mysql', db='fsphinx', user='fsphinx', passwd='fsphinx')

# let's have a cache for later use
cache = RedisCache(db=0)