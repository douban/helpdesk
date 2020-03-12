#! /usr/bin/env sh
# originally copy from https://github.com/tiangolo/uvicorn-gunicorn-docker/blob/master/python3.7/

set -e
if [ $1 = 'nginx' ]; then
    exec nginx -g 'daemon off;'
else
    if [ -f /app/app/__init__.py ]; then
        DEFAULT_MODULE_NAME=app
    elif [ -f /app/app/main.py ]; then
        DEFAULT_MODULE_NAME=app.main
    elif [ -f /app/main.py ]; then
        DEFAULT_MODULE_NAME=main
    fi
    if [ -f /app/secret/local_config.py ]; then
        cp /app/secret/local_config.py /app/app/local_config.py
    fi
    if [ -f /app/secret/sa_tools_config.py ]; then
        mkdir -p /etc/sa-tools
        cp /app/secret/sa_tools_config.py /etc/sa-tools/config.py
    fi
    MODULE_NAME=${MODULE_NAME:-$DEFAULT_MODULE_NAME}
    VARIABLE_NAME=${VARIABLE_NAME:-app}
    export APP_MODULE=${APP_MODULE:-"$MODULE_NAME:$VARIABLE_NAME"}

    if [ -f /app/gunicorn_conf.py ]; then
        DEFAULT_GUNICORN_CONF=/app/gunicorn_conf.py
    elif [ -f /app/app/gunicorn_conf.py ]; then
        DEFAULT_GUNICORN_CONF=/app/app/gunicorn_conf.py
    else
        DEFAULT_GUNICORN_CONF=/gunicorn_conf.py
    fi
    export GUNICORN_CONF=${GUNICORN_CONF:-$DEFAULT_GUNICORN_CONF}

   # If there's a prestart.sh script in the /app directory, run it before starting
    PRE_START_PATH=/app/contrib/docker/prestart.sh
    echo "Checking for script in $PRE_START_PATH"
    if [ -f $PRE_START_PATH ] ; then
        echo "Running script $PRE_START_PATH"
        . "$PRE_START_PATH"
    else 
        echo "There is no script $PRE_START_PATH"
    fi

    # Start Gunicorn
    exec gunicorn -k uvicorn.workers.UvicornWorker -c "$GUNICORN_CONF" "$APP_MODULE"
fi