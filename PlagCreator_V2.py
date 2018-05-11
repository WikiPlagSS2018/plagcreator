import urllib.request

def createPlag(number_plags, plag_length, max_word_dist, base_text_length):

    original_wiki_texts = list()

    start_docid = 1
    while len(original_wiki_texts) < number_plags:
        try:
            original_wiki_texts.append(urllib.request.urlopen("http://localhost:8080/wikiplag/rest/documents/" + str(start_docid)).read().decode('utf-8'))
        except(urllib.error.HTTPError):
            pass
        start_docid+=1



if __name__ == "__main__":
    createPlag(10,1,1,1)
