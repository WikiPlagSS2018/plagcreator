import os
import urllib.request
import random
import re
import copy
import json
import numpy as np


class PlagCreator:
    def __init__(self):
        # get the base text, the plags are gonna be mixed with
        self.base_text = self.get_base_text().replace("\n", "")
        self.base_url = "http://localhost:8080/wikiplag/rest"
        # 'http://wikiplag.f4.htw-berlin.de:8080/wikiplag/rest'

    # number_plagiarism: overall number of texts to be analyzed
    # number_selections: overall number of

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

            # check for wiki articles that are too small (<5 sentences)
            is_there_a_small_sentence_list = True
            while is_there_a_small_sentence_list:
                wiki_articles_plag = self.getWikiArticlesFromDB(number_plags, start_docid_plags)
                length_list = np.array([])
                for article in wiki_articles_plag:
                    article_text = article[1]
                    indices_of_sentence_endings = [m.start() for m in
                                                   re.finditer('[^A-Z0-9]\.(?!\s[a-z])', article_text)]
                    indices_of_sentence_endings = list(filter(
                        lambda x: re.match('[A-Z]', article_text[x + 2]) is not None or re.match('[A-Z]', article_text[
                            x + 3]) is not None, indices_of_sentence_endings))
                    length_list = np.append(length_list, len(indices_of_sentence_endings))
                if len(length_list[np.where(length_list < 5)]) > 0:
                    is_there_a_small_sentence_list = True
                else:
                    is_there_a_small_sentence_list = False

            is_plag = True

            for article in wiki_articles_plag:
                article_docid = article[0]
                article_text = article[1]
                indices_of_sentence_endings = [m.start() for m in re.finditer('[^A-Z0-9]\.(?!\s[a-z])', article_text)]
                indices_of_sentence_endings = list(filter(
                    lambda x: re.match('[A-Z]', article_text[x + 2]) is not None or re.match('[A-Z]', article_text[
                        x + 3]) is not None, indices_of_sentence_endings))

                # select random sentence ending but not the last one
                start_plag_index_within_list = random.randint(0, (len(indices_of_sentence_endings) - 2))
                end_plag_index_within_list = start_plag_index_within_list + 1

                # get the first character of the sentence following the previously selected sentence ending
                start_plag_index_within_article = indices_of_sentence_endings[
                                                      start_plag_index_within_list] + 3  # TODO: check index_out_of_bounds --> should not happen anymore
                end_plag_index_within_article = indices_of_sentence_endings[end_plag_index_within_list]
                length_of_plag = end_plag_index_within_article - start_plag_index_within_article + 1

                # due to the sentence split, punctuation is lost, which is a problem for position determination, therefore a dot is appended to wiki excerpt
                plag_excerpt = article_text[start_plag_index_within_article:end_plag_index_within_article + 1] + "."
                plag = (start_plag_index_within_article, end_plag_index_within_article, length_of_plag,
                        plag_excerpt)

                plags.append((article_docid, is_plag, plag))

            return plags

        def create_potential_plagiarism(subset_from_base_text, plags_from_wiki_articles):

            def create_potential_plagiarism_mix():
                fill_into_set, set_with_fill_ins = get_fill_into_set_first()
                insert_pos_list = compute_insertion_positions()
                potential_plagiarism_mix = copy.copy(fill_into_set)
                pos_index_in_pot_plagiarisms_mix = 0
                for insert_pos in insert_pos_list:
                    potential_plagiarism_mix.insert(insert_pos,
                                                    set_with_fill_ins[pos_index_in_pot_plagiarisms_mix])
                    pos_index_in_pot_plagiarisms_mix += 1

                return potential_plagiarism_mix

            def create_plagiarism_text_and_store_plag_positions(potential_plagiarism_mix):
                potential_plagiarism_text = ""
                plags_pos_in_potential_plagiarism_text_list = list()
                plag_pos_in_potential_plagiarism_text_start = 0
                for part in potential_plagiarism_mix:
                    potential_plagiarism_text += part[2][3] + " "
                    if part[1]:  # meaning: save position if is_plag
                        plags_pos_in_potential_plagiarism_text_list.append((plag_pos_in_potential_plagiarism_text_start,
                                                                            plag_pos_in_potential_plagiarism_text_start
                                                                            + part[2][2] + 1))
                    plag_pos_in_potential_plagiarism_text_start += part[2][2] + 1

                return plags_pos_in_potential_plagiarism_text_list, potential_plagiarism_text

            def compute_insertion_positions():
                if enough_selections_for_plags():
                    return sorted(random.sample(range(0, number_selections + 1), number_plags), reverse=True)
                else:
                    return sorted(random.sample(range(0, number_plags + 1), number_selections), reverse=True)

            def get_fill_into_set_first():
                if enough_selections_for_plags():
                    return subset_from_base_text, plags_from_wiki_articles
                else:
                    return plags_from_wiki_articles, subset_from_base_text

            def enough_selections_for_plags():
                return number_plags <= number_selections + 1

            return create_plagiarism_text_and_store_plag_positions(create_potential_plagiarism_mix()), \
                   sorted(plags_from_wiki_articles, reverse=enough_selections_for_plags())

        # compute list of potential_plagiarisms
        potential_plagiarisms = list()
        for i in range(number_plagiarism):
            potential_plagiarisms.append(create_potential_plagiarism(get_subset_from_base_text(),
                                                                     get_plags_from_wiki_articles()))

        return potential_plagiarisms

    def get_base_text(self):
        with open('base_text.txt') as f:
            base_text = f.read()

        return base_text

    def getWikiArticlesFromDB(self, number_plags, start_docid):
        original_wiki_texts = list()

        # just for fun: choose random start_docid if negative value is given
        if start_docid < 0:
            start_docid = random.randint(1, 450000)

        while len(original_wiki_texts) < number_plags:
            try:
                resource = urllib.request.urlopen(self.base_url + "/documents/" + str(start_docid))
                text = resource.read().decode('utf-8')
                original_wiki_texts.append((start_docid, text))
            except:
                pass
            start_docid += 1

        return original_wiki_texts

    def getAnalysisResponseForPlagiarism(self, plagiarism):
        url = self.base_url + "/analyse"
        data = {"text": plagiarism[0][1]}
        params_for_post = json.dumps(data).encode('utf8')
        req_for_post = urllib.request.Request(url, data=params_for_post, headers={'content-type': 'application/json'})
        response = urllib.request.urlopen(req_for_post)
        return json.loads(response.read().decode('utf8'))

    def compareCreatedAndFoundByAnalysisValues(self, plagiarism):
        analysis_response = self.getAnalysisResponseForPlagiarism(plagiarism)

        def compareCreatedAndFoundByAnalysisPlagPositionsInInputText():
            plag_position_in_input_text_ground_truth = self.extract_plag_position_in_input_text_ground_truth(plagiarism)
            plag_position_in_input_text_analysis_response = self.extract_plag_position_in_input_text_analysis_response(
                analysis_response)
            plag_position_in_input_text_comparison = ""

            for plag_pos_input in plag_position_in_input_text_ground_truth:
                plag_position_in_input_text_comparison = plag_position_in_input_text_comparison + "Positions in input text ground truth:\t\t" + str(
                    plag_pos_input) + os.linesep
                for plag_pos_input_analysis_resp in plag_position_in_input_text_analysis_response:
                    if plag_pos_input_analysis_resp[0] == plag_pos_input[0]:
                        plag_position_in_input_text_comparison = plag_position_in_input_text_comparison + "Positions in input text analysis response:\t" + str(
                            plag_pos_input_analysis_resp) + os.linesep

            return plag_position_in_input_text_comparison

        def compareCreatedAndFoundByAnalysisWikiIds():
            wiki_ids_res_analysis = self.extractWikiIdsOfAnalysisResponse(analysis_response)
            wiki_ids_creation = self.extractWikiIdsOfPlagiarism(plagiarism)
            wiki_ids_not_found = [not_found for not_found in wiki_ids_creation if
                                  not_found not in wiki_ids_res_analysis]

            return "Wiki Id's used for plag creation: " + str(wiki_ids_creation) + os.linesep \
                   + "Wiki Id's as result of analysis:  " + str(wiki_ids_res_analysis) + os.linesep \
                   + "Wiki Id's that weren't found:     " + str(wiki_ids_not_found) + os.linesep \

        return compareCreatedAndFoundByAnalysisWikiIds() + \
               compareCreatedAndFoundByAnalysisPlagPositionsInInputText()

    def extractWikiIdsOfPlagiarism(self, plagiarism):
        wiki_ids_creation = list()
        plags_from_wiki_articles = plagiarism[1]
        for plag_from_wiki_articles in plags_from_wiki_articles:
            wiki_ids_creation.append(plag_from_wiki_articles[0])
        return wiki_ids_creation

    def extractWikiIdsOfAnalysisResponse(self, response):
        wiki_ids_res_analysis = list()
        list_of_plags = response['plags']
        wiki_excerpts = list()
        for list_of_plag in list_of_plags:
            wiki_excerpts.append(list_of_plag['wiki_excerpts'])

        # flattens wiki_excerpts list:
        wiki_excerpts = [y for x in wiki_excerpts for y in x]
        for wiki_excerpt in wiki_excerpts:
            wiki_ids_res_analysis.append(wiki_excerpt['id'])

        return wiki_ids_res_analysis

    def extract_plag_position_in_input_text_ground_truth(self, plagiarisms):
        article_id_and_position_in_plag = list()
        for i in range(len(plagiarisms[0][0])):
            article_id_and_position_in_plag.append((plagiarisms[1][i][0], plagiarisms[0][0][i]))
        return article_id_and_position_in_plag

    def extract_plag_position_in_wiki_article_ground_truth(self, plagiarisms):
        article_id_and_position_in_wiki_article = list()
        for plag in plagiarisms[1]:
            article_id_and_position_in_wiki_article.append((plag[0], (plag[2][0], plag[2][1])))
        return article_id_and_position_in_wiki_article

    def extract_plag_position_in_input_text_analysis_response(self, response):
        wiki_ids_pos_in_input_text_res_analysis = list()
        list_of_plags = response['plags']
        wiki_excerpts = list()
        for list_of_plag in list_of_plags:
            wiki_excerpts.append(list_of_plag['wiki_excerpts'])

        # flattens wiki_excerpts list:
        wiki_excerpts = [y for x in wiki_excerpts for y in x]
        for wiki_excerpt in wiki_excerpts:
            wiki_ids_pos_in_input_text_res_analysis.append(
                (wiki_excerpt['id'], (wiki_excerpt['start'], wiki_excerpt['end'])))

        return wiki_ids_pos_in_input_text_res_analysis


if __name__ == "__main__":
    pc = PlagCreator()
    plagiarisms = pc.createPlagiarism(1, 2, 4, -1)
    for plagiarism in plagiarisms:
        print(plagiarism)
        print(pc.compareCreatedAndFoundByAnalysisValues(plagiarism) + os.linesep)
