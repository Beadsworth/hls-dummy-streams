#!/bin/sh
set -eu

MASTER="video_4k.mp4"
HLS_DIR="/hls/streams-original"
FONT="/usr/share/fonts/ttf-dejavu/DejaVuSans-Bold.ttf"
HLS_OPTS="-c:a aac -f hls -hls_time 6 -hls_list_size 0 -hls_flags +program_date_time -g 144 -keyint_min 144 -sc_threshold 0"

# Generate 360p HLS streams from 4K master
ffmpeg -i "$MASTER" -filter_complex "
  [0:v]split=2[va][vb];

  [va]scale=640:360,drawtext=fontfile=$FONT:text='TEST_CHANNEL_A 360p':fontcolor=white:fontsize=40:borderw=3:bordercolor=black:x=(w-text_w)/2:y=(h-text_h)/2[va_out];

  [vb]scale=640:360,negate,drawtext=fontfile=$FONT:text='TEST_CHANNEL_B 360p':fontcolor=white:fontsize=40:borderw=3:bordercolor=black:x=(w-text_w)/2:y=(h-text_h)/2[vb_out]
" \
  -map "[va_out]" -map 0:a $HLS_OPTS \
  -hls_segment_filename "$HLS_DIR/TEST_CHANNEL_A/360p_%04d.ts" \
  "$HLS_DIR/TEST_CHANNEL_A/360p.m3u8" \
  -map "[vb_out]" -map 0:a $HLS_OPTS \
  -hls_segment_filename "$HLS_DIR/TEST_CHANNEL_B/360p_%04d.ts" \
  "$HLS_DIR/TEST_CHANNEL_B/360p.m3u8"
