import os
import urllib.request
import random
import re
import copy
import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import stats
from collections import defaultdict


class AlgorithmTester:
    def __init__(self, plagiarisms, analysis_endpoint):
        """
        Creates an AlgorithmTester

        :param plagiarisms: list of plagiarisms to use for testing
        :param analysis_endpoint: URL of analyse API to POST request at
        """
        self.analysis_endpoint = analysis_endpoint
        self.plagiarisms = plagiarisms

    def analyze(self, output_mode):

        if output_mode == 'object':
            analysis_results = list()

        for my_plagiarism in self.plagiarisms:
            if output_mode == 'string':
                print(my_plagiarism)
                print(self.compare_created_and_found_by_analysis_values(my_plagiarism, 'string') + os.linesep)
            elif output_mode == 'object':
                analysis_results.append(self.compare_created_and_found_by_analysis_values(my_plagiarism, 'object'))

        if output_mode == 'object':
            return analysis_results

    # mode = 'string'(string output); 'object'(AnalysisResult Object)
    def compare_created_and_found_by_analysis_values(self, plagiarism, output_mode):
        analysis_response = self.get_analysis_response_for_plagiarism(plagiarism)

        analysis_result = AnalysisResult()

        def compare_created_and_found_by_analysis_wiki_ids():
            wiki_ids_res_analysis = self.extract_info_of_wikiexcerpt_in_analysis_response(analysis_response, ["id"])
            wiki_ids_creation = self.extract_wiki_ids_of_plagiarism(plagiarism)
            wiki_ids_not_found = [not_found for not_found in wiki_ids_creation if
                                  not_found not in wiki_ids_res_analysis]

            if output_mode == 'string':
                return "Wiki Id's used for plag creation: " + str(wiki_ids_creation) + os.linesep \
                       + "Wiki Id's as result of analysis:  " + str(wiki_ids_res_analysis) + os.linesep \
                       + "Wiki Id's that weren't found:     " + str(wiki_ids_not_found) + os.linesep
            elif output_mode == 'object':
                analysis_result.plag_ids_gt = wiki_ids_creation
                analysis_result.plag_ids_ar = wiki_ids_res_analysis

        def compare_created_and_found_by_analysis_plag_positions_in_input_text():
            plag_position_in_input_text_ground_truth = self.extract_plag_position_in_input_text_ground_truth(plagiarism)
            plag_position_in_input_text_analysis_response = self.extract_plag_position_in_input_text_analysis_response(
                analysis_response)
            if output_mode == 'string':
                return comparison_response_string_builder(plag_position_in_input_text_ground_truth,
                                                          plag_position_in_input_text_analysis_response, "input")
            elif output_mode == 'object':
                analysis_result.input_text_positions_gt = plag_position_in_input_text_ground_truth
                analysis_result.input_text_positions_ar = plag_position_in_input_text_analysis_response

        def compare_created_and_found_by_analysis_plag_positions_in_wiki_text():
            plag_position_in_wikipedia_text_ground_truth = self.extract_plag_position_in_wiki_article_ground_truth(
                plagiarism)
            plag_position_in_wikipedia_text_analysis_response = \
                self.extract_plag_position_in_wikipedia_text_analysis_response(analysis_response)
            if output_mode == 'string':
                return comparison_response_string_builder(plag_position_in_wikipedia_text_ground_truth,
                                                          plag_position_in_wikipedia_text_analysis_response,
                                                          "wikipedia")
            elif output_mode == 'object':
                analysis_result.wiki_text_positions_gt = plag_position_in_wikipedia_text_ground_truth
                analysis_result.wiki_text_positions_ar = plag_position_in_wikipedia_text_analysis_response

        def comparison_response_string_builder(plag_position_ground_truth, plag_position_analysis_response, descriptor):
            plag_position_in_comparison = ""
            for plag_pos_input in plag_position_ground_truth:
                for plag_pos_input_analysis_resp in plag_position_analysis_response:
                    if plag_pos_input_analysis_resp[0] == plag_pos_input[0]:
                        plag_position_in_comparison = plag_position_in_comparison + "Positions in " + descriptor \
                                                      + " text ground truth:\t\t" + str(plag_pos_input) + os.linesep
                        plag_position_in_comparison = plag_position_in_comparison + "Positions in " + descriptor \
                                                      + " text analysis response:\t" + str(plag_pos_input_analysis_resp) \
                                                      + os.linesep
            return plag_position_in_comparison

        if output_mode == 'string':
            elapsed_time_statement = "Elapsed time for analysis (ms): " + str(
                self.extract_elapsed_time_of_analysis_response(analysis_response))
            return elapsed_time_statement + os.linesep + compare_created_and_found_by_analysis_wiki_ids() + os.linesep \
                   + compare_created_and_found_by_analysis_plag_positions_in_input_text() \
                   + os.linesep + compare_created_and_found_by_analysis_plag_positions_in_wiki_text()
        elif output_mode == 'object':
            analysis_result.elapsed_time = self.extract_elapsed_time_of_analysis_response(analysis_response)
            compare_created_and_found_by_analysis_wiki_ids()
            compare_created_and_found_by_analysis_plag_positions_in_input_text()
            compare_created_and_found_by_analysis_plag_positions_in_wiki_text()
            return analysis_result

    def get_analysis_response_for_plagiarism(self, plagiarism):
        return self.get_analysis_response(plagiarism[0][1])

    def get_analysis_response_for_input_file(self, input_file):
        with open(input_file, 'r', encoding='utf-8') as my_input_file:
            plag_text = my_input_file.read()
        return self.get_analysis_response(plag_text)

    def get_analysis_response(self, text):
        data = {"text": text}
        params_for_post = json.dumps(data).encode('utf8')
        req_for_post = urllib.request.Request(self.analysis_endpoint, data=params_for_post,
                                              headers={'content-type': 'application/json'})
        response = urllib.request.urlopen(req_for_post)
        return json.loads(response.read().decode('utf8'))

    @staticmethod
    def save_analysis_response_to_output_file(analysis_response, output_file):
        file = open(output_file, "w", encoding='utf-8')
        file.write(json.dumps(analysis_response, indent=4, sort_keys=True))  # beautification
        file.close()

    @staticmethod
    def extract_plag_position_in_input_text_ground_truth(plagiarisms):
        article_id_and_position_in_plag = list()
        for i in range(len(plagiarisms[0][0])):
            article_id_and_position_in_plag.append((plagiarisms[1][i][0], plagiarisms[0][0][i]))
        return article_id_and_position_in_plag

    @staticmethod
    def extract_plag_position_in_wiki_article_ground_truth(plagiarisms):
        article_id_and_position_in_wiki_article = list()
        for plag in plagiarisms[1]:
            article_id_and_position_in_wiki_article.append((plag[0], (plag[2][0], plag[2][1])))
        return article_id_and_position_in_wiki_article

    @staticmethod
    def extract_wiki_ids_of_plagiarism(plagiarism):
        wiki_ids_creation = list()
        plags_from_wiki_articles = plagiarism[1]
        for plag_from_wiki_articles in plags_from_wiki_articles:
            wiki_ids_creation.append(plag_from_wiki_articles[0])
        return wiki_ids_creation

    def extract_plag_position_in_input_text_analysis_response(self, response):
        return self.extract_info_of_wikiexcerpt_in_analysis_response(response, ['id', 'start', 'end'])

    def extract_plag_position_in_wikipedia_text_analysis_response(self, response):
        return self.extract_info_of_wikiexcerpt_in_analysis_response(
            response, ['id', 'start_of_plag_in_wiki', 'end_of_plag_in_wiki'])

    @staticmethod
    def extract_info_of_wikiexcerpt_in_analysis_response(response, fields_of_interest):
        computed_responses = list()
        list_of_plags = response['plags']
        wiki_excerpts = list()
        for list_of_plag in list_of_plags:
            wiki_excerpts.append(list_of_plag['wiki_excerpts'])

        # flattens wiki_excerpts list:
        wiki_excerpts = [y for x in wiki_excerpts for y in x]
        for wiki_excerpt in wiki_excerpts:
            if len(fields_of_interest) == 1:
                computed_responses.append(wiki_excerpt[fields_of_interest[0]])
            elif len(fields_of_interest) == 3:
                computed_responses.append((wiki_excerpt[fields_of_interest[0]],
                                           (wiki_excerpt[fields_of_interest[1]], wiki_excerpt[fields_of_interest[2]])))
            else:
                raise IndexError('List has to be of length one or three.')

        return computed_responses

    @staticmethod
    def extract_elapsed_time_of_analysis_response(response):
        return response['elapsed_time']


