import urllib.request
import random
import re
import copy


class PlagCreator:
    def __init__(self):
        # get the base text, the plags are gonna be mixed with
        self.base_text = self.get_base_text()

    def createPlagiarism(self, number_plagiarism, number_selections, number_plags, start_docid_plags):

        def get_subset_from_base_text():

            indices_of_sentence_endings = [m.start() for m in re.finditer('\.', self.base_text)]
            selections_from_base_text = list()
            is_plag = False

            for i in range(number_selections):
                # index within the list, not the text
                start = random.randint(0, len(indices_of_sentence_endings) - 20)
                end = random.randint(start + 2, start + 10)
                start_in_base_text = indices_of_sentence_endings[start]
                end_in_base_text = indices_of_sentence_endings[end]
                start_end_in_base_text = (start_in_base_text, end_in_base_text)
                length_of_selection = end_in_base_text - start_in_base_text + 1
                selection_id = i + 1
                selections_from_base_text.append(
                    (selection_id, is_plag, (start_end_in_base_text[0], start_end_in_base_text[1],
                                             length_of_selection,
                                             self.base_text[
                                             start_in_base_text + 2: end_in_base_text + 1])))

            return selections_from_base_text

        def get_plags_from_wiki_articles():

            plags = list()
            wiki_articles_plag = self.getWikiArticlesFromDB(number_plags, start_docid_plags)
            is_plag = True

            for article in wiki_articles_plag:
                article_docid = article[0]
                article_text = article[1].replace("\n", "")
                indices_of_sentence_endings = [m.start() for m in re.finditer('[^A-Z0-9]\.(?!\s[a-z])', article_text)]
                indices_of_sentence_endings = list(filter(
                    lambda x: re.match('[A-Z]', article_text[x + 2]) is not None or re.match('[A-Z]', article_text[
                        x + 3]) is not None, indices_of_sentence_endings))

                start_plag_index_within_list = random.randint(0, len(indices_of_sentence_endings))
                end_plag_index_within_list = start_plag_index_within_list + 1

                start_plag_index_within_article = indices_of_sentence_endings[
                                                      start_plag_index_within_list] + 3  # TODO: check index_out_of_bounds
                end_plag_index_within_article = indices_of_sentence_endings[end_plag_index_within_list]
                length_of_plag = end_plag_index_within_article - start_plag_index_within_article + 1

                plag = (start_plag_index_within_article, end_plag_index_within_article, length_of_plag,
                        article_text[start_plag_index_within_article:end_plag_index_within_article + 1])

                plags.append((article_docid, is_plag, plag))

            return plags

        def create_potential_plagiarism(subset_from_base_text, plags_from_wiki_articles):
            # TODO: what to do if number_plags > number_selections + 1 (meaning: much more plag than self-made)???

            # compute insertion positions for plags randomly (and begin fill in at end later on)
            insert_pos_list = sorted(random.sample(range(0, number_selections + 1), number_plags), reverse=True)

            # copy to don't tamper with original subset_from_base_text
            potential_plagiarisms_mix = copy.copy(subset_from_base_text)
            # potential_plagiarisms_mix should contain subset_from_base_text and plags of plags_from_wiki_articles
            plags_pos_index_in_pot_plagiarisms_mix = 0
            for insert_pos in insert_pos_list:
                potential_plagiarisms_mix.insert(insert_pos,
                                                 plags_from_wiki_articles[plags_pos_index_in_pot_plagiarisms_mix])
                plags_pos_index_in_pot_plagiarisms_mix += 1

            # finally: create potential_plagiarism_text and a list of start-end-tuples of plags inside of it
            potential_plagiarism_text = ""
            plags_pos_in_potential_plagiarism_text_list = list()
            plag_pos_in_potential_plagiarism_text_start = 0
            for part in potential_plagiarisms_mix:
                if part[1]:  # meaning: if is_plag...
                    potential_plagiarism_text += part[2][3] + ". "  # TODO: not too beautiful here
                    plags_pos_in_potential_plagiarism_text_list.append((plag_pos_in_potential_plagiarism_text_start,
                                                                        plag_pos_in_potential_plagiarism_text_start +
                                                                        part[2][2]))
                    plag_pos_in_potential_plagiarism_text_start += part[2][2]
                else:
                    potential_plagiarism_text += part[2][3] + " "  # TODO: not too beautiful here
                    plag_pos_in_potential_plagiarism_text_start += part[2][2]

            return (plags_pos_in_potential_plagiarism_text_list, potential_plagiarism_text), sorted(
                plags_from_wiki_articles, reverse=True)

        # compute list of potential_plagiarisms
        potential_plagiarisms = list()
        for i in range(number_plagiarism):
            potential_plagiarisms.append(create_potential_plagiarism(get_subset_from_base_text(),
                                                                     get_plags_from_wiki_articles()))

        return potential_plagiarisms

    def get_base_text(self):
        with open('base_text.txt') as f:
            base_text = f.read()

        return base_text.replace("\n", "")

    def getWikiArticlesFromDB(self, number_plags, start_docid):
        original_wiki_texts = list()

        # just for fun: choose random start_docid if negative value is given
        if start_docid < 0:
            start_docid = random.randint(1, 450000)

        while len(original_wiki_texts) < number_plags:
            try:
                resource = urllib.request.urlopen("http://localhost:8080/wikiplag/rest/documents/" + str(start_docid))
                text = resource.read().decode('utf-8')
                original_wiki_texts.append((start_docid, text))
            except:
                pass
            start_docid += 1

        return original_wiki_texts


if __name__ == "__main__":
    pc = PlagCreator()
    plagiarism = pc.createPlagiarism(2, 3, 4, -1)
    # print(plagiarism)
