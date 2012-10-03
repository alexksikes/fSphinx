-- MySQL dump 10.13  Distrib 5.1.63, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: fsphinx
-- ------------------------------------------------------
-- Server version	5.1.63-0+squeeze1

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
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `actor_terms` (
  `id` int(32) unsigned NOT NULL,
  `actor` varchar(250) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cache`
--

DROP TABLE IF EXISTS `cache`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cache` (
  `_key` varchar(32) NOT NULL,
  `query` varchar(250) DEFAULT NULL,
  `value` text,
  `sticky` tinyint(1) DEFAULT NULL,
  `datetime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`_key`),
  KEY `sticky` (`sticky`),
  KEY `datetime` (`datetime`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `casts`
--

DROP TABLE IF EXISTS `casts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `casts` (
  `filename` varchar(32) DEFAULT NULL,
  `imdb_id` int(12) unsigned DEFAULT NULL,
  `imdb_actor_id` int(12) unsigned DEFAULT NULL,
  `actor_name` varchar(250) DEFAULT NULL,
  `imdb_character_id` int(12) unsigned DEFAULT NULL,
  `character_name` varchar(250) DEFAULT NULL,
  KEY `imdb_actor_id` (`imdb_actor_id`),
  KEY `imdb_id` (`imdb_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `director_terms`
--

DROP TABLE IF EXISTS `director_terms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `director_terms` (
  `id` int(32) unsigned NOT NULL,
  `director` varchar(250) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `directors`
--

DROP TABLE IF EXISTS `directors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `directors` (
  `filename` varchar(32) DEFAULT NULL,
  `imdb_id` int(12) unsigned DEFAULT NULL,
  `imdb_director_id` int(12) unsigned DEFAULT NULL,
  `director_name` varchar(250) DEFAULT NULL,
  KEY `imdb_director_id` (`imdb_director_id`),
  KEY `imdb_id` (`imdb_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `genre_terms`
--

DROP TABLE IF EXISTS `genre_terms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genre_terms` (
  `id` int(32) unsigned NOT NULL,
  `genre` varchar(70) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `genre` (`genre`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `genres`
--

DROP TABLE IF EXISTS `genres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genres` (
  `filename` varchar(32) DEFAULT NULL,
  `imdb_id` int(12) unsigned DEFAULT NULL,
  `genre` varchar(250) DEFAULT NULL,
  KEY `genre` (`genre`),
  KEY `imdb_id` (`imdb_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `plot_keyword_terms`
--

DROP TABLE IF EXISTS `plot_keyword_terms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `plot_keyword_terms` (
  `id` int(32) unsigned NOT NULL,
  `plot_keyword` varchar(70) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `plot_keyword` (`plot_keyword`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `plot_keywords`
--

DROP TABLE IF EXISTS `plot_keywords`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `plot_keywords` (
  `imdb_id` int(12) unsigned DEFAULT NULL,
  `plot_keyword` varchar(250) DEFAULT NULL,
  KEY `imdb_id` (`imdb_id`),
  KEY `plot_keyword` (`plot_keyword`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `titles`
--

DROP TABLE IF EXISTS `titles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `titles` (
  `filename` varchar(32) DEFAULT NULL,
  `imdb_id` int(12) unsigned NOT NULL,
  `title` varchar(250) DEFAULT NULL,
  `year` int(4) unsigned DEFAULT NULL,
  `cover_url` varchar(250) DEFAULT NULL,
  `gallery_url` varchar(250) DEFAULT NULL,
  `trailer_url` varchar(250) DEFAULT NULL,
  `user_rating` float(3,2) DEFAULT NULL,
  `nb_votes` int(12) DEFAULT NULL,
  `type_tv_serie` tinyint(1) DEFAULT NULL,
  `type_episode` tinyint(1) DEFAULT NULL,
  `type_other` varchar(10) DEFAULT NULL,
  `release_date` date DEFAULT NULL,
  `release_date_raw` varchar(100) DEFAULT NULL,
  `tagline` varchar(500) DEFAULT NULL,
  `plot` text,
  `awards` varchar(250) DEFAULT NULL,
  `also_known_as` varchar(500) DEFAULT NULL,
  `runtime` int(5) DEFAULT NULL,
  `color` varchar(100) DEFAULT NULL,
  `aspect_ratio` varchar(50) DEFAULT NULL,
  `certification` varchar(10) DEFAULT NULL,
  `trivia` text,
  `goofs` text,
  PRIMARY KEY (`imdb_id`),
  KEY `certification` (`certification`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2012-10-02 10:10:45
