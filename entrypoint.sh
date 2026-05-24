#!/bin/bash

# Set default PORT if not provided
PORT=${PORT:-8000}

# Run gunicorn with the PORT variable
exec gunicorn the_pulse.wsgi:application --bind 0.0.0.0:$PORT
