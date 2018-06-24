# rxivist API

## Endpoints 

## Running the server

### Using Docker

To start the necessary containers:

1. `git clone https://github.com/rabdill/rxivist.git`
1. `docker run -d --rm --name testdb -e POSTGRES_PASSWORD=mysecretpassword postgres` (This may already be running if you spun up the spider first.)
1. `cd rxivist/api`
1. `docker run -it --rm --name rxapi -p 8080:8080 -v "$(pwd)":/app --link testdb:postgres python bash /app/prep.sh`

Because the repository is bind-mounted to the container, editing the files locally using your editor of choice will result in the files also changing within the container. **Exiting the container's TTY will cause the container to stop,** and you will have to run step 4 again. If you're still inside the container, you can run `python main.py` as many times as you want.
