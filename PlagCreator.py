import random
import re
from enum import Enum
import pickle

class PlagCreator:
    # text modes
    class Text_mode(Enum):
        simple = 0
        markov = 1

    # plag modes
    class Plag_mode(Enum):
        one_to_one = 0
        shuffled = 1

    def __init__(self):
        self.wiki_articles = self.parse_wiki_dump()  # parse only once
        self.words, self.db = self.make_words_list_and_db()  # make words list and db only once


    def parse_wiki_dump(self):
        '''
        Parses a wiki dump textfile
        return: dictionary with key: title of wiki article and value: text of wiki article as list of words
        '''

        source_file = "dump/clean_dump.xml"

        text_file = open(source_file, "r")
        wiki = text_file.read()  # whole file in a string
        text_file.close()

        texts = wiki.split("-------------------------------------------------")  # split file at each separator line
        texts = [re.sub(r'==.*==', '', x) for x in texts]  # remove section headings
        texts = [re.sub(r'[^\w]|\n|[\s]', ' ', x) for x in texts]  # remove punctuation chars
        # texts = [re.sub(r'\d+','',x) for x in texts] #remove numbers
        texts = [re.sub(r'\s{2,}', ' ', x).strip() for x in texts]  # replace multiple space chars with one space char
        texts = [x for x in texts if x != '']  # remove empty strings from list
        texts = [x.lower() for x in texts]
        texts = {texts[i]: texts[i + 1].split(' ') for i in range(0, len(texts), 2)}  # turn list into a dictionary
        return texts


    def make_words_list_and_db(self):
        '''
        Generates a list of words and dictionary for the markov chain text generator
        return: tuple with list of words and dictionary
        '''

        # concat all texts of all wiki articles as one bisg list of words
        words = []
        for text in self.wiki_articles.values():
            words.append(text)
        words = sum(words, [])  # flatten

        # build triples of three succeeding words with a step size of 1
        triples = []
        if len(words) >= 3:
            for i in range(len(words) - 2):
                triple = (words[i], words[i + 1], words[i + 2])
                triples.append(triple)

        # build a dictionary with a two word key and a list with all succeeding words as the value
        db = dict()
        for w1, w2, w3 in triples:
            key = (w1, w2)
            if key in db:
                db[key].append(w3)
            else:
                db[key] = [w3]
        return (words, db)


    def text_generator_simple(self, number_of_texts, min_length, max_length):
        '''
        Generates a random text out of a list of words
        param number_of_texts: number of texts to be generated
        param min_length: min length of the text (lower limit of a random length)
        param max_length: max length of the text (upper limit of a random length)
        return: list of generated texts; a text is represented as list of words
        '''

        source_file = "wordlist/germanWords.txt"

        text_file = open(source_file, "r")
        words = text_file.read().splitlines()  # read lines of file to list
        text_file.close()

        random_texts = []  # list with texts
        for x in range(number_of_texts):
            length = random.randrange(min_length, max_length)
            text = []
            for y in range(length):
                text.append(random.choice(words))  # randomly choosing words
            random_texts.append(text)
        return random_texts


    def text_generator_markov(self, number_of_texts, min_length, max_length):
        '''
        Generates a random text using markov chain. The generated text looks more natural
        param number_of_texts: number of texts to be generated
        param min_length: min length of the text (lower limit of a random length)
        param max_length: max length of the text (upper limit of a random length)
        return: list of generated texts; a text is represented as list of words
        '''

        random_texts = []
        for x in range(number_of_texts):
            seed_index = random.randrange(0, len(self.words) - 3)  # randomly choose the index of the word to start with (seed)
            w1, w2 = self.words[seed_index], self.words[seed_index + 1]  # get this word and the next word from the dictionary
            text = []
            length = random.randrange(min_length, max_length)
            for i in range(length):
                text.append(w1)
                w1, w2 = w2, random.choice(self.db[(w1, w2)])  # randomly choose one possible word for the selected key
            text.append(w2)
            random_texts.append(text)

        return random_texts


    def get_plag_text(self, plag_mode, length):
        '''
        Randomly chooses a text part out of a wiki article
        param length: length of the plagiarized text part
        return: tuple (title of article, text part as list of words)
        '''

        article_title = random.choice(list(self.wiki_articles.keys()))  # randomly choose a wiki article
        while len(self.wiki_articles[article_title]) < length:
            article_title = random.choice(list(self.wiki_articles.keys()))  # randomly choose a wiki article

        start = random.randrange(0, len(self.wiki_articles[article_title]) - length)  # randomly choose start position of plag

        plag = self.wiki_articles[article_title][start: start + length]  # cut text part out
        if plag_mode == self.Plag_mode.shuffled:
            random.shuffle(plag)

        return (article_title, plag)


    def generate_plags(self, text_mode, plag_mode, number_of_texts, min_text_length, max_text_length, plag_length,
                       output_dir, ):
        '''
        Generates texts with embedded plagiarism + info file for each text and outputs them to txt files
        param number_of_texts: number of texts to be generated
        param min_text_length: min length of the surrounding text (lower limit of a random length)
        param max_text_length: max length of the surrounding text (upper limit of a random length)
        param plag_length: length of the plagiarized text part
        param output_dir: output directory for the generated texts
        '''

        if text_mode == self.Text_mode.simple:
            random_texts = self.text_generator_simple(number_of_texts, min_text_length, max_text_length)
        elif text_mode == self.Text_mode.markov:
            random_texts = self.text_generator_markov(number_of_texts, min_text_length, max_text_length)
        else:
            print("NO SUCH TEXT MODE (" + str(text_mode) + ")!")
            return

        plag_texts = []

        i = 0  # index for file names
        for text in random_texts:
            plag_start = random.randrange(0, len(text) - 1)  # position of plag in surrounding text
            plag = self.get_plag_text(plag_mode, plag_length)  # randomly choose plag

            text[plag_start: plag_start] = plag[1]  # insert plag into surrounding text
            plag_text = ' '.join(text)  # convert list of words int space separated string

            # print info
            print("text_length: " + str(len(text)))
            print("plagiarized_article: " + plag[0])
            print("plagiarism_start: " + str(plag_start))
            print("plagiarism_end: " + str(plag_start + len(plag[1]) - 1))
            print("plagiarism_length: " + str(plag_length))
            print("plagiarism_text_part:\n" + ' '.join(plag[1]))
            print("text_with_plagiarism:\n" + plag_text)
            print("\n")

            # write text to file
            output_file_name = output_dir + "/plag" + str(i) + ".txt"
            output_file = open(output_file_name, "w")
            output_file.write(plag_text)
            output_file.close()

            # write info file
            output_file_name = output_dir + "/plag" + str(i) + "_info.txt"
            output_file = open(output_file_name, "w")
            output_file.write("text_length: " + str(len(text)) + "\n")
            output_file.write("plagiarized_article: " + plag[0] + "\n")
            output_file.write("plagiarism_start: " + str(plag_start) + "\n")
            output_file.write("plagiarism_end: " + str(plag_start + len(plag[1])) + "\n")
            output_file.write("plagiarism_length: " + str(plag_length) + "\n")
            output_file.write("plagiarism_text_part: " + ' '.join(plag[1]))
            output_file.close()

            i += 1


#save PlagCreator object on disk
#pc = PlagCreator()
#pickle.dump(pc, open("PlagCreator.p", "wb"))

pc = pickle.load(open("PlagCreator.p", "rb"))

pc.generate_plags(pc.Text_mode.markov, pc.Plag_mode.shuffled, 2, 200, 300, 20, "plag")

