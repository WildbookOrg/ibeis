#!/bin/bash

set -ex

mkdir -p /data/db

chown wbia:wbia /data

chown wbia:wbia /data/db

chmod 755 /data

chmod 755 /data/db

# Executes as `wbia` with PID 1
exec gosu wbia:wbia $@
