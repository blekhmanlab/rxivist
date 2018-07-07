# rxivist

A tool for detailed searching of the biorxiv.org academic pre-print server. Indexes entries on the site and provides an interface for users to construct detailed queries for papers.

## Components

### Spider
A web scraper that crawls the bioRxiv site for data about paper submissions.

### API
A RESTful interface for requesting our interpreted results based on the data pulled by the spider.

### Frontend
A web application providing graphical access to the data provided by the API. Currently, this is combined with the API and all pages are rendered server-side.

## Development
### Launching the platform locally

Docker is essentially a requirement for deploying this locally. It's certainly possible to run these scripts without it, but it will be a chore.

If you have [Docker](https://www.docker.com/community-edition) installed locally, the included script (`launch.sh`) should take care of the commands required to get everything running. If you want to run any of the components individually, passing parameters to the launch script should get the job done. Examples:

```sh
# Launch the database, spider and API:
./launch.sh

# get help:
./launch.sh help

# spin up just the database container:
./launch db

# spin up just the database container, and display the process in the console:
./launch db foreground
```

### Viewing database information

The API currently provides endpoints for viewing the contents of the database tables. Once the server starts up, navigate to `http://localhost:8123/db` will show you the available tables.