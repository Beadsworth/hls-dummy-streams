# -------- Stage 1: Generate HLS segments with FFmpeg --------
FROM jrottenberg/ffmpeg:4.4-alpine AS ffmpeg-builder

WORKDIR /video

RUN apk add --no-cache \
    curl \
    coreutils \
    ttf-dejavu \
    unzip

COPY ffmpeg/create-master-video.sh /usr/local/bin/create-master-video.sh
COPY ffmpeg/create-hls-playlist.sh /usr/local/bin/create-hls-playlist.sh

# Copy index files into the container
COPY stream-files/index.m3u8 /hls/streams-original/TEST_CHANNEL_A/index.m3u8
COPY stream-files/index.m3u8 /hls/streams-original/TEST_CHANNEL_B/index.m3u8

# Download the full Big Buck Bunny movie (4K 60fps)
ADD https://download.blender.org/demo/movies/BBB/bbb_sunflower_2160p_30fps_normal.mp4.zip video.mp4.zip

# Verify checksum for reproducibility
RUN echo "750b255c6d9fee1e2a03a6716d4f358bca56e9115bf3e06a66162fc5272ae151  video.mp4.zip" | sha256sum -c -

# create master video file and individual hls stream files
RUN create-master-video.sh
RUN create-hls-playlist.sh

# -------- Stage 2: Copy generated HLS to final image --------
FROM python:3.13-alpine3.21 AS hls-server

# Copy only the generated HLS files from ffmpeg builder
COPY --from=ffmpeg-builder /hls /hls

# Make output directories
RUN mkdir -p /hls/streams/TEST_CHANNEL_A && \
    mkdir -p /hls/streams/TEST_CHANNEL_B

# Set working directory inside container
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app /app

# Use unbuffered output so logs stream immediately
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=5s --retries=1 \
  CMD /app/healthcheck.sh

# Run fetch script
ENTRYPOINT ["python3", "start_hls_streams.py"]
