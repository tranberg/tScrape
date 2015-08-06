from __future__ import division
import re
import os
import sys
import json
import time
import string
from random import random
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver


def vprint(str, verbose=True):
    """
    Print string if verbose is True.
    """
    if verbose: print(str)


def sleep(s):
    """
    A sleep function with random noise so we seem more human.
    """
    time.sleep(random() + s)


def jsonLoad(handle, path):
    """
    Load a specific json file.
    """
    return json.load(open(path + handle + '.json'))


def dateCheck(driver, stopTime, lastTweet=None):
    """
    Check if tweets are older than given stop time.
    """
    soup = BeautifulSoup(driver.page_source.encode('UTF-8'))
    spans = soup.findAll('span')
    for span in spans[::-1]:
        if span.has_attr('data-time'):
            if span['data-time'] == lastTweet:
                return False, span['data-time']
            elif int(span['data-time']) <= stopTime:
                return False, span['data-time']
            else:
                return True, span['data-time']


def scrollBottom(driver):
    """
    Scroll to the bottom of browser window.
    """
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


def timeString(timeStamp):
    """
    Convert unix time to eg. 2015-06-18 14:57:44.
    """
    return datetime.fromtimestamp(int(timeStamp)).strftime('%Y-%m-%d %H:%M:%S')


def getTweetData(tweet):
    """
    Extract data from a tweet, which is a BeautifulSoup object.
    """
    timeStamp = tweet.find('small').find('a').find('span')['data-time']
    # Determine if original tweet or retweet
    try:
        contextClasses = tweet.find('div').find('div').find('span')['class']
        if 'Icon--retweeted' in contextClasses:
            origin = 'RT'
    except:
        origin = 'T'
    text = tweet.find('p').getText()
    hashtags = []
    mentions = []
    anchors = tweet.findAll('a')
    for a in anchors:
        anchorClasses = a['class']
        if 'twitter-hashtag' in anchorClasses:
            hashtags.append(a.getText())
        if 'twitter-atreply' in anchorClasses:
            mentions.append(a.getText())
    # Convert unix time stamp to human readable date format
    timeStamp = timeString(timeStamp)
    return timeStamp, origin, text, hashtags, mentions


def scraper(handles, dataPath, stopTime, verbose=True):
    """
    Scrape twitter page from now and back in time to stopTime.
    """
    vprint('# Starting scraper')
    driver = webdriver.Firefox()
    driver.set_window_size(1920, 1080)

    if not os.path.exists(dataPath):
        os.makedirs(dataPath)

    for handle in handles:
        s = 0
        driver.get('http://twitter.com/' + handle)
        vprint('Got ' + handle, verbose)
        scroll, lastTweet = dateCheck(driver, stopTime)
        while scroll is True:
            s += 1
            if verbose:
                sys.stdout.flush()
                sys.stdout.write('\r' + 'Scrolling (' + str(s) + ')')
            sleep(2)
            scrollBottom(driver)
            scroll, lastTweet = dateCheck(driver, stopTime, lastTweet)
        if s > 0:
            vprint('\nSaving', verbose)
        else:
            vprint('Saving', verbose)
        with open(dataPath + handle + '.html', 'wb') as f:
            f.write(driver.page_source.encode('UTF-8'))
        vprint('------', verbose)
    driver.close()


