#!/bin/sh
DIR="/hls/streams"
MAX_AGE=10
STATUS=0

# Find all variant playlists (.m3u8 but not master.m3u8)
FILES=$(find "$DIR" -type f -name "*.m3u8" ! -name "index.m3u8")

if [ -z "$FILES" ]; then
    echo "No variant .m3u8 files found!"
    exit 1
fi

NOW=$(date +%s)

for FILE in $FILES; do
    AGE=$(( NOW - $(stat -c %Y "$FILE") ))
    if [ "$AGE" -gt "$MAX_AGE" ]; then
        echo "FAIL: $FILE is stale ($AGE s old)"
        STATUS=1
    else
        echo "OK: $FILE is fresh ($AGE s old)"
    fi
done

exit $STATUS
