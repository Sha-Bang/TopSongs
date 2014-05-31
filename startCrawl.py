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
words = {} #word:count
googleUrl = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&"
metroUrl = "http://www.metrolyrics.com/search.html?search="



def main(numPages, args):
	billQ = Queue()
	googleQ = Queue()
	lyricQ = Queue()
	wordsQ = Queue()
	print "total charts: ", numPages
	for url in args:
		for i in range(0, numPages):
			print "%s%s" % (url, i)
			billQ.put("%s%s" % (url, i))

	billSearch = Process(target=grabBody, args=(billQ,googleQ))
#	googSearch = Process(target=googleSearch, args=(googleQ, lyricQ))
	metSearch = Process(target=metroSearch, args=(googleQ, lyricQ))
	lyrSearch = Process(target=lyricSearch, args=(lyricQ, googleQ, wordsQ))
	checkPt = Process(target=checkPoint, args=(billQ, googleQ, lyricQ, wordsQ))
	
	billSearch.start()
	sleep(2)
	#googSearch.start()
	metSearch.start()
	lyrSearch.start()
	checkPt.start()
	

def grabBody(billQ, googleQ):
	while not billQ.empty():
		url = billQ.get()
		x = urllib2.urlopen(url).read()
		y = href.findall(x)
		if not y:
			billQ.put(url)
		for link in  y:
			print "grabBody ", link
			link = (link[0], link[1])
			googleQ.put(" ".join(link))
	print "!!STATUS!! billQ DONE"
	

def metroSearch(googleQ, lyricQ):
	metroLyricGrab = re.compile("<span>Songs</span>.*?href=\"(.*?\.html)\"")
	delayTime = 5
	while not googleQ.empty():
		origQuery = googleQ.get()
		print "orig: ", (1, origQuery)
		sleep(int(delayTime))
		query = "+".join(origQuery.split())
		print(metroUrl + query )
		response = " ".join(urllib2.urlopen(metroUrl + query ).read().split("\n"))
		y = metroLyricGrab.findall(response)
		for link in y:
			print "#####",
			print link
			lyricQ.put(link)



def googleSearch(googleQ, lyricQ):
	delayTime = 5
	while not googleQ.empty():
		origQuery = googleQ.get()
		sleep(int(delayTime))
		
		query = urllib.urlencode( {'q' : origQuery } )
		print query
		query = cleanSpace.sub("+", query)
		print query
		
		try:
			response = urllib2.urlopen(googleUrl + query ).read()
		
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
			print "#GS: failed on: ", query
			delayTime= delayTime * 1.7
			print "#GS: delayTime: ", delayTime
			googleQ.put(origQuery)
		
	print "!!STATUS!! googleSearch DONE"

def lyricSearch(lyricQ, googleQ, wordsQ):
	while not lyricQ.empty() or not googleQ.empty():
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
	
	print "!!STATUS!! lyricSearch DONE"

def checkPoint(billQ, googleQ, lyricQ, wordsQ):
	words = {}
	lastTime = 0 #fast 1st checkpoint
	checkpointnum = 0


	while not billQ.empty() or not googleQ.empty() or not lyricQ.empty() or not wordsQ.empty():
		if not wordsQ.empty():
			word = wordsQ.get()
			words.setdefault(word, 0)
			words[word]+=1
		if time() > lastTime+10:
			lastTime = time()
			sys.stderr.write("Checkpointing\n")
			print "checkpointing"
			write(words, str(int(time()))+" "+str(checkpointnum))
			checkpointnum+=1
			print "*"*50
#			print "*"*10, billQ.qsize(), googleQ.qsize(), lyricQ.qsize(), wordsQ.qsize(), "*"*10
#			print "*"*50
			sys.stdout.flush()
			sys.stderr.flush()

	print "!!STATUS!! checkPoint DONE"
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


