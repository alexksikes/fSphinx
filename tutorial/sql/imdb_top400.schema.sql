-- MySQL dump 10.11
--
-- Host: localhost    Database: fsphinx
-- ------------------------------------------------------
-- Server version	5.0.32-Debian_7etch1-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `actor_terms`
--

DROP TABLE IF EXISTS `actor_terms`;
CREATE TABLE `actor_terms` (
  `id` int(32) unsigned NOT NULL,
  `director` varchar(250) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Table structure for table `casts`
--

DROP TABLE IF EXISTS `casts`;
CREATE TABLE `casts` (
  `filename` varchar(32) default NULL,
  `imdb_id` int(12) unsigned default NULL,
  `imdb_actor_id` int(12) unsigned default NULL,
  `actor_name` varchar(250) default NULL,
  `imdb_character_id` int(12) unsigned default NULL,
  `character_name` varchar(250) default NULL,
  KEY `imdb_actor_id` (`imdb_actor_id`),
  KEY `imdb_id` (`imdb_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Table structure for table `director_terms`
--

DROP TABLE IF EXISTS `director_terms`;
CREATE TABLE `director_terms` (
  `id` int(32) unsigned NOT NULL,
  `director` varchar(250) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Table structure for table `directors`
--

DROP TABLE IF EXISTS `directors`;
CREATE TABLE `directors` (
  `filename` varchar(32) default NULL,
  `imdb_id` int(12) unsigned default NULL,
  `imdb_director_id` int(12) unsigned default NULL,
  `director_name` varchar(250) default NULL,
  KEY `imdb_director_id` (`imdb_director_id`),
  KEY `imdb_id` (`imdb_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Table structure for table `genre_terms`
--

DROP TABLE IF EXISTS `genre_terms`;
CREATE TABLE `genre_terms` (
  `id` int(32) unsigned NOT NULL,
  `genre` varchar(70) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `genre` (`genre`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Table structure for table `genres`
--

DROP TABLE IF EXISTS `genres`;
CREATE TABLE `genres` (
  `filename` varchar(32) default NULL,
  `imdb_id` int(12) unsigned default NULL,
  `genre` varchar(250) default NULL,
  KEY `genre` (`genre`),
  KEY `imdb_id` (`imdb_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Table structure for table `plot_keyword_terms`
--

DROP TABLE IF EXISTS `plot_keyword_terms`;
CREATE TABLE `plot_keyword_terms` (
  `id` int(32) unsigned NOT NULL,
  `plot_keyword` varchar(70) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `plot_keyword` (`plot_keyword`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Table structure for table `plot_keywords`
--

DROP TABLE IF EXISTS `plot_keywords`;
CREATE TABLE `plot_keywords` (
  `filename` varchar(32) default NULL,
  `imdb_id` int(12) unsigned default NULL,
  `plot_keyword` varchar(250) default NULL,
  KEY `plot_keyword` (`plot_keyword`),
  KEY `imdb_id` (`imdb_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Table structure for table `titles`
--

DROP TABLE IF EXISTS `titles`;
CREATE TABLE `titles` (
  `filename` varchar(32) default NULL,
  `imdb_id` int(12) unsigned NOT NULL,
  `title` varchar(250) default NULL,
  `year` int(4) unsigned default NULL,
  `cover_url` varchar(250) default NULL,
  `gallery_url` varchar(250) default NULL,
  `trailer_url` varchar(250) default NULL,
  `user_rating` float(3,2) default NULL,
  `nb_votes` int(12) default NULL,
  `type_tv_serie` tinyint(1) default NULL,
  `type_episode` tinyint(1) default NULL,
  `type_other` varchar(10) default NULL,
  `release_date` date default NULL,
  `release_date_raw` varchar(100) default NULL,
  `tagline` varchar(500) default NULL,
  `plot` text,
  `awards` varchar(250) default NULL,
  `also_known_as` varchar(500) default NULL,
  `runtime` int(5) default NULL,
  `color` varchar(100) default NULL,
  `aspect_ratio` varchar(50) default NULL,
  `certification` varchar(10) default NULL,
  `trivia` text,
  `goofs` text,
  PRIMARY KEY  (`imdb_id`),
  KEY `certification` (`certification`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2011-04-24 17:31:33
