# rxivist spider

## Running the spider for real
The web crawler is designed to be run from local machines that connect remotely to the Rxivist database. It now runs in a lightly customized Docker container.

1. `git clone https://github.com/rabdill/rxivist.git`
1. `cd rxivist/spider`
1. `docker build . -t rxspider:0.1.0` (Replace the "0.1.0" with whatever tag you want to use for this particular version that you're building.)
1. Put accurate database credentials into `config.py`
1. `docker run -it --rm --name rxspider -v "$(pwd)":/app rxspider:0.1.0`

## Development
### Using Docker

**Note: This section has changed significantly; the local database no longer works as described, but this will be updated soon.**

For local development, the spider can also be run against a fake Postgres database deployed in a fresh container. A helper script takes care of the details:

1. `git clone https://github.com/rabdill/rxivist.git`
1. `cd rxivist/spider`
1. `./launch_containers.sh` (This will drop you into the spider container.)

The spider application will run automatically when the container starts. When it finishes, you will be in a TTY session within the container. You can start the process again by running `python spider.py`.

To interact with the database, open a new console window and run (outside of any containers):

```sh
docker exec -it rxdb psql rxdb postgres
```

Because the repository is bind-mounted to the container, editing the spider's Python source locally using your editor of choice will result in the files also changing within the container. **Exiting the container's TTY will cause the container to stop,** and you will have to run the `launch_containers` script again. If you're still inside the container, you can run `python spider.py` as many times as you want. Run `./launch_containers.sh` again if you exit the Python container but want another one; it will use the existing DB container if it's running, or launch another of those as well.

If you want to start over with a fresh database, the simplest way to do it is to re-launch both containers. To do this:

```sh
docker kill rxdb
docker kill rxspider
./launch_containers.sh
```
