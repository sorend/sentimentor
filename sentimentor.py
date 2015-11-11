#!/usr/bin/env python

import os
import sqlite3
import cherrypy
from collections import namedtuple
import tweepy
import random
import twitterkeys

# setup twitter authentication and api
twitter_auth = tweepy.OAuthHandler(twitterkeys.consumer_key, twitterkeys.consumer_secret)
twitter_auth.set_access_token(twitterkeys.access_key, twitterkeys.access_secret)
twitter_api = tweepy.API(twitter_auth)

database_file = 'sentiments.db'

def namedtuple_select(table, nt_type):
    return "SELECT %s FROM %s" % (",".join(nt_type._fields), table)

class TweetRecord(namedtuple("TweetRecord", "id, status, message, message_p, q")):
    """ Helper for twitter records """
    @classmethod
    def _empty(cls):
        return TweetRecord(**dict(zip(TweetRecord._fields, [None] * len(TweetRecord._fields))))

class SentimentRecord(namedtuple("SentimentRecord", "id, username, sentiment, energy")):
    """ Helper for sentiment records """
    @classmethod
    def _empty(cls):
        return SentimentRecord(**dict(zip(SentimentRecord._fields, [None] * len(SentimentRecord._fields))))

class database:
    """ Helper for database connections """
    def __enter__(self):
        self.conn = sqlite3.connect(database_file)
        return self.conn

    def __exit__(self, type, value, traceback):
        if value is None:
            self.conn.commit()
        self.conn.close()


class Sentimentor(tweepy.StreamListener):
    """ Handles twitter interfacing and sentiment retrieval/sending """
    def __init__(self, api=None):
        super(Sentimentor, self).__init__(api=api)
        self.stream = None
        self.q = None
        self.lang = None
        self.counter = 0

    def load_ids(self):
        if not hasattr(self, "ids"):
            with database() as db:
                self.ids = [ int(x[0]) for x in db.cursor().execute("SELECT id FROM tweets").fetchall() ]
        return self.ids

    def start_receiving(self, q, lang='en'):
        """ Start receiving new tweets from twitter for the given query """
        self.q = [ x.strip() for x in q.split(",") ]
        if len(self.q) == 0:
            raise ValueError("Query required")
        self.lang = lang
        self.counter = 0
        self.stream = tweepy.Stream(auth=twitter_api.auth, listener=self)
        self.stream.filter(track=self.q, async=True, languages=[self.lang])

    def stop_receiving(self):
        """ Stop receiving tweets """
        if self.stream is not None:
            self.stream.disconnect()
            self.stream = None
        if hasattr(self, "ids"):
            del self.ids  # rebuild cache

    def on_status(self, status):
        """ Handle new message """
        print "- received:", status.text, "lang:", status.lang
        if status.lang == self.lang and status.retweeted is False:  # avoid retweets
            with database() as db:
                sql = "INSERT INTO tweets (message, q) VALUES (?, ?)"
                data = (status.text, ",".join(self.q))
                db.cursor().execute(sql, data)
                self.counter += 1

    def on_error(self, status_code):
        """ Handle error from twitter """
        print "Got Twitter error code", status_code, "stopping stream."
        self.stop_receiving()
        return False

    def on_exception(self, e):
        print "Exception", e.message
        self.stop_receiving()

    def load_next(self, username=None):
        with database() as db:
            c = db.cursor()
            c.execute("SELECT id FROM sentiments WHERE username = ?", (username,))
            completed_ids = [ int(x[0]) for x in c.fetchall() ]
            incomplete = set(self.load_ids())
            incomplete.difference_update(completed_ids)
            # print "incomplete", incomplete
            # print "completed", completed_ids
            if len(incomplete) < 1:
                return None
            next_id = random.sample(incomplete, 1)[0]
            return TweetRecord._make(c.execute("SELECT * FROM tweets WHERE id = ?", (next_id,)).fetchone())._asdict()

    def save_sentiment(self, tweets_id, username, sentiment, energy=1):
        sql = "INSERT INTO sentiments (id, username, sentiment, energy) VALUES (?, ?, ?, ?)"
        data = (tweets_id, username, sentiment, energy)
        with database() as db:
            db.cursor().execute(sql, data)

class MainPage(object):

    def __init__(self):
        self.s = Sentimentor(twitter_api)

    @cherrypy.expose()
    @cherrypy.tools.json_out()
    def tweet(self, username):
        return self.s.load_next(username)

    @cherrypy.expose()
    @cherrypy.tools.json_out()
    def start(self, q, lang='en'):
        self.s.start_receiving(q, lang)
        return {"status": "Running"}

    @cherrypy.expose()
    def stop(self):
        self.s.stop_receiving()

    @cherrypy.expose()
    @cherrypy.tools.json_out()
    def status(self):
        if self.s.stream is not None:
            return {"status": "running", "q": self.s.q, "lang": self.s.lang, "counter": self.s.counter}
        else:
            return {"status": "stopped"}

    @cherrypy.expose()
    def sentiment(self, tweet_id, username, sentiment, energy=1):
        self.s.save_sentiment(tweet_id, username, sentiment, energy)

if __name__ == "__main__":
    """ Main entry of program """

    """ configure cherrypy """
    cherrypy.config.update({
        "server.socket_host": "127.0.0.1",
        "server.socket_port": 5001
    })

    public_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "public")
    conf = {
        "/": {
            "tools.staticdir.root": public_path,
        },
        "/public": {
            "tools.staticdir.on": True,
            "tools.staticdir.dir": public_path,
        }
    }
    """ startup cherrypy """
    cherrypy.quickstart(MainPage(), "/", conf)
