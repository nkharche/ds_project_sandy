#!/opt/conda/bin/python

'''
Gets text content for tweet IDs
http://stackoverflow.com/questions/28384588/twitter-api-get-tweets-with-specifc-id
'''

# standard
from __future__ import print_function
import getopt
import logging
import os
import sys
import json
#from io import open
# import traceback
# third-party: `pip install tweepy`
import tweepy
import tarfile
import time

# global logger level is configured in main()
Logger = None

def load_api_keys(keyfile, delimiter):
    '''Reads API keys from a file and stores them in a dictionary. Returns dictionary'''
    keydict = {}
    with open(keyfile, 'r') as f:
        for line in f:
            if line:
                lst = line.split(delimiter)
                if len(lst)==2:
                    key, val = [item.strip() for item in lst]
                    keydict[key] = val
    return keydict

def get_tweet_id(line):
    '''
    Extracts and returns tweet ID from a line in the input.
    '''
    (tagid,_timestamp,_sandyflag) = line.split('\t')
    (_tag, _search, tweet_id) = tagid.split(':')
    return tweet_id

def get_tweets_single(twapi, idfile):
    '''
    Fetches content for tweet IDs in a file one at a time,
    which means a ton of HTTPS requests, so NOT recommended.

    `twapi`: Initialized, authorized API object from Tweepy
    `idfile`: Path to file containing IDs
    '''
    # process IDs from the file
    with open(idfile, 'rb') as idfile:
        for line in idfile:
            tweet_id = get_tweet_id(line)
            Logger.debug('Fetching tweet for ID %s', tweet_id)
            try:
                tweet = twapi.get_status(tweet_id)
                print('%s,%s' % (tweet_id, tweet.text.encode('UTF-8')))
            except tweepy.TweepError as te:
                Logger.warn('Failed to get tweet ID %s: %s', tweet_id, te.message)
                # traceback.print_exc(file=sys.stderr)
        # for
    # with

def get_tweet_list(twapi, idlist, outfile):
    '''
    Invokes bulk lookup method.
    Raises an exception if rate limit is exceeded.
    '''
    # fetch as little metadata as possible
    #tweets = twapi.statuses_lookup(id_=idlist, include_entities=False, trim_user=True)
    tweets = twapi.statuses_lookup(id_=idlist, include_entities=False, trim_user=False)

    #############
    with open(outfile, mode='a') as feedsjson:
       with open(outfile, 'a') as outfile:
    #############

           for tweet in tweets:
               #print('%s,%s' % (tweet.id, tweet.text.encode('UTF-8')))
               print('%s' % (tweet.id))

               #############
               #json_str = json.dumps(tweet._json.get('id_str'), feedsjson_id)
               #json.dump(json_str, outfile_id) 
               json_str = json.dumps(tweet._json, feedsjson)
               json.dump(json_str, outfile) 
               #############

def get_tweets_bulk(twapi, idfile_tgz, idfile, outfile):
    '''
    Fetches content for tweet IDs in a file using bulk request method,
    which vastly reduces number of HTTPS requests compared to above;
    however, it does not warn about IDs that yield no tweet.

    `twapi`: Initialized, authorized API object from Tweepy
    `idfile`: Path to file containing IDs
    '''    

    # process IDs from the file
    tweet_ids = list()
    #with open(idfile, 'rb') as idfile:
    with tarfile.open(idfile_tgz, 'r:gz') as tf:
         idfile = tf.extractfile(idfile)
         for line in idfile:
             tweet_id = get_tweet_id(line)
             Logger.debug('Fetching tweet for ID %s', tweet_id)
             # API limits batch size to 100
             if len(tweet_ids) < 100:
                 tweet_ids.append(tweet_id)
             else:
                 while True:
                    try:
                       get_tweet_list(twapi, tweet_ids, outfile)
                       tweet_ids = list()
                       break
                    except tweepy.TweepError, e:
                        #if e == "[{u'message': u'Rate limit exceeded', u'code': 88}]":
                        if 'Rate limit exceeded' in str(e): 
                           print('tweepy.error.RateLimitError')
                           time.sleep(60*5) #Sleep for 5 minutesi
                           pass
                        else:
                           print (e)
    # process rump of file
    if len(tweet_ids) > 0:
        get_tweet_list(twapi, tweet_ids)

def usage():
    print('Usage: get_tweets_by_id.py [options] file')
    print('    -s (single) makes one HTTPS request per tweet ID')
    print('    -v (verbose) enables detailed logging')
    sys.exit()

def main(args):
    '''
    Input arguments
    args[0] = Archive containg tweet ids
    args[1] = File in the archive that contains tweet ids
    args[2] = File containing twitter API keys
    args[3] = Delimiter separating API key and its value 
    args[4] = output file
    '''

    logging.basicConfig(level=logging.WARN)
    global Logger
    Logger = logging.getLogger('get_tweets_by_id')
    bulk = True
    try:
        opts, args = getopt.getopt(args, 'sv')
    except getopt.GetoptError:
        usage()
    for opt, _optarg in opts:
        if opt in ('-s'):
            bulk = False
        elif opt in ('-v'):
            Logger.setLevel(logging.DEBUG)
            Logger.debug("verbose mode on")
        else:
            usage()
    if len(args) != 5:
        usage()

    # File names
    idfile_tgz = args[0]
    idfile = args[1]
    keyfile = args[2]
    keyfile_delimiter = args[3]
    outfile = args[4]

    if not os.path.isfile(idfile_tgz):
        print('Not found or not a file: %s' % idfile, file=sys.stderr)
        usage()

    # Load API keys
    keyfile = 'TWITTER_API_KEYS'
    delimiter = '='
    keydict = load_api_keys(keyfile, delimiter)

    # connect to twitter
    auth = tweepy.OAuthHandler(keydict['CONSUMER_KEY'], keydict['CONSUMER_SECRET'])
    auth.set_access_token(keydict['OAUTH_TOKEN'], keydict['OAUTH_TOKEN_SECRET'])
    api = tweepy.API(auth)

    # hydrate tweet IDs
    if bulk:
        get_tweets_bulk(api, idfile_tgz, idfile, outfile)
    else:
        get_tweets_single(api, idfile)

if __name__ == '__main__':
    '''$python get_sandy_corpus_tweets.py sandy_corpus_tweet_ids.tgz release.txt TWITTER_API_KEYS = sandy_corpus_tweets.json'''
    main(sys.argv[1:])
