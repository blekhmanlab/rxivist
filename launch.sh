#!/bin/sh

# Launches individual containers in the rxivist platform.
# Usage:
#   `./launch.sh` with no parameters launches all containers in the platform.
#   `./launch.sh api` will launch only the API container.
#    `./launch.sh api foreground` will launch the API container and display the
#                                 active container process to the user.
#   Services that can be launched individually: `api`, `db`, `spider`

function launch_db {
  echo "Launching database..."
  if [[ $# -lt 1 || $1 != "foreground" ]]; then
    flag="-d"
  else
    flag="-it"
  fi
  docker run $flag --rm --name rxdb -e POSTGRES_PASSWORD=mysecretpassword postgres
}

function launch_server {
  echo "Launching API..."
  if [[ $# -lt 1 || $1 != "foreground" ]]; then
    docker run -d --rm --name rxapi -p 8080:8080 -v "$(pwd)/api":/app --link rxdb:postgres python bash /app/prep.sh
  else
    docker run -it --rm --name rxapi -p 8080:8080 -v "$(pwd)/api":/app --link rxdb:postgres python bash /app/prep.sh
  fi
}

function launch_spider {
  echo "Launching spider..."
  if [[ $# -lt 1 || $1 != "foreground" ]]; then
    docker run -d --rm --name rxspider -v "$(pwd)/spider":/app --link rxdb:postgres python bash /app/prep.sh
  else
    docker run -it --rm --name rxspider -v "$(pwd)/spider":/app --link rxdb:postgres python bash /app/prep.sh
  fi
}

# Default is to launch everything,
# and show the output of the spider
if [[ $# -lt 1 ]]; then
  echo "\n\nrxivist: Launching DB, spider and API. Dropping user into spider container."
  launch_db
  launch_server
  launch_spider foreground
fi

case "$1" in
  spider)
    launch_spider $2
    ;;
  api)
    launch_api $2
    ;;
  db)
    launch_db $2
    ;;
  help)
    echo "\nYou have four primary options. No parameters launches all containers.
The first parameter can either be 'api', 'db' or 'spider', depending on
which service you want to start. Adding 'foreground' as a second
parameter will drop you into the specified container.\n"
    ;;
  *)
    echo "Unrecognized option. Run './launch.sh help' for details."
esac