class PlagiarismCreator:
    def __init__(self, documents_endpoint="http://wikiplag.f4.htw-berlin.de:8080/wikiplag/rest/documents/"):
        """
        A Plagiarism is a mixture of self-written text and plags (c&p text from wikipedia)
        Self-written sentences come from a "base text". They are neither considered as nor recognized as plags.

        :param documents_endpoint: URL of documents API to get wikipedia articles from (default: wikiplag server)
        """
        # get the base text, the plags are gonna be mixed with
        self.base_text = self.get_base_text().replace("\n", "")
        self.documents_endpoint = documents_endpoint
        self.min_sentence_length_for_positioning = 12

    def create(self, number_plagiarism, number_selections, number_plags, start_docid_plags):
        """
        Creates a plagiarism - a mixture of self-written text and plags (c&p text from wikipedia)
        :param number_plagiarism: number of plagiarisms to create
        :param number_selections: number of self-written sentences in each plagiarism
        :param number_plags: number of plag sentences (each taken from a different wikipedia article) per plagiarism
        :param start_docid_plags: wikipedia article id to start getting plags from
                (< 0 means: choose randomly from first 450,000 wiki articles)
        :return: list of generated plagiarisms including info about the plags sources and their positions in mixed text
        """

        def get_subset_from_base_text():
            indices_of_sentence_endings = [m.start() for m in re.finditer('\.', self.base_text)]
            selections_from_base_text = list()
            is_plag = False

            for selection_number in range(number_selections):
                # index within the list, not the text
                start = random.randint(0, len(indices_of_sentence_endings) - 20)
                end = random.randint(start + 2, start + 10)
                start_in_base_text = indices_of_sentence_endings[start]
                end_in_base_text = indices_of_sentence_endings[end]
                start_end_in_base_text = (start_in_base_text, end_in_base_text)
                length_of_selection = len(self.base_text[start_in_base_text + 2: end_in_base_text + 1])
                selection_id = selection_number + 1
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
            wiki_articles_plag = list()
            while is_there_a_small_sentence_list:
                wiki_articles_plag = self.get_wiki_articles_from_db(number_plags, start_docid_plags)
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
                article_text = article[1]  # .replace("\n", "")
                indices_of_sentence_endings = [m.start() for m in re.finditer('[^A-Z0-9]\.(?!\s[a-z])', article_text)]
                indices_of_sentence_endings = list(filter(
                    lambda x: re.match('[A-Z]', article_text[x + 2]) is not None or re.match('[A-Z]', article_text[
                        x + 3]) is not None, indices_of_sentence_endings))

                # select random sentence ending but not the last one
                start_plag_index_within_list = random.randint(0, (len(indices_of_sentence_endings) - 2))
                end_plag_index_within_list = start_plag_index_within_list + 1

                # get the first character of the sentence following the previously selected sentence ending
                start_plag_index_within_article = indices_of_sentence_endings[
                                                      start_plag_index_within_list] + 3
                end_plag_index_within_article = indices_of_sentence_endings[end_plag_index_within_list] + 1

                # due to the sentence split, punctuation is lost, which is a problem for position determination,
                # therefore a dot is appended to wiki excerpt
                plag_excerpt = article_text[start_plag_index_within_article:end_plag_index_within_article] + "."
                length_of_plag = len(plag_excerpt)

                plag_excerpt = plag_excerpt.replace("\n", "")

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
                part_index = 0
                for part in potential_plagiarism_mix:
                    potential_plagiarism_text += part[2][3] + " "
                    if part[1]:  # meaning: save position if is_plag
                        correction_amount = \
                            correct_position_in_potential_plagiarism_text_depending_on_previous_sentence_length(
                                potential_plagiarism_mix, part_index)
                        plags_pos_in_potential_plagiarism_text_list.append((plag_pos_in_potential_plagiarism_text_start
                                                                            - correction_amount,
                                                                            plag_pos_in_potential_plagiarism_text_start
                                                                            + part[2][2] + 1))
                    plag_pos_in_potential_plagiarism_text_start += part[2][2] + 1
                    part_index = part_index + 1

                return plags_pos_in_potential_plagiarism_text_list, potential_plagiarism_text

            def correct_position_in_potential_plagiarism_text_depending_on_previous_sentence_length(
                    potential_plagiarism_mix, part_index):
                if part_index == 0:
                    return 0
                else:
                    # get the text of the previous part
                    text = potential_plagiarism_mix[part_index - 1][2][3]
                    sentence_list = re.split('\. |, |\? |! ', text)
                    last_sentence = sentence_list[-1]
                    if len(last_sentence) <= self.min_sentence_length_for_positioning:
                        return len(last_sentence)
                    else:
                        return 0

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

            return create_plagiarism_text_and_store_plag_positions(create_potential_plagiarism_mix()), sorted(
                plags_from_wiki_articles, reverse=enough_selections_for_plags())

        # compute list of potential_plagiarisms
        potential_plagiarisms = list()
        for i in range(number_plagiarism):
            potential_plagiarisms.append(create_potential_plagiarism(get_subset_from_base_text(),
                                                                     get_plags_from_wiki_articles()))

        return potential_plagiarisms

    @staticmethod
    def get_base_text():
        with open('base_text.txt') as f:
            base_text = f.read()

        return base_text

    def get_wiki_articles_from_db(self, number_plags, start_docid):
        original_wiki_texts = list()

        # just for fun: choose random start_docid if negative value is given
        if start_docid < 0:
            start_docid = random.randint(1, 450000)

        while len(original_wiki_texts) < number_plags:
            try:
                resource = urllib.request.urlopen(self.documents_endpoint + str(start_docid))
                text = resource.read().decode('utf-8')
                original_wiki_texts.append((start_docid, text))
            except:
                pass
            start_docid += 1

        return original_wiki_texts


