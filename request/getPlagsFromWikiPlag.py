import json
import requests


def getResponseAndSaveInFile(input_file, output_file):
    '''
    Send request to wikiplag and save output as beautified json in file
    :param input_file: a given input text with potential plagiarisms
    :param output_file: the file for writing the output to
    '''
    plag_text = ''
    with open(input_file, 'r', encoding='utf-8') as myfile:
        plag_text = myfile.read()
    r = requests.post('http://wikiplag.f4.htw-berlin.de:8080/wikiplag/rest/analyse', json={'text': plag_text})
    file = open(output_file, "w", encoding='utf-8')
    file.write(json.dumps(json.loads(r.text), indent=4))
    file.close()


getResponseAndSaveInFile('request/input.txt', 'request/reponse.txt')
