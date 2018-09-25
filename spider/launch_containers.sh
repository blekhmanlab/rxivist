#!/bin/sh

docker run -it --rm --name rxspider -v "$(pwd)":/app --env RX_DBPASSWORD --env RX_DBHOST rxspider:0.4
