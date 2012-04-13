from __init__ import *

# we start with the following user query
query = 'movie @year 1999 @-genre drama (@actor harrison ford)'

# and transform the query into a pretty url 
# result should be: movie/actor=harrison+ford/genre=*drama/year=1999/?ot=0321
url = QueryToPrettyUrl(query)
print url

# and now back to a user query
print PrettyUrlToQuery(url)

# try with url parameters
url = QueryToPrettyUrl(query, root='/search/', keep_order=True, s=0, so='relevance')
print url

# and back to a user query
print PrettyUrlToQuery(url, root='/search/')

# some more ...
print QueryToPrettyUrl('movie', root='/search/')

url = 'author=Arjan+Durresi/keyword=networks|systems/?ot=201'
print PrettyUrlToQuery(url, root='/search/')