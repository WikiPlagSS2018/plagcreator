# plagcreator
Tool for generate plagiarisms for testing. By default stores the generated plagiarisms in the ./plag directory.

### Requires:
- python3

### Install and run:
1. git clone https://github.com/WikiplagSS2018/plagcreator
2. python PlagCreator.py


21-10-2017 Tested on Windows 10 with python 3.5.2


### Manual test of plags
0. Prerequisites

    install HTTPie ```sudo apt-get install httpie```

1. start REST-API of wikiplag-multi project locally
2. request result of analysis at API (using HTTPie)

    ```http POST http://localhost:8080/wikiplag/rest/analyse text="potential_plag_text"```