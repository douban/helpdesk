#!/bin/bash

cd /app
if [ -f /app/secret/local_config.py ]; then
    cp /app/secret/local_config.py /app/local_config.py
fi
if [ -f /app/secret/sa_tools_config.py ]; then
    mkdir -p /etc/sa-tools
    cp /app/secret/sa_tools_config.py /etc/sa-tools/config.py
fi

# TODO: init database
# make database
