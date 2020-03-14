'''
Contains the class definitions for the Timer class which is used to stagger HTTP GET requests during multi-threading.
Author: Grayson Spidle

This code is open source, I don't care if you use it anywhere else. No legal red tape from me.
'''
__author__ = "Grayson Spidle"

from threading import Thread
from time import sleep

class Timer:
    def __init__(self):
        self._thread = None

    def start(self, seconds):
        ''' Starts a new thread. If there is a pre-existing thread, it will just create another one which may cause a resource leak, but
        just use startAndWait() to circumvent this problem.

        Parameters
        ----------
        seconds : int
            The amount of seconds you wish to put on the timer.
        '''
        self._thread = Thread(name="TimerThread", target=lambda: sleep(seconds))
        self._thread.start()

    def wait(self):
        ''' Waits for the timer to reach 0. 
        This will block the current thread until the timer reaches 0.
        '''
        if self._thread is not None:
            self._thread.join()
            del self._thread
        else:
            return
    
    def startAndWait(self, seconds):
        ''' Basically just does start() and wait(). For convenience. '''
        self.start(seconds)
        self.wait()