#!/bin/bash

if [ "$1" = 'serve' ]; then
    exec gunicorn --bind 0.0.0.0:8080 app:app --timeout 3000
fi

exec "$@"

