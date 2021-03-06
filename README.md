# tScrape
A simple Python scraper and parser for Twitter pages using [Beautifulsoup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/) and [Selenium](http://selenium-python.readthedocs.org/) webdriver. Parser output is json, see details below.


Install requirements
--------------------
    pip install -r requirements.txt


Configure scraper
-----------------
In *run.py*:

1. Define a list of Twitter handles
2. Set a date for the scraper to go back in time
3. Define verbosity and output paths


Run the scraper
---------------
    python run.py


Output
------
For each Twitter handle the parser will output two json files:

**handle-stats.json** with the keys:
- name
- url
- bioText
- following
- frequency: tweets per day
- followers
- location:
- favorites: average received favorites per tweet
- tweets: total number of tweets
- joinDate
- retweets: average received retweets per tweet


**handle-tweets.json** with an entry for each tweet containing the keys:
- origin: tweet (T) or retweet (RT)?
- text: full text including hashtags, mentions and links
- hashtags: a list of used hashtags
- retweets: number of received retweets
- favorites: number of received favorites
- time: time of tweet
- mentions: list of @ mentions


Importing results
-----------------
To import the results as a Python dictionary use the _jsonLoad_ function:

    from tScrape import jsonLoad
    results = jsonLoad(handle, path)

Use the standard dictionary methods to inspect the content:

    results.keys()
    results.values()

    for key en results.keys():
        print key, results[key]
