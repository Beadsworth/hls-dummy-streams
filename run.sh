#!/bin/bash

docker compose -p "hls_dummy_streams" -f docker-compose.yml up

# need to delete hls-files volume when done -- not doing so may affect builds
docker compose -p "hls_dummy_streams" -f docker-compose.yml down --volumes
