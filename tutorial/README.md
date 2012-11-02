This tutorial on fSphinx is aimed at users with some familiarity with [Sphinx][1]. If you are not familiar with Sphinx, I invite you to check out the excellent book from [O'Reilly][2] or to go through the Sphinx [documentation][3].

Throughout this tutorial we will assume that the current working directory is the "tutorial" directory. All the code samples can be found in the file "./test.py".

Setting up and Indexing Data
----------------------------

This tutorial uses a scrape of the top 400 movies found on IMDb. First let's create a MySQL database called "fsphinx" with user and password "fsphinx". 

In a MySQL shell type:

    create database fsphinx character set utf8;
    create user 'fsphinx'@'localhost' identified by 'fsphinx';
    grant ALL on fsphinx.* to 'fsphinx'@'localhost';
    
Now let's load the data into this database:

    mysql -u fsphinx -D fsphinx -p < ./sql/imdb_top400.data.sql
    
Let Sphinx index the data (assuming indexer is in /user/local/sphinx/):

    /user/local/sphinx/indexer -c ./config/sphinx_indexer.conf --all
    
And let searchd serve the index:

    /user/local/sphinx/searchd -c ./config/sphinx_indexer.conf

You can now create a file called "_test.py": 

    # importing the required modules
    import sphinxapi
    from fsphinx import *

    # let's build a Sphinx Client
    cl = sphinxapi.SphinxClient()

    # assuming searchd is running on 10001
    cl.SetServer('localhost', 10001)

    # let's have a handle to our fsphinx database
    db = utils.database(dbn='mysql', db='fsphinx', user='fsphinx', passwd='fsphinx')

    # let's have a cache for later use
    cache = RedisCache(db=0)

Setting up the Facets
---------------------

Every facet in fSphinx must be declared as an attribute either single or multi-valued. The file "./config/sphinx_indexer.conf" holds Sphinx indexing configurations. For the director facet, this file must have the following lines:

    # needed to create the director facet
    sql_attr_multi = \
        uint director_attr from query; \
        select imdb_id, imdb_director_id from directors

Additionally every facet (except facets with numerical value terms) must have a corresponding MySQL table which maps ids to terms. Let's have a look at the director_terms table:

    select * from director_terms limit 5;
    +----+------------------+
    | id | director         |
    +----+------------------+
    |  5 | Ingmar Bergman   |
    | 19 | Federico Fellini |
    | 33 | Alfred Hitchcock |
    | 36 | Buster Keaton    |
    | 37 | Gene Kelly       |
    +----+------------------+

Going through sphinx_indexer.conf, we see that we have at our disposal the following facets: year, genre, director, actor and plot keywords. Each but the year facet has a corresponding MySQL table which maps ids to term values. When the facet terms are numerical, as in the year facet, there is no need to create an additional MySQL table.

Playing with Facets
-------------------

Creating a facet to be computed is easy:

    # sql_table is optional and defaults to (facet_name)_terms
    factor = Facet('actor', sql_table='actor_terms')

    # the sphinx client is what will perform the computation
    factor.AttachSphinxClient(cl, db)

    # let's set the number of facet values returned to 5
    factor.SetMaxNumValues(5)

Here we have created a new facet of name "actor" with terms found in the MySQL table named "actor_terms". We also need to attach a SphinxClient to perform the computation and pass a handle to our database to fetch the results. Additionally we have limited the number of facet values to 5.

We can proceed and compute this facet:

    # computing the actor facet for the query "drama"
    factor.Compute('drama')

At this point it's important to step back and understand what happened. fSphinx called Sphinx to process the query. The results are then found in factor.results. This later holds some basic statistics such as the time it took to compute or the total number of facet values found. The list of facet values is providing in factor.results['matches']. 

Each facet value is a dictionary with the following key-values:
    
    @groupby: id of the facet value indexed by Sphinx.
    @term: term of the facet value fetched from MySQL.
    @count: number of times this facet term appears.
    @groupfunc: value of a custom grouping function (see next section).
    @selected: whether this facet has been selected (see section on multi-field queries).

In fact we can print the facet and see for ourselves:

    # let's see how this looks like
    print factor
    
    actor: (5/3563 values group sorted by "@count desc" in 0.030 sec.)
            1. Al Pacino, @count=7, @groupby=199, @groupfunc=7, @selected=False
            2. John Qualen, @count=6, @groupby=702798, @groupfunc=6, @selected=False
            3. Morgan Freeman, @count=6, @groupby=151, @groupfunc=6, @selected=False
            4. Robert De Niro, @count=9, @groupby=134, @groupfunc=9, @selected=False
            5. Robert Duvall, @count=6, @groupby=380, @groupfunc=6, @selected=False

By default facets are grouped by their terms, sorted by how many times they appear and ordered alphabetically. Let's group sort our facet by a custom function which models popularity.

    # setting up a custom sorting function
    factor.SetGroupFunc('sum(user_rating_attr * nb_votes_attr)')

You can pass to SetGroupSort any Sphinx expression wrapped by an aggregate function such as avg(), min(), max() or sum(). Sphinx [provides][4] a rather long list of functions and operators which can be used in this expression.

Let's additionally order the final results by the value of this expression:

    # @groupfunc holds the value of the custom grouping function
    factor.SetOrderBy('@groupfunc', order='desc')

Now we can compute the facet and print it:

    # computing the actor facet for the query "drama"
    factor.Compute('drama')

    # let's what we get
    print factor
    
    actor: (5/3563 values group sorted by "@groupfunc desc" in 0.012 sec.)
            1. Morgan Freeman, @count=6, @groupby=151, @groupfunc=1218292.125, @selected=False
            2. Robert De Niro, @count=9, @groupby=134, @groupfunc=933700.375, @selected=False
            3. Al Pacino, @count=7, @groupby=199, @groupfunc=868737.0, @selected=False
            4. Robert Duvall, @count=6, @groupby=380, @groupfunc=800953.3125, @selected=False
            5. John Cazale, @count=5, @groupby=1030, @groupfunc=676553.75, @selected=False

Performance, Caching and Multiple Facets
----------------------------------------

Most of the time we have many facets from which we may want to refine from. Calling Sphinx each time would be rather inefficient. Also we'd like to make good use of some of the great optimization Sphinx provides with batched queries. Also since facet computation is expensive, we'd like to make sure the computation is cached when possible.

Let's first create another facet to refine by year:

    # sql_table is optional and defaults to (facet_name)_terms
    fyear = Facet('year', sql_table=None)
    
Since year is a numerical facet, we didn't need a MySQL table for the term values. Instead we explicitely pass "None" to the sql_table parameter.

Now we can create a group of facets which will carry the computation of the year and actor facet all at once:

    # let's put the facets in a group for faster computation
    facets = FacetGroup(fyear, factor)

    # as always Sphinx is what carries the computation
    facets.AttachSphinxClient(cl, db)

    # finally compute these two facets at once
    facets.Compute("drama", caching=False)

Cool if we were to print this group of facets, we would have the same results as if the year and actor facets had been computed independently. Note that we can setup each facet differently, say we'd like to group sort by count on the year facet but by popularity on the actor facet.

As we discussed above the facet computation can be expensive, so we better make sure we don't perform the same computation more than once. Let's have a cache on our facets.

    # turning caching on
    facets.AttachCache(cache)
    
The object cache is the RedisCache we have previsouly created. The cache has a couple of options you can setup such as the amount of memory to use and the expiration on the keys. Each facet computation within the group is cached independantly.

Now we can perform our computation as usual:

    # computing facets twice with caching on
    facets.Compute('drama')
    facets.Compute('drama')
    assert(facets.time == 0)
    
    # this makes sure the facet computation is not fetched from the cache
    facets.Compute('drama', caching=False)
    assert(facets.time > 0)
    
We can also preload the facet cache computation within the cache. To preload your facets starting from a query (usually the empty query) and recursively down to every facet values, have a look at the tool preload_facets.py (see section on tools).

Playing With Multi Field Queries
--------------------------------

A crucial aspect of faceted search is to let the user refine by facet values. A user may also want to toggle on or off different facet values and see the results. To do so easily fSphinx supports a multi-field query object.

    # creating a multi-field query
    query = MultiFieldQuery(user_sph_map={'actor':'actors', 'genre':'genres'})
   
This creates a query parser for a multi-field which maps the user search in "actor" or "genre" to a Sphinx search in the fields "actors" or "genres" respectively.

Now let's parse a query string:

    # parsing a multi-field query
    query.Parse('@year 1999 @genre drama @actor harrison ford')

The multi-field query object has a couple of representations. The first one is the query as represented by the user.

    # the query the user will see: '(@year 1999) (@genre drama) (@actor harrison ford)'
    print query.user

Then there is the query which will be passed to Sphinx. Since we mapped genre to genres, here is what we get:

    # the query that should be sent to sphinx: '(@year 1999) (@genres drama) (@actors harrison ford)'
    print query.sphinx

We can toggle any terms on or off and see how the user and the Sphinx query differ:

    # let's toggle the year field off
    query['@year 1999'].ToggleOff()

    # the query the user will see: '(@-year 1999) (@genre drama) (@actor harrison ford)'
    print query.user

    # the query that should be passed to Sphinx: '(@genres drama) (@actors harrison ford)'
    print query.sphinx

In order to know if a facet value has been selected, the "in" operator is overloaded:

    # is the query term '@year 1999' in query
    assert('@year 1999' in query)

There is a unique / canonical representation of the query which could be used for caching:

    # a canonical form of this query: (@actors harrison ford) (@genres drama)
    print query.uniq

Another representation is in the form of a pretty url:
    
    # a unique url path representing this query: /actor/harrison+ford/genre/drama/year/*1999/?ot=210
    print query.ToPrettyUrl()

Finally we can pass a query object to Compute as if it was a normal string. However the SphinxClient match mode must be set to extended2:

    # setting cl to extended matching mode
    cl.SetMatchMode(sphinxapi.SPH_MATCH_EXTENDED2)

    # and now passing a multi-field query object
    factor.Compute(query)
    
    # and looking at the results
    print factor
    
    actor: (5/25 values group sorted by "@groupfunc desc" in 0.020 sec.)
        1. Frederic Forrest, @count=2, @groupby=2078, @groupfunc=161016.6875, @selected=False
        2. Harrison Ford, @count=2, @groupby=148, @groupfunc=161016.6875, @selected=True
        3. Jerry Ziesmer, @count=1, @groupby=956310, @groupfunc=137119.265625, @selected=False
        4. G.D. Spradlin, @count=1, @groupby=819525, @groupfunc=137119.265625, @selected=False
        5. Kerry Rossall, @count=1, @groupby=743953, @groupfunc=137119.265625, @selected=False
        6. James Keane, @count=1, @groupby=443856, @groupfunc=137119.265625, @selected=False

We see that the facet value "Harrison Ford" has been properly marked as selected.

Retrieving Results
------------------

fSphinx internally uses an object called DBFetch which retrieves the terms from the facets. This object may be used independently:
        
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

The sql parameter is a SQL statement with the special variable $id which will be replaced by the ids that Sphinx returns. Here we are asking to fetch the title, year, plot and list of directors from the DB.

    # let's perform a simple query
    results = cl.Query('movie')
    
    # and fetch the results form the DB
    hits = db_fetch.Fetch(results)
    
The object "hits" behaves like a normal sphinx result set. However each match has an additional field called "@hit" for each field value retrieved. Let's see how this looks like (only showing the first result and omitting some lengthy attributes):

    # looking at the hits
    print hits
    
    matches: (7/7 documents in 0.000 sec.)
    1. document=56687, weight=1
    year_attr=1962, user_rating_attr=0.800000011921, runtime_attr=134
            plot=In a decaying Hollywood mansion, Jane Hudson, a former child star, and her sister Blanche, a movie queen forced into retirement after a crippling accident, live in virtual isolation.
            directors=Robert Aldrich
            imdb_id=56687
            title=What Ever Happened to Baby Jane?
            year=1962
            filename=e9278ce4f803b6795a83174a86f3289d
            
    ...
    
    words:
    1. "movie": 7 documents, 7 hits
    
Additionnaly we may want to post-process the results returned by DBFetch. For example we grouped the directors with a phony separator. Let's have DBFetch return these values as a list instead of as a concatenated string.

    # make sure directors are returned as a list instead of as a concatenated string
    db_fetch.post_processors = [SplitOnSep('directors', sep='@#@')]
    
There are post-processors to build excerpts and to highlight results or you can write your own.

Full text search is fine, how about item based search?
------------------------------------------------------

To look up similar things and search for whole items, have a look at [SimSearch][7].

    # make sure you have SimSearch installed
    import simsearch

    # assuming we have created a similarity search index
    index = simsearch.ComputedIndex('./data/sim-index/')

    # and a query handler to query it
    handler = simsearch.QueryHandler(index)

    # and wrap cl to give it similarity search abilities
    cl = simsearch.SimClient(cl, handler)
    
    # order by similarity search scores
    cl.SetSortMode(sphinxapi.SPH_SORT_EXPR, 'log_score_attr')  

    # looking for movies similar to Terminator (movie id = 88247)
    cl.Query('@similar 88247')

Putting Everything Together
---------------------------

fSphinx can replace a normal SphinxClient entirely. Every feature discussed above can be attached to the client.

Let's create an FSphinxClient:
    
    # creating a sphinx client
    cl = FSphinxClient()

    # it behaves exactly like a normal SphinxClient
    cl.SetServer('localhost', 10001)

Now let's attach a db_fetch object to retrieve results from the db:
    
    # get the results from the db
    cl.AttachDBFetch(db_fetch)

Let's attach the facets we made above:

    # attach the facets
    cl.AttachFacets(fyear, fgenre)

And finally we can run the query:
    
    # running the query
    cl.Query('movie')

    # or pass a MultiFieldQuery
    cl.Query(query)
    
The results can be found cl.query, cl.hits and cl.facets and are the same as if computed independently.
    
Playing With Configuration Files
--------------------------------

Lastly we can put all these parameters in a single configuration file. A configuration file is a plain python file which creates a client called "cl" in its local name space. Have a look at "./config/sphinx_client.py".

Let's create a client using a configuration file:
    
    # create a fSphinx client from a configuration file
    cl = FSphinxClient.FromConfig('./config/sphinx_client.py')

Now we can run our query as usual:
    
    # querying for "movie"
    cl.Query('movie')

Additional Tools
----------------    

A configuration file can be passed to "search.py" at the command line:

    python ../tools/search.py -c config/sphinx_client.py 'harrison ford'

This tool provides a command line interface to fSphinx which could be used for testing and debugging.
    
The cache can be pre-computed or pre-loaded using the tool "preload_cache.py".

    python ../tools/preload_cache.py -c config/sphinx_client.py ''
    
This will compute the facets given in "sphinx_client.py" for the empty query (full scan) and perform this computation for every facet value under it.  It is important to note that by default every preloaded facet will always persist in the cache (the key will not expire). It is assumed that your configuration file has either a cache attached to the facets or to the entire client. In the later case the computation of the search is also cached along with the computation of the facets.

Cool Now I'd like an Interface
------------------------------

Now that you got yourself setup on the backend, you might still want an interface. You may also be interested in choosing between different visualizations for your facets. If this is the case, have a look at [Cloud Mining][8]. Cloud Mining uses the configuration file (discussed above) to build a complete search interface.

    python /path/to/cloudiminig/tools/serve_instance -c config/sphinx_client.py

OK I don't even have data, how do I start?
------------------------------------------

If you'd like to scrape websites on a massive scale, feel free to give [Mass Scrapping][6] a shoot. It's a tool I made which makes it easy to retrieve, extract and populate data. It was used to download all the content from the IMDb website in order to make [this][5].

[1]: http://sphinxsearch.com
[2]: http://oreilly.com/catalog/9780596809553 
[3]: http://sphinxsearch.com/docs/
[4]: http://sphinxsearch.com/docs/manual-2.0.1.html#expressions
[5]: http://imdb.cloudmining.net
[6]: https://github.com/alexksikes/mass-scraping
[7]: https://github.com/alexksikes/SimSearch
[8]: https://github.com/alexksikes/cloudmining
