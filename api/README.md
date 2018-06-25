# rxivist API

## Endpoints

* `/db`: An admin endpoint that displays the tables currently stored in the rxivist database.
* `/db/$table_name`: Displays the contents of the `$table_name` table in the database.
* `/hello` The "hello world" endpoint. Should respond `200 Hello World!` if the server isn't totally messed up.

## Running the server

### Using Docker

To start the necessary containers:

1. 1. Start the database: `docker run -d --rm --name rxdb -e POSTGRES_PASSWORD=mysecretpassword postgres` (This may already be running if you spun up the spider first.)
1. `git clone https://github.com/rabdill/rxivist.git`
1. `cd rxivist/api`
1. `docker run -it --rm --name rxapi -p 8123:8080 -v "$(pwd)":/app --link rxdb:postgres python bash /app/prep.sh`

*Note:* To run the container in the background, replace the `-it` flags in the docker command above with `-d`.

Because the repository is bind-mounted to the container, editing the files locally using your editor of choice will result in the files also changing within the container. The server reloads the applications whenever a modification is detected, but **will exit if it encounters an uncaught exception**. At that point, you should land in a shell; running `python main.py` again should start up the server again.

**Exiting the container's TTY will cause the container to stop,** and you will have to run step 4 again.
