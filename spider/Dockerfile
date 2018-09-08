FROM postgres:10
MAINTAINER Richard Abdill

RUN apt-get update
RUN apt-get install -y python3 python3-pip

ENTRYPOINT ["bash", "/app/prep.sh"]
