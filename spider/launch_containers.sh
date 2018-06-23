#!/bin/sh

docker run -d --rm --name testdb -e POSTGRES_PASSWORD=mysecretpassword postgres
docker run -it --rm --name pytest -v "$(pwd)":/app --link testdb:postgres python bash /app/prep.sh
