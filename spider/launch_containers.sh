#!/bin/sh

docker run -d --rm --name rxdb -e POSTGRES_PASSWORD=mysecretpassword postgres
docker run -it --rm --name rxspider -v "$(pwd)":/app --link rxdb:postgres python bash /app/prep.sh
