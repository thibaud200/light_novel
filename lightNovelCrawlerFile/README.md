========================================================================================================================================================================================
# lightnovel-crawler requirement file for the lightnovel-crawler app

Go and see here for the app and the details https://github.com/dipu-bd/lightnovel-crawler
## 1. Prérequities

1. **Install the following tools**:
    - [Python v3.12.3] or [Python v3.13.5]([https://www.python.org/downloads/](https://www.python.org/downloads/release/)) << the crawler seems to have install/running problems with the latests version of python
            - best way to do it, is to prepare a virtual environnement for it :
      ** Windows :** (v3.13.5)
      ```bash
      py -3.13 -m venv lightnovel_313_env
      lightnovel_313_env\Scripts\activate
      pip install -U lightnovel-crawler
      ```
      
	  ** linux(Ubuntu virtual env from windows) :** (v3.12.3)
      ```bash
      python3 -m venv .venv
      source .venv/bin/activate
      pip install -r requirements.txt
      ```
 and then of course get the files from https://github.com/dipu-bd/lightnovel-crawler