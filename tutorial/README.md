This tutorial on fSphinx is aimed at users with some familiarity with [Sphinx] [1]. If you are not familiar with Sphinx I invite you to check out the excellent book from [O'Reilly] [2] or to go through the Sphinx [documentation] [3].

Throughout this tutorial we will assume that the current working directory is the "tutorial" directory. All code samples can be found in the file "./test.py".

Setting up and Indexing Data
----------------------------

This tutorial uses a scrape of the top 400 movies found on IMDb. First let's create a MySQL database called "fsphinx" with user and password "fsphinx". 

In a MySQL shell type:

    create database geonames character set utf8;
    create user 'fsphinx'@'localhost' identified by 'fsphinx';
    grant ALL on fsphinx.* to 'fsphinx'@'localhost';
    
Now let's load the data into this database:

    mysql -u fsphinx -D fsphinx -p < ./sql/imdb_top400.data.sql
    
Let Sphinx index the data (assuming indexer is in /user/local/sphinx/):

    /user/local/sphinx/indexer -c ./config/indexer.conf --all
    
And let searchd serve the index:

    /user/local/sphinx/searchd -c ./config/indexer.conf

You can now create a file called "_test.py": 

    # importing the required modules
    import sphinxapi
    from fsphinx import *

    # let's build a Sphinx Client
    cl = sphinxapi.SphinxClient()

    # assuming searchd is running on 9315
    cl.SetServer('localhost', 9315)

    # let's have a handle to our fsphinx database
    db = utils.database(dbn='mysql', db='fsphinx', user='fsphinx', passwd='fsphinx')

Setting up the Facets
---------------------

Every facet in fSphinx must be declared as an attribute either single or multi-valued. For the director facet ./config/indexer.conf you must have the following lines:

    # needed to create the director facet
    sql_attr_multi = \
        uint director_attr from query; \
        select imdb_id, imdb_director_id from directors

Additionaly every facet (except facets with numerical term values) must have a coresponding MySQL table which maps ids to terms. Let's have a look at the director_terms table:

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

Going through indexer.conf, we see that we have at our disposal the following facets: year, genre, director, actor and plot keywords. Each but the year facet has a corresponding MySQL table which holds their ids and terms. When facet terms are numerical, as in the year facet, there is no need to create an additional MySQL table.

Playing with Facets
-------------------

Creating a facet to be computed is easy:

    # sql_table is optional and defaults to (facet_name)_terms
    factor = Facet('actor', sql_table='actor_terms')
    
    # the sphinx client is what will perform the computation
    factor.AttachSphinxClient(cl, db)
    
    # let's set the number of facet values returned to 5
    factor.SetMaxNumValues(5)

Here we have created a new facet of name "actor" with terms found in the MySQL table named "actor_terms". We also need to attach a SphinxClient to perform the computation and pass a handle to our database to fetch the results. Additionaly we have limited the number of facet values to 5.

We can proceed and compute this facet:

    # computing the actor facet for the query "drama"
    factor.Compute('drama')

At this point it's important to step back and understand what happened. fSphinx called Sphinx to process to query. The results can now be found in factor.results which holds some basic statistics such as the time it took or the total number of facet values found. Also the list of facet values is found in factor.results['matches']. 

Each facet value is a dictionnary with following key-values:
    
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

You can pass to SetGroupSort any Sphinx expression wrapped by an aggreate function such as avg(), min(), max() or sum(). Sphinx [provides] [4] a rather long list of functions and operators which can be used in this expression.

Let's addtionnaly order the final results by the value of this expression:

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

Most of the time we have many facets from which we may want to refine from. Calling Sphinx each time would be rather unefficient. Also we'd like to make good use of some the great optimization of Sphinx when multiple queries are processed. Since facet computation is expensive, we'd like to make sure the computation is cached when possible.

Let's first create another facet to refine by year:

    # sql_table is optional and defaults to (facet_name)_terms
    fyear = Facet('year', sql_table=None)
    
Since year is a numerical facet, we did not require to have a MySQL table for the term values, so we simply passe None to the sql_table parameter.

Now we can create a group of facet which will carry the computation of the year and actor facet all at once:

    # let's put the facets in a group for faster computation
    facets = FacetGroup(fyear, factor)

    # as always Sphinx is what carries the computation
    facets.AttachSphinxClient(cl, db)

    # finally compute these two facets at once
    facets.Compute("drama", caching=False)

Cool if we were to print the facet group, we would have the same results as if the year and actor facet had been computed independantly. Note that we can setup each facet differently, say we'd like to group sort by count on the year facet but by popularity on the actor facet.

As we discussed above facet computation can be expensive, so we better make sure that we don't perform the same computation more than once. Let's turn caching on.

    # turning caching on
    facets.caching = True

And we can perform our computation as usual:

    # computing facets twice with caching on
    facets.Compute('drama')
    facets.Compute('drama')
    assert(facets.time == 0)
    
    # this always overrides facets.caching
    facets.Compute('drama', caching=False)
    assert(facets.time > 0)
    
We can also preload our facets once and never cache the results afterwards:

    # turning preloading on and caching off
    facets.preloading = True
    facets.caching = False
    
    # preloading the facets for the query: "drama"
    facets.Preload('drama')
    
    # this takes the value from the cache
    facets.Compute('drama')
    assert(facets.time == 0)

To preload your facets starting from a query (usually the empty query) and recursively down to every facet values, have a look at the tool preload_facets.py (see section on tools).
    
Playing With Multi-field Queries
--------------------------------

A crucial aspect of faceted search is to let the user refine by facet values. A user may also want to toggle on or off different facet values and see the results. To do so easily fSphinx supports a multi-field query object.

    # creating a multi-field query
    query = MultiFieldQuery({'actor':'actors', 'genre':'genres'})
   
This creates a query object which maps a user search in "actor" or "genre" to a Sphinx search in the fields "actors" or "genres" respectively.

Now let's parse a query string:

    # parsing a multi-field query
    query.Parse('@year 1999 @genre drama @actor harrison ford')

The multi-field query object has a couple of representation. The first one is the query as represented by the user.

    # the query the user will see: '(@year 1999) (@genre drama) (@actor harrison ford)'
    print query.user

Then there is the query which will be passed to Sphinx. Since we mapped genre to genres, here is what we get:

    # the query that should be sent to sphinx: '(@year 1999) (@genres drama) (@actors harrison ford)'
    print query.sphinx

We can toggle any term on or off and see how the user and Sphinx query differs:

    # let's toggle the year field off
    query.ToggleOff('@year 1999')

    # the query the user will see: '(@-year 1999) (@genre drama) (@actor harrison ford)'
    print query.user

    # the query that should be passed to Sphinx: '(@genres drama) (@actors harrison ford)'
    print query.sphinx

In order to know if a facet value has been selected, the "in" operator is overriden in the multi-field query object:

    # is the query term '@year 1999' in query
    assert('@year 1999' in query)

There is a unique / canonical representation of the query which is mainly used for caching which is accessed by:

    # a connical form of this query: (@actors harrison ford) (@genres drama)
    print query.uniq

Finally we can pass the pass a query object to Compute as if it was a normal string. However the SphinxClient must suppport multi-field queries and so set the match mode to extended2:

    # setting cl to extended matching mode
    cl.SetMatchMode(sphinxapi.SPH_MATCH_EXTENDED2)

    # and now passing a multi-field query object
    fyear.Compute(query)
    
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

fSphinx internally uses an object called DBFetch which retrieves the terms from the facets. This object may be used independantly:
        
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
    
The object "hits" behaves like a normal sphinx results but each match has an additional field called "@hit" for each field value retrieved. Let's see how this looks like (only showing the first result and omitting some lengthy attributes):

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

Putting Everything Together
---------------------------

fSPhinx can replace a normal SphinxClient entirely. Every feature discussed above can be attached to the client.

Let's create an FSphinxClient:
    
    # creating a sphinx client
    cl = FSphinxClient()

    # it behaves exactly like a normal SphinxClient
    cl.SetServer('localhost', 9315)

Now let's attach the db_fetch object to retrieve results from the db:
    
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
    
The results can be found cl.query, cl.hits and cl.facets and are the same as if computed independantly.
    
Playing With Configuration Files
--------------------------------

Lastly we can put all these parameters in a single configuration file. A configuration file is a plain python file which creates a client called "cl" in its local namespace. Have a look at "./config/sphinx_config.py".

Let's create a client using a configuration file:

    # as a module
    from config import sphinx_config
    cl = FSphinxClient.FromConfig(sphinx_config)
    
    # or as a path to a configuration file
    cl = FSphinxClient.FromConfig('./config/sphinx_config.py')

Now we can run our query as usual:
    
    # querying for "movie"
    cl.Query('movie')

Additional Tools
----------------    

A configuration file can be passed to "search.py" at the command line:

    python ../tools/search.py -c config/sphinx_config.py 'harrison ford'

This tool provides a command line interface to fSphinx which could be used for testing and debugging.
    
The facets can be pre-computed or pre-loaded using the tool "preload_facets.py".

    python ../tools/preload_facets.py -c config/sphinx_config.py ''
    
This will compute the facets given in "sphinx_config.py" for the empty query (full scan) and perform this computation for every facet value under it.

Cool Now I'd like An Interface
------------------------------

Now that you got yourself setup on the backend, you might still want an interface. You may also be interested in choosing different visualizations of your facets. If this is the case have a look at [Cloud Mining] [5] (coming soon). Cloud Mining uses the configuration file (discussed above) to build a complete search interface.

Ok I don't even have data, how do I start?
------------------------------------------

If you'd like to scrape websites on a massive scale, check out [Mass Scrapping] [6]. It's a tool I made which makes it easy to retrieve, extract and populate data. It's the tool used to download all of IMDb in order to make [this] [5].

[1]: http://sphinxsearch.com
[2]: http://oreilly.com/catalog/9780596809553 
[3]: http://sphinxsearch.com/docs/
[4]: http://sphinxsearch.com/docs/manual-2.0.1.html#expressions
[5]: http://imdb.cloudmining.net
[6]: https://github.com/alexksikes/mass-scraping