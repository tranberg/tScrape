from datetime import datetime
from tScrape import scraper, parser

# List of Twitter handles to scrape. It works with pages, not persons.
handles = ['SeleniumHQ', 'ThePSF', 'OSFramework']

# Date for the scraper to go back in time. Must be unix time stamp.
# Format: year, month, day, hour, minute, second
stopTime = int(datetime(2015, 6, 1, 0, 0, 0).strftime('%s'))

# Should the scraper and parser be verbose?
verbose = True

# Path for data to be stored
dataPath = './data/raw/'
parsePath = './data/'

scraper(handles, dataPath, stopTime, verbose)
parser(handles, dataPath, parsePath, stopTime, verbose)
