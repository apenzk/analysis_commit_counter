# analysis_commit_counter

Extract the number and distribution of commits accross all public repos of an organisation. The distribution is then processed and displayed in a png graph.

## Setup

create `config.py` file with the following content:

```
access_token = "mytoken" 
organization = "targetorg"
```
where the organization is taken from `https://github.com/targetorg`

The github token should have the permission `public_repo access`

## Dependencies

```
python3 -m venv venv    
source venv/bin/activate
pip3 install requests
pip3 install matplotlib
deactivate     # to exit the virtual environment
```


## Usage

```
python3 main.py
```