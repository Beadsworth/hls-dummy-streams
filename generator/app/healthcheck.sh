#!/bin/sh
DIR="/hls/streams"
MAX_AGE=10
STATUS=0

# Find all m3u8 files
FILES=$(find "$DIR" -type f -name "*.m3u8")

if [ -z "$FILES" ]; then
    echo "No .m3u8 files found!"
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
