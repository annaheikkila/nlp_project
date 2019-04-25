#  -*- coding: utf-8 -*-
from __future__ import unicode_literals
import math
import argparse
import nltk
import os
from collections import defaultdict
import codecs
import json
import requests


"""
This file is part of the computer assignments for the course DD1418/DD2418 Language engineering at KTH.
Created 2017 by Johan Boye and Patrik Jonell.
"""


class BigramTrainer(object):
    """
    This class constructs a trigram language model from a corpus.
    """

    def process_files(self, f):
        """
        Processes the file @code{f}.
        """
        with codecs.open(f, 'r', 'ISO-8859-1') as text_file:
            text = reader = str(text_file.read()).lower()
        try :
            self.tokens = nltk.word_tokenize(text) 
        except LookupError :
            nltk.download('punkt')
            self.tokens = nltk.word_tokenize(text)
        for token in self.tokens:
            self.process_token(token)


    def process_token(self, token):
        """
        Processes one word in the training corpus, and adjusts the unigram and
        bigram counts.

        :param token: The current word to be processed.
        
           
            If word has not been seen before it needs to be added to unique words etc.
            Otherwise, just add on to the unigram and bigram count.
            
            index:  {'i': 0, 'in': 2, 'live': 1}
			word:  {0: 'i', 1: 'live', 2: 'in'}

        """
        #Text uppdelad ord för ord
        #Unigram - count number of times word appears in text
     
        if self.unique_words == 0:
            self.unigram_count[token] = 1
            self.word[self.unique_words] = token
            self.index[token] = self.unique_words
            self.unique_words += 1
            
            
        elif token not in self.index.keys() and self.unique_words == 1:
            self.unigram_count[token] = 1
            self.word[self.unique_words] = token
            self.index[token] = self.unique_words
            self.unique_words += 1
            self.bigram_count[self.last_index][self.index[token]] = 1
            

        elif token not in self.index.keys():
            self.unigram_count[token] = 1
            self.word[self.unique_words] = token
            self.index[token] = self.unique_words
            self.unique_words += 1
            self.bigram_count[self.last_index][self.index[token]] = 1
            self.trigram_count[self.before_last_index][self.last_index][self.index[token]] = 1
        else:
            if self.bigram_count[self.last_index][self.index[token]] != 0:
                self.bigram_count[self.last_index][self.index[token]] = self.bigram_count[self.last_index][self.index[token]] + 1

            if self.bigram_count[self.last_index][self.index[token]] == 0:
                self.bigram_count[self.last_index][self.index[token]] = 1

            if self.trigram_count[self.before_last_index][self.last_index][self.index[token]] != 0:
                self.trigram_count[self.before_last_index][self.last_index][self.index[token]] += 1

            if self.trigram_count[self.before_last_index][self.last_index][self.index[token]] == 0:
                self.trigram_count[self.before_last_index][self.last_index][self.index[token]] = 1
            
            self.unigram_count[token]+=1


        self.before_last_index = self.last_index
        self.last_index = self.index[token]
        self.total_words += 1


    def stats(self):
        """
        Creates three lists of rows to print of the language model consisting of the unigrams, bigrams and trigrams.

        """
        uni_rows_to_print = []
        bi_rows_to_print = []
        tri_rows_to_print = []

        # YOUR CODE HERE
        
        uni_rows_to_print.append([self.unique_words, self.total_words])

        for i in range(self.unique_words):
            uni_rows_to_print.append([i, self.word[i], self.unigram_count[self.word[i]]])

        
        for key1, newdict in self.bigram_count.items():
            for key2, value in newdict.items():

                    bigram = value/self.unigram_count[self.word[key1]]
                    bi_rows_to_print.append([key1, key2, "%.15f" % math.log(bigram)])

        for key1, newdict in self.trigram_count.items():
            for key2, smallerdict in newdict.items():
                for key3, value in smallerdict.items():
                    trigram = value/self.bigram_count[key1][key2]
                    tri_rows_to_print.append([key1, key2, key3, "%.15f" % math.log(trigram)])

        uni_stringList =[]
        bi_stringList = []
        tri_stringList = []
        
        for row in uni_rows_to_print:
            myStr = ""
            for j,col in enumerate(row):
                if not j==len(row)-1:
                    myStr += str(col) + " "
                else:
                    myStr += str(col) 
            uni_stringList.append(myStr)
        
        #uni_stringList.append("-1")

        
        for row in bi_rows_to_print:
            myStr = ""
            for j,col in enumerate(row):
                if not j==len(row)-1:
                    myStr += str(col) + " "
                else:
                    myStr += str(col) 
            bi_stringList.append(myStr)
        
        #bi_stringList.append("-1")
        
        for row in tri_rows_to_print:
            myStr = ""
            for j,col in enumerate(row):
                if not j==len(row)-1:
                    myStr += str(col) + " "
                else:
                    myStr += str(col) 
            tri_stringList.append(myStr)


        return {"Unigram": uni_stringList,
                "Bigram": bi_stringList,
                "Trigram": tri_stringList}
        
    def __init__(self):
        """
        <p>Constructor. Processes the file <code>f</code> and builds a language model
        from it.</p>

        :param f: The training file.
        """

        # The mapping from words to identifiers.
        self.index = {}

        # The mapping from identifiers to words.
        self.word = {}

        # An array holding the unigram counts.
        self.unigram_count = defaultdict(int)

        """
        The bigram counts. Since most of these are zero, we store these
        in a hashmap rather than an array to save space.
        """
        self.bigram_count = defaultdict(lambda: defaultdict(int))

        # The identifier of the previous word processed.
        self.last_index = -1

        # Number of unique words (word forms) in the training corpus.
        self.unique_words = 0

        # The total number of words in the training corpus.
        self.total_words = 0

        self.laplace_smoothing = False
        
        # The trigram counts.
        self.trigram_count = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        # Index for word before-last
        self.before_last_index = -2



def main():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(description='BigramTrainer')
    parser.add_argument('--file', '-f', type=str,  required=True, help='file from which to build the language model')
    parser.add_argument('--destination1', '-d1', type=str, help='files in which to store the unigrams of the language model')
    parser.add_argument('--destination2', '-d2', type=str, help='files in which to store the bigrams of the language model')
    parser.add_argument('--destination3', '-d3', type=str, help='files in which to store the trigrams of the language model')
    #parser.add_argument('--check', action='store_true', help='check if your alignment is correct')

    arguments = parser.parse_args()

    bigram_trainer = BigramTrainer()

    bigram_trainer.process_files(arguments.file)

    stats = bigram_trainer.stats()
    
    UniFil = stats["Unigram"]
    BiFil = stats["Bigram"]
    TriFil = stats["Trigram"]
    
    if arguments.destination1:
        with codecs.open(arguments.destination1, 'w', 'utf-8' ) as f:
            for row in UniFil: f.write(row + '\n')
    else:
        for row in UniFil: print(row)
    
    if arguments.destination2:
        with codecs.open(arguments.destination2, 'w', 'utf-8' ) as f:
            for row in BiFil: f.write(row + '\n')
    else:
        for row in BiFil: print(row)

    if arguments.destination3:
        with codecs.open(arguments.destination3, 'w', 'utf-8' ) as f:
            for row in TriFil: f.write(row + '\n')
    else:
        for row in TriFil: print(row)


if __name__ == "__main__":
    main()
