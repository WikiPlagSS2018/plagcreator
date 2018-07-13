# plagcreator (version 1)
Tool for generate plagiarisms for testing. By default stores the generated plagiarisms in the ./plag directory.

### Requires:
- python3

### Install and run:
1. git clone https://github.com/WikiplagSS2018/plagcreator
2. python PlagCreator.py


21-10-2017 Tested on Windows 10 with python 3.5.2


## Manual test of plags
0. Prerequisites

    install HTTPie ```sudo apt-get install httpie```

1. start REST-API of wikiplag-multi project (locally)
2. request result of analysis at API (using HTTPie)

    ```http POST http://localhost:8080/wikiplag/rest/analyse text="potential_plag_text"```

# plagcreator (version 2)
Tool to generate plagiarisms, to test detection algorithm(s) and to compare the results of the algorithm tests against each others. 

(Optional: stores the generated plagiarisms in the ./request directory and analysis responses to ./response)

09-07-2018 Tested on Ubuntu 14.04 & 16.04, IntelliJ IDEA 2018.1.5 (Ultimate) with python 3.6.4

### API requirement: analysis endpoint
To test an detection algorithm with PlagCreator_V2, an analysis endpoint has to be given as in wikiplag project.

Example: 

- Request Payload:
```json
{
  "text": "Daniel Stenberg, der Programmierer von cURL, begann 1997 ein Programm zu schreiben,das IRC-Teilnehmern Daten über Wechselkurse zur Verfügung stellen sollte, welche von Webseiten abgerufen werden mussten. Er hat dabei auf das schon vorhandene und sehr verbreitete Open-Source-Tool httpget aufgesetzt. Nach einer Erweiterung um andere Protokolle wurde das Programm am 20. März 1998 als cURL 4 erstmals veröffentlicht." 
}
```
- RESPONSE
```json
{
    "elapsed_time": 1650, 
    "plags": [
        {
            "id": 0, 
            "wiki_excerpts": [
                {
                    "end": 202, 
                    "end_of_plag_in_wiki": 796, 
                    "excerpt": "[...] .== Geschichte ==<span class=\"wiki_plag\">Daniel Stenberg, der Programmierer von cURL, begann 1997 ein Programm zu schreiben, das IRC-Teilnehmern Daten über Wechselkurse zur Verfügung stellen sollte, welche von Webseiten</span> abgerufen werden mu [...]", 
                    "id": 474951, 
                    "start": 0, 
                    "start_of_plag_in_wiki": 618, 
                    "title": "CURL"
                }
            ]
        }, 
        {
            "id": 1, 
            "wiki_excerpts": [
                {
                    "end": 414, 
                    "end_of_plag_in_wiki": 983, 
                    "excerpt": "[...] httpget. Nach einer <span class=\"wiki_plag\">Erweiterung um andere Protokolle wurde das Programm am 20. März 1998 als cURL 4 erstmals</span> veröffentlicht.== [...]", 
                    "id": 474951, 
                    "start": 299, 
                    "start_of_plag_in_wiki": 895, 
                    "title": "CURL"
                }
            ]
        }
    ], 
    "tagged_input_text": "<span id='0' class='input_plag'>Daniel Stenberg, der Programmierer von cURL, begann 1997 ein Programm zu schreiben,das IRC-Teilnehmern Daten über Wechselkurse zur Verfügung stellen sollte, welche von Webseiten abgerufen werden mussten</span>. Er hat dabei auf das schon vorhandene und sehr verbreitete Open-Source-Tool httpget aufgesetzt.<span id='1' class='input_plag'> Nach einer Erweiterung um andere Protokolle wurde das Programm am 20. März 1998 als cURL 4 erstmals veröffentlicht</span>."
}
```

### Software requirements:
- python3
- panda
- numpy
- scipy

### Install and run:
1. git clone https://github.com/WikiplagSS2018/plagcreator
2. start main of PlagCreator_V2.py in IDE (IntelliJ IDEA recommended)

Hint: functionality of PlagCreator_V2 is described in examples in it's main. Also in it's classes and methods documentation.

### Comparison
The Wilcoxon signed-rank test is used, because it is a non-parametric test for related samples. A non-parametric test should be 
reasonable, because most of the result distributions are right-skewed and normal distributions cannot be assumed.
A test for related samples seemed reasonable, because all algorithms are fed with the same texts, which act as samples.

The Wilcoxon signed-rank test yields a p-value, which indicates whether a difference between two algorithms can be considered
random or non-random/significant. If the p-value is below 0.05, there is evidence for the difference being significant.

#### Minimum plagiarism sample size
Because the normal approximation is used for the calculations, the samples used should be large. 
A typical rule is to require that n > 20. 

So create at least 21 plagiarisms for a testing sample used for testing of detection algorithms and comparison of the results. 

#### Persistence of comparison result
The comparison results are stored in files:

Detailed results for all input texts:
```./algo_results_detailed.csv```

Results for statistical comparison of algorithms:
```./wilcoxon_difference_results.csv```