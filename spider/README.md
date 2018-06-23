# rxivist spider

## Running the spider

### Using Docker

To start the necessary containers:

1. `git clone https://github.com/rabdill/rxivist.git`
1. `cd rxivist/spider`
1. `./launch_containers.sh`
1. (Within container) `python spider.py`

To interact with the database, open a new console window and run:

```sh
docker exec -it testdb psql testdb postgres
```

Because the repository is bind-mounted to the container, editing the files locally using your editor of choice will result in the files also changing within the container. **Exiting the container's TTY will cause the container to stop,** and you will have to run step 4 again. If you're still inside the container, you can run `python spider.py` as many times as you want. Run `./launch_containers.sh` again if you exit the Python container but want another one; it will use the existing DB container if it's running, or launch another of those as well.

### On a local machine

Running this setup locally might be a pain because the script requires a Postgres database to store its data. If you have one running locally or there's one accessible over a network/the internet, edit spider.py to point at its hostname or IP address rather than "testdb" and follow these instructions. If your Python environment isn't all messed up and you only have one version of Python, the commands to do this (`python` vs `python3`, `pip` vs `pip3`, etc.) may be a little different.

1. `git clone https://github.com/rabdill/rxivist.git`
1. `cd rxivist/spider`
1. `python3 -m venv .`
1. `source bin/activate`
1. `pip3 install -r requirements.txt`
1. `python3 spider.py`

When you're done, be sure to run `deactivate` to exit the virtual environment. Once the dependencies are installed with pip, you can skip most of these steps and just run `source bin/activate && python3 spider.py`

*pending: instructions to get Postgres running via Docker and running the script locally*
