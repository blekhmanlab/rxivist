#!/bin/sh

docker run -it --rm --name rxspider -v "$(pwd)":/app spider:0.1
