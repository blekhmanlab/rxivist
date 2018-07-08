# rxivist spider

## Running the spider for real
The web crawler is designed to be run from local machines that connect remotely to the Rxivist database. Doing this is not as bad as it sounds:

1. `git clone https://github.com/rabdill/rxivist.git`
1. `cd rxivist/spider`
1. Put accurate database credentials into `config.py`
1. `docker run -it --rm --name rxspider -v "$(pwd)":/app python bash /app/prep.sh`

## Development
### Using Docker

For local development, the spider can also be run locally, against a fake Postgres database deployed in a fresh container. A helper script takes care of the details:

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

### On a local machine

Running this setup locally might be a pain because the script requires a Postgres database to store its data. If you have one running locally or there's one accessible over a network/the internet, edit `config.py` to point at its hostname or IP address rather than "rxdb" and follow these instructions. If your Python environment isn't all messed up and you only have one version of Python, the commands to do this (`python` vs `python3`, `pip` vs `pip3`, etc.) may be a little different.

1. `git clone https://github.com/rabdill/rxivist.git`
1. `cd rxivist/spider`
1. `python3 -m venv .`
1. `source bin/activate`
1. `pip3 install -r requirements.txt`
1. `python3 spider.py`

When you're done, be sure to run `deactivate` to exit the virtual environment. Once the dependencies are installed with pip, you can skip most of these steps and just run `source bin/activate && python3 spider.py`
