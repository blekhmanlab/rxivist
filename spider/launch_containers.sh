#!/bin/sh

docker run -d --rm --name testdb -e POSTGRES_PASSWORD=mysecretpassword postgres
docker run -it --rm --name pytest -v "$(pwd)":/app --link testdb:postgres python bash /app/prep.sh

#### What the Docker commands are doing
## Flags attached to the Postgres command:

# * `--name testdb` – The name of this container actually matters a little,
#        because its name will also be the DNS record other containers user
#        to connect to it.
# * `-e POSTGRES_PASSWORD=mysecretpassword` – Set an environment variable
#        called `POSTGRES_PASSWORD`
# * `-d` – Start the container in "detached mode": Don't give the user a
#        shell, and when the primary process exits, stop the container.
#####

## Flags for the Python command:

# * `-it` – Allocate a TTY for the container process that the user can get
#        to. (Technically two flags put together.)
# * `--rm` – Remove the container once it stops; don't leave a random
#        container called "pytest" lying around, because it will keep us from
#        spinning up a new one.
# * `-v "$(pwd)":/app` – Create a bind-mount to the container that connects
#        the directory we're currently in (`"$(pwd)"`) to a directory in the
#        container at `/app`.
# * `--link testdb:postgres` – Link this container to another container
#        called `testdb`. (In this case, the container we just started in the
#        previous step.) Enables the containers to see each other over a
#        network, and adds an entry for `testdb` to our Python container's
#        /etc/hosts file.
# * `python bash /app/prep.sh` – In this case `python` is the name of the
#        Docker image we want to spin up. `bash /app/prep.sh` is the command
#        we want to pass to the container once it's started. The "prep.sh"
#        script included in this repo just moves the user into the app
#        directory and installs the spider's dependencies. Its last action
#        is to start a shell for the user; otherwise, the primary process
#        exiting would cause the container to stop.
#####
