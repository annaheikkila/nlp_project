import math
import sys
import numpy as np
import codecs
import argparse
import json
import requests
import urllib.request as urllib2
import urllib.parse
from bs4 import BeautifulSoup

from collections import defaultdict
import nltk

class ViterbiBigramDecoder(object):
    """
    This class implements Viterbi decoding using bigram probabilities in order
    to correct keystroke errors.
    """
	
    def read_bifile(self, filename):
        #print("read bifile")
        with codecs.open(filename, 'r', 'latin-1') as f:
            for line in f:
                ord1, ord2, prob = [func(x) for func, x in zip([int, int, float], line.strip().split(' '))]
                self.bidict[ord1][ord2] = prob
	
    def read_unifile(self, filename):
        #print("read unifile")
        with codecs.open(filename, 'r', 'latin-1') as f:
            self.unique_words, self.total_words = map(int, f.readline().strip().split(' '))


            for line in f:
                index, word, prob = [func(x) for func, x in zip([int, str, float], line.strip().split(' '))]
                self.unidict[index] = prob
                self.index[word] = index
                self.word[index] = word

    def reaad_trifile(self, filename):
        with codecs.open(filename, 'r', 'latin-1') as f:
            for line in f:
                ord1, ord2, ord3, prob = [func(x) for func, x in zip([int, int, int, float], line.strip().split(' '))]
                self.tridict[ord1][ord2][ord3] = prob

    def process_input(self, text):
        #print("process_input")
        """
        Processes the input string.
        """
        try :
            self.tokens = nltk.word_tokenize(text) 
        except LookupError :
            nltk.download('punkt')
            self.tokens = nltk.word_tokenize(text)

	
    def get_newindex(self):
        #print("get_newindex")
        for index, word in enumerate(self.tokens):
            if word in self.sentenceindex.keys():
                pass
            else:
                engwordlist = self.translator(word)
                if engwordlist != []:
                    self.swedishtoenglish[word] = engwordlist
                    self.numberoftranslations[word] = len(engwordlist)
                    for engord in engwordlist:
                        self.sentenceindex[engord] = self.wordindex
                        self.index_to_word[self.wordindex] = engord
                        self.wordindex += 1
                        
                else:
                    self.sentenceindex[word] = self.wordindex
                    self.index_to_word[self.wordindex] = word
                    self.wordindex += 1
                    self.swedishtoenglish[word] = [word]
                    self.numberoftranslations[word] = 1
                    if word == ".":
                        pass
                    else:
                        print("The word ", word, " in your sentence cannot be translated. The full translation might not be correct.")
                        

    def translator(self, sweword):
        #print("translator")
        translation = []
        webpage = "https://sv.bab.la/lexikon/svensk-engelsk/" + urllib.parse.quote(sweword)
        page = urllib2.urlopen(webpage)

        soup = BeautifulSoup(page, features="html5lib")

        body = soup.find('body')
        main = soup.find('main')
        divs = main.findAll('div')

        for div in divs:
            if div.has_attr('class') and div['class'][0] == 'page':
                #print('page')
                divs = div.findAll('div')
                
                for div in divs:
                    if div.has_attr('class') and div['class'][0] == 'column-wrapper':
                        #print('column-wrapper')

                        divs = div.findAll('div')

                        for div in divs:
                            if div.has_attr('class') and div['class'][0] == 'content-column':
                                #print('content-column')
                                divs = div.findAll('div')


                                foundContent = False
                                for div in divs:
                                    

                                    if div.has_attr('class') and div['class'][0] == 'content' and not foundContent:
                                        foundContent = True
                                        #print('content')
                                        #det finns tva contents har!!!
                                        divs = div.findAll('div')

                                        for div in divs:

                                            
                                            # print('has attr class')
                                            # print(div.has_attr('class'))
                                            # print()
                                            # print('div class 0 + 1')
                                            # print(div['class'][0] + div['class'][1])

                                            # print()
                                            # print(div.prettify)
                                            # print()

                                            if div.has_attr('class') and div['class'][0] == 'quick-results':
                                                #print('quick-results container')
                                                
                                                divs = div.findAll('div')

                                                for div in divs:


                                                    if div.has_attr('class') and div['class'][0] == 'quick-result-entry':
                                                        #print('quick results entry')
                                                        divs = div.findAll('div')


                                                        for div in divs:


                                                            if div.has_attr('class') and div['class'][0] == 'quick-result-overview':
                                                                #print('quick results overview')
                                                                
                                                                '''
                                                                Kolla så spanTag är EN, annars vill vi inte ha orden
                                                                '''
                                                                
                                                                spans = div.findAll('span')
                                                                for span in spans:
                                                                    if span.has_attr('class') and span['class'][1] == 'uk':
                                                                


                                                                        uls = div.findAll('ul')



                                                                        for ul in uls:



                                                                            if ul.has_attr('class') and ul['class'][0] == 'sense-group-results':
                                                                                #print('sense group')

                                                                                lis = ul.findAll('li')
                                                                                for li in lis:

                                                                                    aTag = li.find('a')
                                                                                    translation.append(aTag.text)
                                                                                    #print()
                                                                                    #print(aTag.text)	
        return translation

    def init_a(self):
        #print("init_a")
        self.a = np.zeros((self.wordindex, self.wordindex, self.wordindex))
        self.a[:,:,:] = -float("inf")
        for ord1, value in self.sentenceindex.items():
            #print("Ord1: ", ord1)
            if ord1 in self.index.keys(): # Kommer finnas unigram och bigram i vår data för ordet
                for ord2, value in self.sentenceindex.items(): # see if there is a bigram for the combination
                    #print("ord2: ", ord2)
                    if ord2 in self.index.keys():
                        for ord3, value in self.sentenceindex.items():
                            if ord3 in self.index.keys():
                                if self.tridict[self.index[ord1]][self.index[ord2]][self.index[ord3]] is not None:
                                    self.a[self.sentenceindex[ord1]][self.sentenceindex[ord2]][self.sentenceindex[ord3]] =self.lambda1 * self.tridict[self.index[ord1]][self.index[ord2]][self.index[ord3]] + self.lambda2*self.bidict[self.index[ord1]][self.index[ord2]] +np.log( self.lambda3 * self.unidict[self.index[ord1]]/self.total_words + self.lambda4)
                                elif self.bidict[self.index[ord1]][self.index[ord2]] is not None:
                                    #print(self.bidict[self.index[ord1]][self.index[ord2]])
                                    self.a[self.sentenceindex[ord1]][self.sentenceindex[ord2]][self.sentenceindex[ord3]] = self.lambda2*self.bidict[self.index[ord1]][self.index[ord2]] + np.log(self.lambda3 * self.unidict[self.index[ord1]]/self.total_words + self.lambda4)
                                else:
                                    self.a[self.sentenceindex[ord1]][self.sentenceindex[ord2]][self.sentenceindex[ord3]] = np.log(self.lambda3 * self.unidict[self.index[ord1]]/self.total_words + self.lambda4)
                            elif self.bidict[self.index[ord1]][self.index[ord2]] is not None:
                                self.a[self.sentenceindex[ord1]][self.sentenceindex[ord2]][self.sentenceindex[ord3]] = self.lambda2*self.bidict[self.index[ord1]][self.index[ord2]] + np.log(self.lambda3 * self.unidict[self.index[ord1]]/self.total_words + self.lambda4)
                            else:
                                self.a[self.sentenceindex[ord1]][self.sentenceindex[ord2]][self.sentenceindex[ord3]] = np.log(self.lambda3 * self.unidict[self.index[ord1]]/self.total_words + self.lambda4)
                    else:
                        self.a[self.sentenceindex[ord1]][self.sentenceindex[ord2]][:] = np.log(self.lambda3 * self.unidict[self.index[ord1]]/self.total_words + self.lambda4)
            else: # Ordet finns inte i vår data, kommer bli en default prob
                #print("wordindex", ord1)
                self.a[self.sentenceindex[ord1]][:][:] = np.log(self.lambda4) 
            #print(self.a)
	
	
	
	
	
	    # ------------------------------------------------------
	
	
    def init_b(self):
        #print("init_b")
        '''
        Initializes the observation probabilities (the 'B' matrix).
        
        '''
        i=0
        self.b = np.zeros((len(set(self.tokens)), self.wordindex))
        self.b[:,:] = - float("inf")
        #print(self.swedishtoenglish.items())
        for key, value in self.swedishtoenglish.items():
            #print(value)
            for n in value:
                engelsktindex = self.sentenceindex[n]
                self.b[i][engelsktindex] = np.log(1/self.numberoftranslations[key])
            self.svensktindex[key] = i
            i +=1
        #print(self.b)


    # ------------------------------------------------------



    def viterbi(self):
        """
        Performs the Viterbi decoding and returns the most likely
        string.
        """
        START_END = self.sentenceindex["."]
        # The Viterbi matrices
        self.v = np.zeros((len(self.tokens), self.wordindex, self.wordindex), dtype='double')
        self.v[:,:,:] = -float("inf")
        self.backptr = np.zeros((len(self.tokens)+1, self.wordindex, self.wordindex), dtype='int')

        # Initialization
        
        # YOUR CODE HERE
        self.v[0,START_END,:] = self.a[START_END, START_END, :] + self.b[self.svensktindex[self.tokens[0]],:]
        
        self.backptr[0, :, :] = self.sentenceindex["."]

        # Induction step

        # YOUR CODE HERE
        for t in range(1,len(self.tokens)):
            #print("b", self.b[index[t],:])
            for j in range(self.wordindex):
                for k in range(self.wordindex):
                    possible_states = self.v[t-1,:,j] + self.a[:,j,k] + self.b[self.svensktindex[self.tokens[t]],k] 
                    
                
                    self.v[t,j,k] = np.amax(possible_states)
                    self.backptr[t,j,k] = np.argmax(possible_states)
            #print("a", self.a)
            #print("b", self.b)
            #print("v", self.v)
        #print(self.v)
        #print(self.backptr)
        # Finally return the result
        
        k1=START_END
        k2=START_END
        self.bestpath.append(self.index_to_word[k2])
        for i in range(len(self.tokens))[::-1]:
            k = self.backptr[i,k1,k2]
            k2 = k1
            k1 = k
            #print(previousstate)
            self.bestpath.append(self.index_to_word[k2])

        myStr= ""
        for j,item in enumerate(reversed(self.bestpath[2:-2])):
            if item != ".":
                myStr += str(item) + " "
            else:
                myStr += str(item)

        return myStr


    # ------------------------------------------------------



    def __init__(self, filename1=None, filename2=None, filename3=None, svenskmening=None):
        """
        Constructor: Initializes the A and B matrices.
        
        
        """
        
        self.bidict = defaultdict(lambda: defaultdict(lambda: None))

        self.tridict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None)))

        self.unidict = {}

        self.index = {}

        self.word = {}
        
        self.index_to_word = {}
        self.sentenceindex ={}
        self.numberoftranslations={}
        self.swedishtoenglish={}
        
        self.wordindex = 0
        # The trellis used for Viterbi decoding. The first index is the time step.
        self.v = None

        # The bigram stats.
        self.a = None
        # The observation matrix.
        self.b = None

        # Pointers to retrieve the topmost hypothesis.
        self.backptr = None

        self.bestpath = []

        if filename1: self.read_unifile(filename1)
        if filename2: self.read_bifile(filename2)
        if filename3: self.reaad_trifile(filename3)

        self.lambda1 = 0.98
        self.lambda4 = 0.00001
        self.lambda3 = 0.0001 - self.lambda4
        self.lambda2= 0.02 - self.lambda3
        self.svensktindex = {}
		


    # ------------------------------------------------------


