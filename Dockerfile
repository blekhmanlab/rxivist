FROM python:slim
# NOTE: The python:alpine image would be lovely
# to use here, but it isn't compatible with the
# postgres SDK, per this issue:
# https://github.com/psycopg/psycopg2/issues/699

LABEL org.label-schema.schema-version = "1.0.0-rc.1"

LABEL org.label-schema.vendor = "Blekhman Lab"
LABEL org.label-schema.name = "Rxivist API"
LABEL org.label-schema.description = "The Rxivist API web application, a Python-based interface built using the Bottle framework."
LABEL org.label-schema.vcs-url = "https://github.com/blekhmanlab/rxivist"
LABEL org.label-schema.url = "https://rxivist.org"
LABEL maintainer="rxivist@umn.edu"

LABEL org.label-schema.version = "0.7.0"

COPY requirements.txt /
RUN pip install -r /requirements.txt

RUN apt-get update
RUN apt install -y curl

ADD . /app
WORKDIR /app

HEALTHCHECK --start-period=10s --interval=10s --timeout=10s CMD curl --fail http://localhost/v1/papers?page_size=3 || exit 1

CMD ["python", "main.py"]
