FROM postgres:10-alpine
LABEL maintainer="Richard Abdill rxivist@umn.edu"

WORKDIR /app
ADD rxivist.backup .
ADD load.sh /docker-entrypoint-initdb.d/init-load-rxivist.sh
