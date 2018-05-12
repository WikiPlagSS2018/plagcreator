import urllib.request
import random
import re


class PlagCreator:
    def __init__(self):
        # get the base text, the plags are gonna be mixed with
        self.base_text = self.get_base_text()
        # get n articles out of the database, save in list of tuples (docid, text)
        self.wiki_articles_plag = self.getWikiArticlesFromDB(2, 1)

    def createPlag(self, number_plags):

        def get_subset_from_base_text(number_plags):

            indices_of_sentence_endings = [m.start() for m in re.finditer('\.', self.base_text)]
            selections_from_base_text = list()

            for i in range(number_plags):
                # index within the list, not the text
                start = random.randint(0, len(indices_of_sentence_endings) - 20)
                end = random.randint(start + 2, start + 10)
                start_in_base_text = indices_of_sentence_endings[start]
                end_in_base_text = indices_of_sentence_endings[end]
                start_end_in_base_text = (start_in_base_text, end_in_base_text)
                selections_from_base_text.append((start_end_in_base_text[0], start_end_in_base_text[1], self.base_text[start_in_base_text + 2: end_in_base_text + 1]))

            return selections_from_base_text

        def get_plags_from_wiki_articles():

            plags = list()

            for article in self.wiki_articles_plag:
                article_docid = article[0]
                article_text = article[1]
                indices_of_sentence_endings = [m.start() for m in re.finditer('[^A-Z0-9]\.(?!\s[a-z])', article_text)]
                indices_of_sentence_endings = list(filter(
                    lambda x: re.match('[A-Z]', article_text[x + 2]) is not None or re.match('[A-Z]', article_text[
                        x + 3]) is not None, indices_of_sentence_endings))

                start_plag_index_within_list = random.randint(0, len(indices_of_sentence_endings))
                end_plag_index_within_list = start_plag_index_within_list + 1

                start_plag_index_within_article = indices_of_sentence_endings[start_plag_index_within_list] + 3 # TODO: check index_out_of_bounds
                end_plag_index_within_article = indices_of_sentence_endings[end_plag_index_within_list]

                plag = (start_plag_index_within_article, end_plag_index_within_article,
                        article_text[start_plag_index_within_article:end_plag_index_within_article + 1])

                plags.append((article_docid, plag))

            return plags

        subset_from_base_text = get_subset_from_base_text(number_plags)
        plags_from_wiki_articles = get_plags_from_wiki_articles()

    def get_base_text(self):
        with open('base_text.txt') as f:
            base_text = f.read()

        return base_text

    def getWikiArticlesFromDB(self, number_plags, start_docid):
        original_wiki_texts = list()

        start_docid = start_docid

        while len(original_wiki_texts) < number_plags:
            try:
                resource = urllib.request.urlopen("http://localhost:8080/wikiplag/rest/documents/" + str(start_docid))
                text = resource.read().decode('utf-8')
                original_wiki_texts.append((start_docid, text))
            except:
                pass
            start_docid += 1

        return original_wiki_texts

    def text_generator_markov(self, min_length, max_length):
        '''
        Generates a random text using markov chain. The generated text looks more natural
        :param number_of_texts: number of texts to be generated
        :param min_length: min length of the text (lower limit of a random length)
        :param max_length: max length of the text (upper limit of a random length)
        :return: list of generated texts; a text is represented as list of words
        '''

        # randomly choose the index of the word to start with (seed)
        seed_index = random.randrange(0, len(self.words) - 3)
        w1, w2 = self.words[seed_index], self.words[seed_index + 1]  # get the word and the next word from the dict
        text = []
        length = random.randint(min_length, max_length)
        for i in range(length):
            text.append(w1)
            w1, w2 = w2, random.choice(self.db[(w1, w2)])  # randomly choose one possible word for the selected key
        text.append(w2)

        return text

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


if __name__ == "__main__":
    pc = PlagCreator()
    pc.createPlag(10)
    # pc.createPlag(10,1,1,1)
