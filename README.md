# rxivist API

The Rxivist project is spread out over three code repositories:

* This one contains code for [the API](https://rxivist.org/docs), which provides programmatic access to the data in the Rxivist database.
* The [Rxivist web application](https://rxivist.org), which consumes data from the API, is stored in the [rxivist_web](https://github.com/blekhmanlab/rxivist_web) project.
* The web crawler that indexes bioRxiv and medRxiv preprints is stored in the [biorxiv_spider](https://github.com/blekhmanlab/biorxiv_spider) project.

## Deployment
The Rxivist API is designed to be run in a Docker container (though it doesn't have to be). Once Docker is installed on whatever server you plan to use, there are only a few commands to run:

```sh
docker swarm init
docker build . -t rxivist:latest
docker service create --name rxivist_service --replicas 3 --publish published=80,target=80 --env RX_DBUSER --env RX_DBPASSWORD --env RX_DBHOST rxivist:latest
```

NOTE: This assumes that the necessary environment variables are set on the host machine. If they aren't, you should **set them in the `docker service create` command**: For example, rather than including the flag `--env RX_DBUSER`, you would replace it with something like `--env RX_DBUSER=root` The required variables are:

* `RX_DBHOST`: The location of your database server, as it should be passed to Postgres. For example, `rxivistdev.12345.us-east-1.rds.amazonaws.com`
* `RX_DBUSER`: The username with which the database client should connect to the Rxivist database.
* `RX_DBPASSWORD`: That user's password.

Running the commands above builds a new image based on the current code on the repository, and deploys three containers to which all requests are load balanced. If one becomes unhealthy, it's removed and replaced with a fresh container. If you want your server to listen on a different port than 80, you can change the value of the "published" option to whatever you'd like—however, changing the "target" option will break the default settings of the app. The API listens on port 80 *inside the container*, but you can map that port to whatever host port you wish.

**Note:** You'll want to **modify the `config.py` file** *before* you run `docker build`, not after. This file contains several settings regarding the API's server and basic behavior. For now, the configuration is copied into the container at build time. This may change one day and be much nicer.

## Development

### Using Docker

For local development, you don't need to rebuild a container image every time you want to test a change: Mounting the repository to the container will allow you to test changes as you make them.

```sh
git clone https://github.com/blekhmanlab/rxivist.git
cd rxivist
docker run -it --rm --name rxapi -p 80:80 -v "$(pwd)":/app --env RX_DBUSER --env RX_DBPASSWORD --env RX_DBHOST python:3 bash

# You will now be in a shell within the container:
cd /app
pip install -r requirements.txt
python main.py
```

*Note:* To run the container in the background, replace the `-it` flags in the docker command above with `-d`.

Because the repository is bind-mounted to the container, editing the files locally using your editor of choice will result in the files also changing within the container. If you change the `use_prod_webserver` value in `config.py` to `False`, the server will reload the applications whenever a code modification is detected. (Note that the application **will exit if it encounters an uncaught exception**, and you'll have to start the application again by hand.)
