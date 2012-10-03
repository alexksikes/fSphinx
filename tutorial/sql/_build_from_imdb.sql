# this is for me, do not use!
# sql file that was used to build the test database from the real IMDb database

# let's get the most popular movies on imdb
create table titles like imdb.titles;
insert titles select * from imdb.titles where user_rating >= 0.8 and nb_votes >= 10000;

# directors
create table fsphinx.directors like imdb.directors;
insert fsphinx.directors 
    select t1.*
        from imdb.directors as t1
    inner join fsphinx.titles as t2 
        where t1.imdb_id = t2.imdb_id

create table fsphinx.director_terms like imdb.director_tags;
insert director_terms 
    select imdb_director_id, director_name 
    from fsphinx.directors
    group by imdb_director_id; 
    
# actors
create table fsphinx.casts like imdb.casts;
insert fsphinx.casts
    select t1.*
        from imdb.casts as t1
    inner join fsphinx.titles as t2 
        where t1.imdb_id = t2.imdb_id

create table fsphinx.actor_terms like imdb.actor_tags;
insert fsphinx.actor_terms
    select imdb_actor_id, actor_name 
    from casts
    group by imdb_actor_id; 

# plot_keywords (we grab all keywords from all_plot_keywords)
create table fsphinx.plot_keywords like imdb.all_plot_keywords;
insert fsphinx.plot_keywords
    select t1.*
        from imdb.all_plot_keywords as t1
    inner join fsphinx.titles as t2 
        where t1.imdb_id = t2.imdb_id

create table fsphinx.plot_keyword_terms like imdb.plot_keyword_tags;
set @i := 0; 
insert fsphinx.plot_keyword_terms
    select @i := @i + 1, plot_keyword 
    from plot_keywords
    group by plot_keyword 
    order by plot_keyword;

# genres
create table fsphinx.genres like imdb.genres;
insert fsphinx.genres
    select t1.*
        from imdb.genres as t1
    inner join fsphinx.titles as t2 
        where t1.imdb_id = t2.imdb_id

create table fsphinx.genre_terms like imdb.genre_tags;
set @i := 0; 
insert fsphinx.genre_terms
    select @i := @i + 1, genre 
    from genres
    group by genre 
    order by genre;

# test it ...
select 
    imdb_id, filename, title, year, user_rating, nb_votes, type_tv_serie, type_other, 
    release_date, release_date_raw, plot, awards, runtime, 
    color, aspect_ratio, certification, 
    cover_url, gallery_url, trailer_url, release_date_raw, 
    (select group_concat(distinct director_name separator '@#@') from directors as d where d.imdb_id = t.imdb_id) as directors, 
    (select group_concat(distinct actor_name separator '@#@') from casts as c where c.imdb_id = t.imdb_id) as actors, 
    (select group_concat(distinct genre separator '@#@') from genres as g where g.imdb_id = t.imdb_id) as genres, 
    (select group_concat(distinct plot_keyword separator '@#@') from plot_keywords as p where p.imdb_id = t.imdb_id) as plot_keywords
from titles as t 
where imdb_id in (111161, 111161)

# finally create the cache
create table fsphinx.cache like imdb.cache;

# create the fsphinx user for testing ...
create user 'fsphinx'@'localhost' identified by 'fsphinx';
grant select on fsphinx.* to 'fsphinx'@'localhost';
grant insert on fsphinx.cache to 'fsphinx'@'localhost';
grant update on fsphinx.cache to 'fsphinx'@'localhost';
grant delete on fsphinx.cache to 'fsphinx'@'localhost';

# dump the schema only and full data and get into mysql
# >> mysqldump --no-data -p fsphinx > sql/imdb_top400.schema.sql
# >> mysqldump -p fsphinx > sql/imdb_top400.data.sql
# >> mysql -u fsphinx -D fsphinx -p