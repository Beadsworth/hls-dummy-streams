#!/bin/bash

docker compose -p "hls_dummy_stream" -f docker-compose.yml up
docker compose -p "hls_dummy_stream" -f docker-compose.yml down --volumes
