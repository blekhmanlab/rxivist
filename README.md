# rxivist

A tool for detailed searching of the biorxiv.org academic pre-print server. Indexes entries on the site and provides an interface for users to construct detailed queries for papers.

## Components

### Spider
A web scraper that crawls the bioRxiv site for data about paper submissions.

### API
A RESTful interface for requesting our interpreted results based on the data pulled by the spider.

### Frontend
A web application providing graphical access to the data provided by the API.