#!/Users/shabang/anaconda/bin/python


from multiprocessing import Queue, Process
from time import time, sleep


def start():
	q = Queue() #Create multiprocessing.Queue

	hi1 = Process(target=sayHi, args=(5,0))
	hi2 = Process(target=sayHi, args=(5,1))

	#Start the new Processes
	hi1.start()
	hi2.start()

def sayHi(speed, me):
	while True:
		sleep(speed)
		print me, "hi", time()
	

if __name__ == '__main__':
	start()
