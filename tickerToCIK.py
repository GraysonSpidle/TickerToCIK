'''
Contains the functions necessary for looking up a stock's Central Index Key (CIK) given the stock's ticker.
Author: Grayson Spidle

This code is open source, I don't care if you use it anywhere else. No legal red tape from me.
'''

import re
from requests import get
from threading import Thread
from timer import Timer
from progressbar import progressbar

def get_CIK(ticker) -> str:
    ''' Gets the CIK from the SEC's website given a ticker. 
    This works as of 11/20/2019, it might not work in the future because the SEC might change their site (unlikely, but possible)
    Also, the SEC limits connections it serves from one IP address to 5 per second. If exceeded, it'll deny service for a short period of time.

    Parameters
    ----------
    ticker : str
        The ticker you wish to find the CIK for.

    Returns
    -------
    A string that contains the CIK associated with the ticker. If there was an error and the CIK could not be found, then it will return None.

    '''
    url = "https://www.sec.gov/cgi-bin/browse-edgar?CIK=%s&owner=exclude&action=getcompany" % (ticker.strip().replace("\n",""))
    conn = get(url)
    data = get(url).content.decode()
    assert conn.ok, "Connection wasn't successful. Perhaps you exceeded the maximum allowed connections per second."
    try:
        value = re.findall("([0-9]*) \\(see all company filings\\)", data)[0].replace("\n","")
    except:
        value = None
    conn.close()
    return value

def _get_CIKs_multithread(tickers) -> dict:
    ''' Takes in an iterable that iterates through strings that represent tickers. Then it goes to the SEC's website and retrieves the CIK associated with each ticker and spits out
    a dictionary with each ticker mapped to its own CIK.
    This does the requests to the SEC's website using parallel programming (multi-threading) which makes the job go faster than its sequential counterpart.
    However, this one runs the risk of exceeding the SEC's request limit (it shouldn't, but it's definitely a possibility). In which case will hamper accuracy and performance.
    '''
    numberOfConnectionsPerSecond = 5 # Limit the number of connections we make to 5 per second

    output = {}
    threads = []
    timer = Timer()
    timer.start(1) # Start the timer, if this timer is still going by the time we've hit our maximum number of connections, then we'll wait for it to end before continuing.
    i = 0 # The counter we'll use to determine how many connections we've established in a period of time
    for pos, ticker in enumerate(progressbar(tickers)):
        # Limiting our connections so we don't exceed the SEC's HTTP GET request limit.
        if pos - i >= numberOfConnectionsPerSecond:
            timer.wait() # Waits for the timer to finish. If it's already finished, this does nothing.
            timer.start(1)
            i = pos
        # Making the thread
        t = Thread(target=lambda ticker, output: output.__setitem__(ticker, get_CIK(ticker)), args=(ticker,output))
        t.start()
        threads.append(t)
    print("Waiting for threads to terminate...")
    for thread in progressbar(threads): # Wait until all threads have concluded before continuing
        thread.join()
    
    return output

def get_CIKs(tickers, enableMultiThreading:bool = True) -> dict:
    ''' Gets CIKs from the SEC's website given a collection of tickers. It won't neccessarily preserve the order of the tickers.

    This works as of 11/20/2019, it might not work in the future because the SEC might change their site (unlikely, but possible).
    Also, the SEC limits connections it serves from one IP address to 5 per second. If exceeded, it'll deny service for a short period of time.

    Parameters
    ----------
    tickers : iterable
        This should be an iterable object (e.g. list, tuple) that supplies strings that represent the tickers. This cannot be None.

    enableMultiThreading : bool
        This tells the function whether you want to harness the power of parallel programming (multi-threading) to complete the job faster.
        Set this value to True if you do want multi-threading enabled or set it to False if you want it disabled. It defaults to True.

    Returns
    -------
    A dictionary object with each ticker (key) mapped to its respective CIK (value). It won't neccessarily preserve the order of the tickers.
    '''
    
    # Parameter Validation
    if not hasattr(tickers, "__next__") and not hasattr(tickers, "__iter__"):
        raise TypeError("Parameter tickers of type {} is not iterable.".format(type(tickers)))
    if type(enableMultiThreading) is not bool:
        raise ValueError("Parameter enableMultiThreading must be either True or False not {}.".format(enableMultiThreading))

    # Actual Code
    output = {}
    print("Retrieving CIKs...")
    if not enableMultiThreading: # Means we're going to use 1 thread to do the job (slower)
        for ticker in progressbar(tickers):
            output[ticker] = get_CIK(ticker)
    else: # We're going to use multiple threads to do the job (faster)
        output = _get_CIKs_multithread(tickers)

    return output


def get_CIKs_file_to_file(tickerFilePath:str, outputFilePath:str, delim:str = "\n", enableMultiThreading:bool = True):
    ''' Reads a file of tickers delimited by the supplied delimiter and gets the corresponding CIK and puts both of those into a
    file (it truncates the existing information in the file) in the format of: ticker,CIK\\n

    Tickers that the program fails to find a CIK for default to the value of None.
    Note: this doesn't guarantee that the output will preserve the order of the tickers in the output file.

    Parameters
    ----------
    tickerFilePath : str
        A string representation of the path to the input file which contains the tickers to look up.

    outputFilePath : str
        A string representation of the path to the output file in which this program will dump the results.
    
    delim : str
        A string that tells the program how the input file delimits its tickers.
    
    enableMultiThreading : bool
        A boolean that tells the program whether or not to use multi-threading. Setting this value to True will make the program run significantly faster,
        but may hit the SEC's request per second limit (it shouldn't but it's a possibility). Setting this value to False will make the program run slower,
        but won't hit the request per second limit. I recommend you use multi-threading because it's just way faster than the alternative.

    '''
    out = open(outputFilePath, 'w')
    with open(tickerFilePath) as file:
        mapped = get_CIKs(file.read().split(delim), enableMultiThreading)
        print("Writing data to file: %s" % outputFilePath)
        for ticker, cik in progressbar(mapped.items()):
            out.write("%s,%s\n" % (ticker,cik))
    out.close()

if __name__ == "__main__":
    get_CIKs_file_to_file("tickers.txt", "ciks.csv", '\n', True)

     