class AnalysisResult:
    # suffixes: gt = ground truth; ar = analysis response
    # plag_ids_gt (type = list of scalars): plags that were placed into the text that was analyzed
    # plag_ids_ar (type = list of scalars): plags that were identified by the algorithm
    # input_text_positions_gt (type = list of tuples[from, to]): true text positions of plags in input text
    # input_text_positions_ar (type = list of tuples[from, to]): text pos of plags in input text as determined by algo
    # same with wiki article positions
    def __init__(self, elapsed_time=None, plag_ids_gt=None, plag_ids_ar=None, input_text_positions_gt=None,
                 input_text_positions_ar=None, wiki_text_positions_gt=None, wiki_text_positions_ar=None):
        self.elapsed_time = elapsed_time

        self.plag_ids_gt = plag_ids_gt
        self.plag_ids_ar = plag_ids_ar

        self.input_text_positions_gt = input_text_positions_gt
        self.input_text_positions_ar = input_text_positions_ar
        self.wiki_text_positions_gt = wiki_text_positions_gt
        self.wiki_text_positions_ar = wiki_text_positions_ar


class AlgorithmComparator:
    # it is important that all algorithms have been fed with the same texts
    # algo_results is supposed to be a list of tuples with ('name of algo', AnalysisResult-Object)
    # create_parameters: parameters that were used to create plags
    # algo_parameters: parameters that were used in the algorithm
    def __init__(self, algo_results, create_parameters=None, algo_parameters=None):
        self.algo_results = algo_results
        self.wiki_text_deviation_distr = None
        self.input_text_deviation_distr = None
        self.average_share_plags_distr = None
        self.elapsed_time_distr = None
        self.data = pd.DataFrame(columns=["index", "algo", "wiki_text_deviation", "input_text_deviation", "average_share_plags_found", "elapsed_time"])

    def compare_algorithms(self):

        # average per input text
        def get_average_elapsed_time(results):
            time_sum = 0
            for result in results:
                time_sum = time_sum + result.elapsed_time
            return time_sum / len(results)

        # average per input text
        def get_average_share_plags_found(results):
            share_sum = 0
            for result in results:
                number_found = np.intersect1d(np.array(result.plag_ids_gt), np.array(result.plag_ids_ar))
                share_sum = share_sum + len(number_found) / len(result.plag_ids_gt)
            return share_sum / len(results)

        # average per found plag
        def get_average_input_text_deviation(results):
            deviations = list()
            for result in results:
                for ground_truth in result.input_text_positions_gt:
                    for analysis_response in result.input_text_positions_ar:
                        if ground_truth[0] == analysis_response[0]:
                            start = abs(ground_truth[1][0] - analysis_response[1][0])
                            end = abs(ground_truth[1][1] - analysis_response[1][1])
                            deviations.append(start + end)

            return np.array(deviations).mean()

        # average per found plag
        def get_average_wiki_text_deviation(results):
            deviations = list()
            for result in results:
                for ground_truth in result.wiki_text_positions_gt:
                    for analysis_response in result.wiki_text_positions_ar:
                        if ground_truth[0] == analysis_response[0]:
                            start = abs(ground_truth[1][0] - analysis_response[1][0])
                            end = abs(ground_truth[1][1] - analysis_response[1][1])
                            deviations.append(start + end)

            return np.array(deviations).mean()

        def put_elapsed_time_into_distr(results):
            self.elapsed_time_distr = list()
            for result in results:
                self.elapsed_time_distr.append(result.elapsed_time)

        def put_share_plags_found_into_distr(results):
            self.average_share_plags_distr = list()
            for result in results:
                number_found = np.intersect1d(np.array(result.plag_ids_gt), np.array(result.plag_ids_ar))
                self.average_share_plags_distr.append(len(number_found) / len(result.plag_ids_gt))

        def put_input_text_deviation_into_distr(results):
            self.input_text_deviation_distr = list()
            for result in results:
                for ground_truth in result.input_text_positions_gt:
                    for analysis_response in result.input_text_positions_ar:
                        if ground_truth[0] == analysis_response[0]:
                            start = abs(ground_truth[1][0] - analysis_response[1][0])
                            end = abs(ground_truth[1][1] - analysis_response[1][1])
                            self.input_text_deviation_distr.append(start + end)

        def put_wiki_text_deviation_into_distr(results):
            self.wiki_text_deviation_distr = list()
            for result in results:
                for ground_truth in result.wiki_text_positions_gt:
                    for analysis_response in result.wiki_text_positions_ar:
                        if ground_truth[0] == analysis_response[0]:
                            start = abs(ground_truth[1][0] - analysis_response[1][0])
                            end = abs(ground_truth[1][1] - analysis_response[1][1])
                            self.wiki_text_deviation_distr.append(start + end)

        def put_results_into_dataframe(idx, algo_name):
            index = np.full(len(self.wiki_text_deviation_distr), idx)
            id = np.full(len(self.wiki_text_deviation_distr), algo_name)
            data_zipped_list = list(zip(index,id,self.wiki_text_deviation_distr,self.input_text_deviation_distr,self.average_share_plags_distr,self.elapsed_time_distr))
            self.data = pd.concat([self.data, pd.DataFrame(data_zipped_list, columns=["index", "algo", "wiki_text_deviation", "input_text_deviation", "average_share_plags_found", "elapsed_time"])])

        def compute_statistical_evidence_for_group_differences():
            grouped_data = self.data.groupby(["algo"])
            results = defaultdict(list)

            for algo_1 in grouped_data:
                for algo_2 in grouped_data:
                    if algo_1[0] != algo_2[0]:
                        u, p = stats.mannwhitneyu(algo_1[1]["wiki_text_deviation"], algo_2[1]["wiki_text_deviation"])
                        results[algo_1[0]].append((algo_2[0], p))

            return results


        def make_histograms():
            plt.figure()
            plt.hist(self.elapsed_time_distr)
            plt.title('elapsed time')
            plt.figure()
            plt.hist(self.average_share_plags_distr)
            plt.title('share of found plags')
            plt.figure()
            plt.hist(self.input_text_deviation_distr)
            plt.title('deviation from input text')
            plt.figure()
            plt.hist(self.wiki_text_deviation_distr)
            plt.title('deviation from wiki text')




        for idx, algo in enumerate(self.algo_results):
            put_elapsed_time_into_distr(algo[1])
            put_input_text_deviation_into_distr(algo[1])
            put_share_plags_found_into_distr(algo[1])
            put_wiki_text_deviation_into_distr(algo[1])
            put_results_into_dataframe(idx, algo[0])
            print("Algorithm: ", algo[0])
            print("Average elapsed time: ", get_average_elapsed_time(algo[1]))
            print("Average share of found plags: ", get_average_share_plags_found(algo[1]))
            print("Average deviation from input text position: ", get_average_input_text_deviation(algo[1]))
            print("Average deviation from wiki text position: ", get_average_wiki_text_deviation(algo[1]))
            make_histograms()

        statistical_comparison_results = compute_statistical_evidence_for_group_differences()

        print(statistical_comparison_results)

        plt.show()




