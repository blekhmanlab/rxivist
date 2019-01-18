FROM postgres:10
LABEL maintainer="Richard Abdill rxivist@umn.edu"

RUN apt-get update
RUN echo deb http://ftp.de.debian.org/debian testing main >> /etc/apt/sources.list
RUN echo 'APT::Default-Release "stable";' | tee -a /etc/apt/apt.conf.d/00local
RUN apt-get update
RUN apt-get -t testing install -y python3.6 python3-pip

# TODO: these env vars shouldn't be necessary
ENV LANGUAGE="C"
ENV LC_ALL="C"

ADD . /app
WORKDIR /app
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "/app/spider.py"]
