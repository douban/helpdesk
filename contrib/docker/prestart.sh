#!/bin/bash

cd /app
if [ -f /app/secret/local_config.py ]; then
    cp /app/secret/local_config.py /app/local_config.py
fi
if [ -f /app/secret/bridge.py ]; then
    cp /app/secret/bridge.py /app/bridge.py
fi

# TODO: init database
# make database
