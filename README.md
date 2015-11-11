
Sentimentor
===========

Sentimentor is a small tool which can do two things:

 * Collect messages from Twitter given a criteria.
 * A user interface to specify sentiment of the messages.

Installation
------------

After downloading the code, you must obtain API keys for Twitter and put
them in the file twitterkeys.py. See twitterkeys.py.sample for an example
(no keys provided). You can get API keys from https://dev.twitter.com/.

Once keys are provided, you can install the application by creating a
virtualenv and installing packages from requirements.txt, then create the
database using sqlite3.

    virtualenv venv
    . venv/bin/activate
    pip install -r requirements.txt
    sqlite3 sentiments.db < sentiments.sql

To start the application running run the sentimentor.py file

    ./sentimentor.py

Now you can open the application using the following URLs:

 * Collect messages: http://localhost:5001/public/receive.html
 * Annotate sentiment: http://localhost:5001/public/index.html

