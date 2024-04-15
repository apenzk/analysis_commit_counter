# analysis_commit_counter

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
pip3 install requests
pip3 install matplotlib
```


## Usage

```
python3 main.py
```