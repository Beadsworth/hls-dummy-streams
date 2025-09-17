FROM nginx:stable-alpine

# Remove stock configs
RUN rm -rf /etc/nginx/conf.d/*

# copy in custom configs
COPY conf.d /etc/nginx/conf.d

# hls test pages
COPY test-pages /test-pages

HEALTHCHECK --interval=30s --timeout=5s --retries=1 \
  CMD curl -f http://localhost:8000/health || exit 1