def parser(handles, dataPath, parsePath, stopTime, verbose=True):
    """
    Parse data from scraper and output to json files.
    """
    vprint('# Parsing', verbose)
    if not os.path.exists(parsePath):
        os.makedirs(parsePath)
    for handle in handles:
        tweetDict = {}
        try:
            soup = BeautifulSoup(open(dataPath + handle + '.html'))
            vprint('Got ' + handle, verbose)
        except:
            raise Exception('Run scraper before parser!')
        try:
            tweetDict = jsonLoad(handle + '-tweets', parsePath)
            firstRun = False
        except:
            firstRun = True

        # Gather page stats
        anchors = soup.findAll('a')
        statsDict = {}
        for a in anchors:
            if a.has_attr('class'):
                if 'ProfileHeaderCard-nameLink' in a['class']:
                    statsDict['name'] = a.getText()
            if a.has_attr('data-nav'):
                if a['data-nav'] == 'tweets':
                    sp = a.findAll('span')
                    statsDict['tweets'] = sp[-1].getText().replace(',', '')
                elif a['data-nav'] == 'following':
                    sp = a.findAll('span')
                    statsDict['following'] = sp[-1].getText().replace(',', '')
                elif a['data-nav'] == 'followers':
                    sp = a.findAll('span')
                    statsDict['followers'] = sp[-1].getText().replace(',', '')
                elif a['data-nav'] == 'favorites':
                    sp = a.findAll('span')
                    statsDict['favorites'] = sp[-1].getText().replace(',', '')
        statsDict['bioText'] = soup.findAll('p', class_='ProfileHeaderCard-bio')[0].getText()
        bioDivs = soup.findAll('div', class_=re.compile('ProfileHeaderCard-'))
        for div in bioDivs:
            if 'location' in div['class'][0]:
                statsDict['location'] = div.getText().replace('\n', '').replace(' ', '')
            elif 'url' in div['class'][0]:
                statsDict['url'] = 'http://' + div.getText().replace('\n', '').replace(' ', '')
            elif 'joinDate' in div['class'][0]:
                statsDict['joinDate'] = div.getText().replace('\n', '').replace(' ', '')

        # Find tweets
        feed = soup.find_all('li')
        tweets = []
        new = 0
        for tag in feed:
            if tag.has_attr('data-item-type'):
                if tag['data-item-type'] == 'tweet':
                    tweets.append(tag)

        # Find delicious data within each tweet
        nTweets = len(tweets)
        for t, tweet in enumerate(tweets):
            if verbose:
                sys.stdout.write('\r' + str(t + 1) + ' / ' + str(nTweets))
                sys.stdout.flush()

            # Unique tweet identifier
            ID = tweet['data-item-id']

            # Find number of retweets and favorites
            buttons = tweet.findAll('button')
            for button in buttons:
                buttonClasses = button['class']
                if 'js-actionRetweet' in buttonClasses:
                    retweets = button.findAll('span')[-1].getText()
                if 'js-actionFavorite' in buttonClasses:
                    favorites = button.findAll('span')[-1].getText()

            if firstRun is True:
                new += 1
                timeStamp, origin, text, hashtags, mentions = getTweetData(tweet)
                tweetDict[ID] = {'time': timeStamp,
                                 'origin': origin,
                                 'text': text,
                                 'hashtags': hashtags,
                                 'mentions': mentions,
                                 'retweets': retweets,
                                 'favorites': favorites}
            else:
                if ID in tweetDict.keys():
                    tweetDict[ID]['retweets'] = retweets
                    tweetDict[ID]['favorites'] = favorites
                else:
                    new += 1
                    timeStamp, origin, text, hashtags, mentions = getTweetData(tweet)
                    tweetDict[ID] = {'time': timeStamp,
                                     'origin': origin,
                                     'text': text,
                                     'hashtags': hashtags,
                                     'mentions': mentions,
                                     'retweets': retweets,
                                     'favorites': favorites}

        # Calculate stats
        nDays = round((round(time.time()) - stopTime) / (60 * 60 * 24))
        freq = nTweets / nDays
        retweets = 0
        favorites = 0
        for key in tweetDict.keys():
            try:
                retweets += int(tweetDict[key]['retweets'])
            except:
                pass
            try:
                favorites += int(tweetDict[key]['favorites'])
            except:
                pass
        RTfrac = retweets / nTweets
        replFrac = favorites / nTweets
        statsDict['frequency'] = '%.3f' % freq
        statsDict['retweets'] = '%.3f' % (retweets / nTweets)
        statsDict['favorites'] = '%.3f' % (favorites / nTweets)

        # Save data
        if new > 0:
            vprint(', ' + str(new) + ' new.')
        vprint('Saving', verbose)
        with open(parsePath + handle + '-tweets.json', 'w') as jsonFile:
            json.dump(tweetDict, jsonFile)
        with open(parsePath + handle + '-stats.json', 'w') as jsonFile:
            json.dump(statsDict, jsonFile)
        vprint('------', verbose)
