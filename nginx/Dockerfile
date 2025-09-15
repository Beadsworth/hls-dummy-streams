FROM nginx:stable-alpine

# Remove stock configs
RUN rm -rf /etc/nginx/conf.d/*

# copy in custom configs
COPY conf.d /etc/nginx/conf.d

# hls test pages
COPY test-pages /test-pages

HEALTHCHECK --interval=5m --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1