def main():

    parser = argparse.ArgumentParser(description='ViterbiBigramDecoder')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', '-f', type=str, help='decode the contents of a file')
    group.add_argument('--string', '-s', type=str, help='decode a string')
    #parser.add_argument('--probs2', '-bp', type=str,  required=True, help='bigram probabilities file')
    #parser.add_argument('--probs1', '-up', type=str,  required=True, help='unigram probabilities file')
    #parser.add_argument('--probs3', '-tp', type=str,  required=True, help='bigram probabilities file')
    probs1 = "uniguardian.txt"
    probs2 = "biguardian.txt"
    probs3 = "triguardian.txt"

    arguments = parser.parse_args()

    if arguments.file:
        with codecs.open(arguments.file, 'r', 'utf-8') as f:
            s1 = f.read().replace('\n', '')
    elif arguments.string:
        s1 = arguments.string
    s =  ". " + s1 + " ." + " ."
    # Give the filename of the bigram probabilities as a command line argument
    d = ViterbiBigramDecoder(probs1, probs2, probs3, s)

    d.process_input(s)
    d.get_newindex()
    d.init_a()
    d.init_b()



    # Append two extra "\t" to the input string, one at the start and one at the end, to indicate start/end of sentence. 
    result = d.viterbi()

    
    print(result)


if __name__ == "__main__":
    main()