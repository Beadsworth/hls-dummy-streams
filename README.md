# HLS Dummy Stream Generator

Need an HLS live-stream for testing?  This project allows you to run an HLS live-stream server locally without `ffmpeg` (which should save you some CPU cycles).


## Features

Key features of this project:
- generate two distinct, clearly labelled HLS live-stream channels
- low resource cost to run (compared to `ffmpeg` running continuously in `-hls` mode)
- premade docker images hosted on `dockerhub` -- just run the docke-compose file!
- `nginx` server hosting hls live-stream
- static html test page to confirm all streams are running

Upcoming features wishlist:
- multiple resolutions supported
- better docke security
- statically host [hls.js demo page](https://hlsjs.video-dev.org/demo/) (it's a very good page!)


## Before you use this project...

...are you sure you need two distinct test channels that run on local hardware?  You might just need one of these publically-available, web-hosted hls streams:
- https://test-streams.mux.dev/


More resources here:
- https://hlsjs.video-dev.org/demo/


# Running and Testing

Run the server with:
```
./run.sh
```

Confirm the server is up and running:
```
curl localhost:8000/health
```

Streams are hosted at:
- http://localhost:8081/streams/TEST_CHANNEL_A/360p.m3u8
- http://localhost:8081/streams/TEST_CHANNEL_B/360p.m3u8

Access the test page to confirm the hls live-streams are running:

http://localhost:8000/test-pages/test-all-streams.html


## Implementation Details and Notes

How it works:
- `hls-dummy-streams-generator` has pre-cut hls segments saved on the image and cycles through them, bypassing any streaming with `ffmpeg`
  - segment length: 6 seconds
  - playlist size: 6 segments
  - makes use of `#EXT-X-DISCONTINUITY` tag
- stream is in `/hls` directory `hls-dummy-streams-generator`
  - `/hls/streams-original` has original hls segments
  - `/hls/streams/` simply links/unlinks corresponding files in `/hls/streams-original`
  - `hls-dummy-streams-nginx` must share the entire `/hls` volume for linking to work correctly
- `hls-dummy-streams-nginx` simply serves static content

Other notes:
- 24 fps only
- slight drift (~1.001 measured by hls.js) created from discontinuities
- this is not `LL-HLS`