if __name__ == "__main__":
    # Step 1: create plagiarisms
    plagiarism_creator = PlagiarismCreator()  # or: PlagiarismCreator("http://localhost:8080/wikiplag/rest/documents/")
    # create 10 documents, each containing 2 "self-written" sections and 4 plagiarized sections, -1 = select plag-sections
    # randomly from the first 450,000 wiki-articles
    my_plagiarisms_for_tests = plagiarism_creator.create(3, 2, 4, -1)

    # Step 2: test an algorithm
    wikiplag_tester = AlgorithmTester(my_plagiarisms_for_tests,
                                      "http://wikiplag.f4.htw-berlin.de:8080/wikiplag/rest/analyse")

    wikiplag_tester_test_for_statistics = AlgorithmTester(my_plagiarisms_for_tests,
                                      "http://wikiplag.f4.htw-berlin.de:8080/wikiplag/rest/analyse")
    # or for localhost: "http://localhost:8080/wikiplag/rest/analyse"

    # Example usage for another algorithm:
    # word2vec_tester = AlgorithmTester(my_plagiarisms_for_tests, "put analysis_endpoint of word2vec algorithm here")

    # Put tester objects into list
    # algorithm_testers = [wikiplag_tester, ...]

    # this needs to be done in a loop if there is more than one algorithm, results need to be put in a list
    analysis_results_wikiplag = wikiplag_tester.analyze('object')
    analysis_results_wikiplag_test_for_statistics = wikiplag_tester_test_for_statistics.analyze("object")
    print(wikiplag_tester.analyze('string'))

    # the list is fed into the AlgorithmComparator
    algorithm_comparator = AlgorithmComparator(list([("wikiplag", analysis_results_wikiplag), ("wikiplag_test_for_statistics", analysis_results_wikiplag_test_for_statistics)]))
    algorithm_comparator.compare_algorithms()

    # Example usage of input/ output file read and write
    analysis_resp = wikiplag_tester.get_analysis_response_for_input_file('request/input.txt')
    wikiplag_tester.save_analysis_response_to_output_file(analysis_resp, 'response/response.txt')
