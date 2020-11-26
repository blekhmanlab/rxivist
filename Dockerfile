FROM python:3
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

LABEL org.label-schema.version = "1.1.0"

ADD . /app
WORKDIR /app
RUN pip install -r requirements.txt

HEALTHCHECK --start-period=30s --interval=120s --timeout=15s CMD curl --fail http://localhost/v1/papers?page_size=3 || exit 1

CMD ["python", "main.py"]
