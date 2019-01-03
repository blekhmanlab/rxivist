# rxivist spider

## Running the spider for real
The web crawler runs in a lightly customized Docker container and can be launched from any server (or workstation) that has access to the database.

```sh
git clone https://github.com/blekhmanlab/rxivist.git
cd rxivist/spider
docker build . -t rxspider:latest
docker run -it --rm --name rxspider -v "$(pwd)":/app --env RX_DBPASSWORD --env RX_DBHOST  rxspider:latest
```

### Configuration

The spider uses a separate configuration file (`config.py`) from the one used by the API. There are extensive comments in that file to explain which variable control what behavior; the `crawl` dictionary is probably the one that you will change most often. Its keys turn on and off major sections of the code:

* `"fetch_new"`: Set to `True` to record preprints that have been posted since the last time this was run.
* `"fetch_collections"`: Set to `True` to parse bioRxiv's category-specific listings of the latest preprints. Papers will still be indexed if this is set to `False`, but this is currently the only way to associate a preprint with whatever collection it was posted to.
* `"fetch_abstracts"`: Set to `True` to fetch abstracts for any preprints that don't have them recorded yet. (A separate call is required to record the abstract of each preprint.) Papers will still be indexed if this is set to `False`, but this is currently the only way to associate a preprint with its abstract.
* `"fetch_crossref"`: Set to `True` to fetch and record the number of tweets mentioning any documents registered in the `10.1101` DOI prefix, which includes all of bioRxiv. The first time this is run in a given day, it will also update the count from the previous day.
* `"refresh_stats"`: Set to `True` to iterate through all preprints that have not been updated in a given number of days (set by the `refresh_interval` config value) and retrieve updated download metrics. Depending on how many papers are out of date (and the value of `refresh_category_cap`), this can run for a long time.


## Development

You can use a technique similar to the one described in [the API's README](https://github.com/blekhmanlab/rxivist/blob/master/README.md) for running the spider without rebuilding the container every time your code changes:

```sh
git clone https://github.com/blekhmanlab/rxivist.git
cd rxivist/spider
docker run -it --rm --name rxspider -v "$(pwd)":/app --env RX_DBUSER --env RX_DBPASSWORD --env RX_DBHOST python:slim bash

# You will now be in a shell within the container:
cd /app
pip install -r requirements.txt
# Make whatever changes you want, then:
python spider.py
```
