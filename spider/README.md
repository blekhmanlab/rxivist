# rxivist spider

## Running the spider for real
The web crawler runs in a lightly customized Docker container and can be launched from any server (or workstation) that has access to the database.

```sh
git clone https://github.com/rabdill/rxivist.git
cd rxivist/spider
docker build . -t rxspider:latest
docker run -it --rm --name rxspider -v "$(pwd)":/app --env RX_DBPASSWORD --env RX_DBHOST  rxspider:latest
```

NOTE: The spider is **configured to use the `root` user by default**—you can change this in `config.py`.
