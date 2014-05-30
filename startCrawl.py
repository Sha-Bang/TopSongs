#!/Users/shabang/anaconda/bin/python


import urllib2
import urllib
import json
import sys
import re
from time import sleep, time
from multiprocessing import Queue, Process


href = re.compile("<h1>(.*)</h1>\s*?<p class=\"chart_info\">\s*<.*?href.*?title=\"(.*?)\"")
lyricHref = re.compile("id=\"lyrics-body-text\">(.*?)</div>")
cleanHTML = re.compile("<.*?>")
cleanSpace = re.compile("\+\++")
global words
words = {} #word:count
delayTime = 5
checkpointnum = 0



def main(numPages, args):
	billQ = Queue()
	googleQ = Queue()
	lyricQ = Queue()
	wordsQ = Queue()
	print "total charts: ", numPages
	for url in args:
		for i in range(0, numPages+1):
			billQ.put("%s%s" % (url, i))

	billSearch = Process(target=grabBody, args=(billQ,googleQ))
	googSearch = Process(target=googleSearch, args=(googleQ, lyricQ, delayTime))
	lyrSearch = Process(target=lyricSearch, args=(lyricQ, googleQ, wordsQ))
	checkPt = Process(target=checkPoint, args=(billQ, googleQ, lyricQ, wordsQ))
	
	billSearch.start()
	sleep(10)
	googSearch.start()
	lyrSearch.start()
	checkPt.start()
	

def grabBody(billQ, googleQ):
	while billQ:
		url = billQ.get()
		x = urllib2.urlopen(url).read()
		y = href.findall(x)
		if not y:
			billQ.put(url)
		for link in  y:
			print "grabBody ", link
			link = (link[0], link[1], "site:www.metrolyrics.com")
			googleQ.put(" ".join(link))
	

def googleSearch(googleQ, lyricQ, delayTime):
	while googleQ:
		origQuery = googleQ.get()
		sleep(int(delayTime))
		url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&"
		
		query = urllib.urlencode( {'q' : origQuery } )
		print query
		query = cleanSpace.sub("+", query)
		print query
		
		try:
			response = urllib2.urlopen(url + query ).read()
		
			data = json.loads( response )
		
			results = data [ 'responseData' ] [ 'results' ]
			result = results[0]

			title = result['title']
			url = result['url']
			print ( title + '; ' + url )
			lyricQ.put(url)
			delayTime-=1
			if delayTime<=0:
				delayTime+=1
			if delayTime>=180:
				delayTime=180
		except:
			print "failed on: ", query
			delayTime= delayTime * 1.7
			print "delayTime: ", delayTime
			googleQ.put(origQuery)
		

def lyricSearch(lyricQ, googleQ, wordsQ):
	global words
	while lyricQ or googleQ:
		url = lyricQ.get()
		try:
			print "trying: ", url
			x = "".join(urllib2.urlopen(url).read().split("\n"))
			for link in  lyricHref.findall(x):
				print link
				clean = cleanHTML.sub(" ", link).split()
				for word in clean:
					word = word.lower()
					wordsQ.put(word)

		except:
			print "wah2"

def checkPoint(billQ, googleQ, lyricQ, wordsQ):
	words = {}
	lastTime = time()



	while billQ or googleQ or lyricQ or wordsQ:
		if wordsQ:
			word = wordsQ.get()
			words.setdefault(word, 0)
			words[word]+=1
		if words and time() > lastTime+15:
			lastTime = time()
			sys.stderr.write("Checkpointing\n")
			print "checkpointing"
			write(words, str(int(time()))+" "+str(checkpointnum))
			print "*"*50
			sys.stdout.flush()
			sys.stderr.flush()



def write(words, filename="out.txt"):
	outFile = open(filename, "w")
	for k, v in sorted(words.items(), key=lambda x: x[1], reverse=True):
		outFile.write("%s: %s\n" % (k, v))
	outFile.close()


def test():
	x = "".join(open("summer-lyrics-calvin-harris.html", "r").read().split("\n"))
	for link in lyricHref.findall(x):
		print link
		clean = cleanHTML.sub(" ", link).split()
		for word in clean:
			word = word.lower()
			words.setdefault(word, 0)
			words[word]+=1

	print words
	sys.exit()

if __name__=="__main__":
	print "starting"
	main(int(sys.argv[1]), sys.argv[2:])


