import os
import random
import re
from enum import Enum
import pickle
import time
import collections


# text modes
class Text_mode(Enum):
    simple = 0
    markov = 1


# plag modes
class Plag_mode(Enum):
    one_to_one = 0
    shuffle = 1
    replace = 2
    distance_between_words = 3  # umnennen?


Source_Info = collections.namedtuple('Source_Info', 'article extract start end')


class PlagCreator:
    def __init__(self):
        self.wiki_articles = self.parse_wiki_dump()
        self.words, self.db = self.make_words_list_and_db()

    def parse_wiki_dump(self):
        '''
        Parses a wiki dump textfile
        :return: dictionary with key: title of wiki article and value: text of wiki article as list of words
        '''

        print("parsing wiki dump file...")
        source_file = "dump/clean_dump.txt"

        text_file = open(source_file, "r")
        wiki = text_file.read()  # whole file in a string
        text_file.close()

        texts = wiki.split("-------------------------------------------------")  # split file at each separator line
        texts = [re.sub(r'==.*==', '', x) for x in texts]  # remove section headings
        texts = [re.sub(r'[^\w]|\n|[\s]', ' ', x) for x in texts]  # remove punctuation chars
        texts = [re.sub(r'\d+', '', x) for x in texts]  # remove numbers
        texts = [re.sub(r'\s{2,}', ' ', x).strip() for x in texts]  # replace multiple space chars with one space char
        texts = [x for x in texts if x != '']  # remove empty strings from list
        texts = [x.lower() for x in texts]
        texts = {texts[i]: texts[i + 1].split(' ') for i in range(0, len(texts), 2)}  # turn list into a dictionary
        return texts

    def make_words_list_and_db(self):
        '''
        Generates a list of words and dictionary for the markov chain text generator
        :return: tuple with list of words and dictionary
        '''
        # concat all texts of all wiki articles as one bisg list of words
        print("making words list...")
        words = []
        for text in self.wiki_articles.values():
            words.append(text)
        words = sum(words, [])  # flatten

        # append the two first words to the end, to avoid KeyError in markov
        words.append(words[0])
        words.append(words[1])

        # build triples of three succeeding words with a step size of 1
        print("making db dictionary...")
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
        :param number_of_texts: number of texts to be generated
        :param min_length: min length of the text (lower limit of a random length)
        :param max_length: max length of the text (upper limit of a random length)
        :return: list of generated texts; a text is represented as list of words
        '''

        source_file = "wordlist/germanWords.txt"

        text_file = open(source_file, "r")
        words = text_file.read().splitlines()  # read lines of file to list
        text_file.close()

        random_texts = []  # list with texts
        for x in range(number_of_texts):
            length = random.randint(min_length, max_length)
            text = []
            for y in range(length):
                text.append(random.choice(words))  # randomly choosing words
            random_texts.append(text)
        return random_texts

    def text_generator_markov(self, number_of_texts, min_length, max_length):
        '''
        Generates a random text using markov chain. The generated text looks more natural
        :param number_of_texts: number of texts to be generated
        :param min_length: min length of the text (lower limit of a random length)
        :param max_length: max length of the text (upper limit of a random length)
        :return: list of generated texts; a text is represented as list of words
        '''

        random_texts = []
        for x in range(number_of_texts):
            seed_index = random.randrange(0, len(
                self.words) - 3)  # randomly choose the index of the word to start with (seed)
            w1, w2 = self.words[seed_index], self.words[seed_index + 1]  # get the word and the next word from the dict
            text = []
            length = random.randint(min_length, max_length)
            for i in range(length):
                text.append(w1)
                w1, w2 = w2, random.choice(self.db[(w1, w2)])  # randomly choose one possible word for the selected key
            text.append(w2)
            random_texts.append(text)

        return random_texts

    def shuffle_plag(self, plag):
        '''
        Rondomly shuffles extract
        :param plag: wiki source extract
        '''
        random.shuffle(plag)

    def replace_plag(self, plag):
        '''
        Randomly replaces words in extract with other words
        :param plag: wiki source extract
        '''
        number_replacements = int(len(plag) * 0.2)

        if number_replacements == 0:
            number_replacements = 1

        replaced_indices = []
        for _ in range(number_replacements):
            random_position = random.randrange(len(plag))
            while random_position in replaced_indices:
                random_position = random.randrange(len(plag))
            replaced_indices.append(random_position)

        for i in replaced_indices:
            replacement = random.choice(self.words)
            while plag[i] == replacement:
                replacement = random.choice(self.words)

            plag[i] = replacement

    def get_plag_text(self, length):
        '''
        Randomly chooses a text part out of a wiki article
        :param length: length of the plagiarized text part
        :return: tuple (title of article, text part as list of words)
        '''

        # randomly choose a wiki article
        article_title = random.choice(list(self.wiki_articles.keys()))

        # if wiki article is too short, randomly choose a different article
        while len(self.wiki_articles[article_title]) < length:
            article_title = random.choice(list(self.wiki_articles.keys()))

        # randomly choose start position of plag
        start = random.randint(0, len(self.wiki_articles[article_title]) - length)

        # cut text part out
        plag = self.wiki_articles[article_title][start: start + length]

        return Source_Info(article_title, plag, start, start + len(plag) - 1)

    def detect_overlapping_plags(self, existing_positions, new_position):
        '''
        Detects overlapping of two plags
        :param existing_positions: list of tupels the position of all plagiarisms in text
        :param new_positions: tupel containing new intended position for plag
        :return: true if overlapping
        '''

    def generate_plags(self, text_mode, plag_mode, number_of_texts, min_text_length, max_text_length,
                       plag_length, output_dir, max_word_distance=1, number_of_plags_per_text=1):
        '''
        Generates texts with embedded plagiarism + info file for each text and outputs them to txt files
        :param number_of_texts: number of texts to be generated
        :param min_text_length: min length of the surrounding text (lower limit of a random length)
        :param max_text_length: max length of the surrounding text (upper limit of a random length)
        :param plag_length: length of the plagiarized text part
        :param output_dir: output directory for the generated texts
        '''

        if text_mode == Text_mode.simple:
            random_texts = self.text_generator_simple(number_of_texts, min_text_length, max_text_length)
        elif text_mode == Text_mode.markov:
            random_texts = self.text_generator_markov(number_of_texts, min_text_length, max_text_length)
        else:
            print("NO SUCH TEXT MODE (" + str(text_mode) + ")!")
            return

        # used for creation of files containing target texts and infos
        file_name_index = 0

        for text in random_texts:
            plag_pos_in_target_text = []
            for _ in range(number_of_plags_per_text):
                # randomly choose plag
                plag = self.get_plag_text(plag_length)

                # position of plag in surrounding text
                plag_start_in_target_text = random.randrange(0, len(text))
                plag_end_in_target_text = plag_start_in_target_text + len(plag.extract) - 1
                word_pos_list = []

                if plag_mode == Plag_mode.distance_between_words:
                    for word in plag.extract:
                        word_pos_list.append((plag_start_in_target_text,word))
                        plag_start_in_target_text += random.randint(1, max_word_distance)

                    print(word_pos_list)

                # if list is not empty
                if plag_pos_in_target_text:
                    # check if overlap then new start position
                    should_restart = True
                    while should_restart:
                        should_restart = False
                        for pos in plag_pos_in_target_text:
                            print("existing pos: " + str(pos))
                            if plag_start_in_target_text <= pos[1] and pos[0] <= plag_end_in_target_text:
                                should_restart = True
                                print("overlapping pos: (" + str(plag_start_in_target_text) + ", " + str(plag_end_in_target_text) + ")")
                                plag_start_in_target_text = random.randrange(0, len(text))
                                plag_end_in_target_text = plag_start_in_target_text + len(plag.extract) - 1
                                print("new pos: (" + str(plag_start_in_target_text) + ", " + str(plag_end_in_target_text) + ")")
                                break
                            else:
                                for pos in plag_pos_in_target_text:
                                    if plag_start_in_target_text < pos[0]:
                                        pos = (pos[0] + plag_length, pos[1] + plag_length)

                # copy plag.extract
                extract_from_source_text = list(plag.extract)
                plag_infos = []

                # plag infos extended with infos common in all modes
                plag_infos.extend(("article: " + plag.article,
                                   "extract_from_source_text: " + ' '.join(extract_from_source_text),
                                   "plag_start_in_source_text: " + str(plag.start),
                                   "plag_end_in_source_text: " + str(plag.end),
                                   "plag_length: " + str(plag_length)))

                # special case: distance_between_words. Plag infos differs from other cases
                if plag_mode == Plag_mode.distance_between_words:
                    if max_word_distance:
                        # iterate over all words in extract and insert every single word
                        # with different distances into target text
                        for word_tupel in word_pos_list:
                            # insert word
                            text.insert(word_tupel[0], word_tupel[1])

                            # plag infos extended with infos in plag mode distance_between_words
                            plag_infos.extend(("word: " + word_tupel[1],
                                               "word_position_target_text: " + str(word_tupel[0])))

                # other plag modes
                else:
                    if plag_mode == Plag_mode.shuffle:
                        self.shuffle_plag(plag.extract)
                    if plag_mode == Plag_mode.replace:
                        self.replace_plag(plag.extract)

                    # insert plag into surrounding text
                    text[plag_start_in_target_text: plag_start_in_target_text] = plag.extract

                    # alias for plag.extract to show that original text has changed
                    text_in_target_text = plag.extract

                    # plag infos extended with infos common in other plag modes
                    plag_infos.extend(("text_in_target_text: " + ' '.join(text_in_target_text),
                                       "plag_start_in_target_text: " + str(plag_start_in_target_text),
                                       "plag_end_in_target_text: " +
                                       str(plag_end_in_target_text)))

                    # save plag position
                    plag_pos_in_target_text.append((plag_start_in_target_text, plag_end_in_target_text))

                print("plag_pos_i_t_text: " +str(plag_pos_in_target_text))


                for i, word in enumerate(text):
                    print(str(i) + ": " + word)

                # convert list of words into space separated string
                plag_text = ' '.join(text)

                # plag infos extended with infos common in all plag modes
                plag_infos.extend(("plag_mode: " + plag_mode.name, "text_length: " + str(len(text)),
                                   "text_with_plagiarism:\n" + plag_text))

                # concatenate plag_infos to string
                plag_infos_str = ""
                for info in plag_infos:
                    plag_infos_str += info + "\n"

                print(plag_infos_str)
                print("\n")

                # create output_dir if not existing
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                # write text to file
                output_file_name = output_dir + "/plag" + str(file_name_index) + ".txt"
                output_file = open(output_file_name, "w")
                output_file.write(plag_text)
                output_file.close()

                # write info file
                output_file_name = output_dir + "/plag" + str(file_name_index) + "_info.txt"
                output_file = open(output_file_name, "w")
                output_file.write(plag_infos_str)
                output_file.close()

                file_name_index += 1


# measure execution time
start = time.clock()

# read PlagCreator object from disk if existing, else create it
if os.path.exists("PlagCreator.p"):
    pc = pickle.load(open("PlagCreator.p", "rb"))
else:
    pc = PlagCreator()
    pickle.dump(pc, open("PlagCreator.p", "wb"))

# execute generate_plags with desired parameters
pc.generate_plags(Text_mode.markov, Plag_mode.distance_between_words, number_of_texts=1, number_of_plags_per_text=3,
                  min_text_length=20, max_text_length=30,
                  plag_length=5, max_word_distance=4, output_dir="plag")

print("execution time: %.3f seconds" % (time.clock() - start))
