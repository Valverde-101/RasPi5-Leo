#!/bin/sh
set -e

if [ -e /dev/gpiochip0 ] && [ ! -e /dev/gpiochip4 ]; then
  ln -sf /dev/gpiochip0 /dev/gpiochip4
fi

if [ -e /dev/gpiomem0 ] && [ ! -e /dev/gpiomem4 ]; then
  ln -sf /dev/gpiomem0 /dev/gpiomem4
fi

exec uvicorn app:app --host 0.0.0.0 --port 8000
