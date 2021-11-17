FROM python:3.9
LABEL maintainer="sysadmin <sysadmin@douban.com>"

WORKDIR /app
COPY requirements.txt /app
RUN set -ex && apt-get update && \
    apt-get install -y --no-install-recommends default-libmysqlclient-dev git gcc && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# COPY codes
COPY ./ /app

ENV PYTHONPATH=/app

CMD ["/app/contrib/docker/start.sh"]
