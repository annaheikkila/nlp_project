import urllib.request as urllib2
import urllib.parse
from bs4 import BeautifulSoup
import argparse
import nltk

class Translate_Swe_Eng(object):

    def __init__(self):
        #self.input_string = input_string
        self.tokens = None

        self.swetoeng = {}

    def process_input(self, text):
        """
        Processes the input string.
        """
        try :
            self.tokens = nltk.word_tokenize(text) 
        except LookupError :
            nltk.download('punkt')
            self.tokens = nltk.word_tokenize(text)
        for token in self.tokens:
            self.translator(token)


    def translator(self, sweword):
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
        self.swetoeng[sweword] = translation

    def return_translation(self):
        '''
        Takes first translation from bab.la of swedish words and erturns total sentence. If no translation, 
        return original word in the same position.
        '''
        sentence = []
        for key, value in self.swetoeng.items():
            if value != []:
                sentence.append(value[0])
            else:
                sentence.append(key)
                print("Warning, the word ", key, " has no translation on babla. For a more accurate translation, try a different word instead.")
        # List_to_print with elements ("rows") as strings instead of lists

        myStr = ""
        for j,col in enumerate(sentence):
            if not j==len(sentence)-1:
                myStr += str(col) + " "
            else:
                myStr += str(col) 

        return myStr

def main():

    parser = argparse.ArgumentParser(description='Translate_Swe_Eng')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--string', '-s', type=str, help='decode a string')


    arguments = parser.parse_args()

    
    s1 = arguments.string

    # Give the filename of the bigram probabilities as a command line argument
    d = Translate_Swe_Eng()

    # Append two extra "\t" to the input string, one at the start and one at the end, to indicate start/end of sentence. 
    d.process_input(s1)
    result = d.return_translation()

    print(result)


if __name__ == "__main__":
    main()
