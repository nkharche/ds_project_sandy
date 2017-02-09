#!/global/common/cori/software/python/2.7-anaconda/bin/python

'''
Replaces empty double quotes ('""') by line breaks ('\n'). Useful for debugging
'''
with open("sandy_corpus_tweets_include_user_info_newline.json", "wt") as fout:
    with open('sandy_corpus_tweets_include_user_info.json') as fin:
        for line in fin:
            #print line
            fout.write(line.replace('""', '"\n"'))
