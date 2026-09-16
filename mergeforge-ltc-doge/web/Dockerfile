FROM python:3.12-alpine@sha256:1887c114801a8c82a4ec01daa52cfe7fc3f63573640e2247320289807ac1c3bb
WORKDIR /app
COPY server.py /app/server.py
COPY node-status.py /app/node-status.py
COPY init-config.py /app/init-config.py
COPY index.html /app/index.html
COPY icon.svg /app/icon.svg
COPY support /app/support
RUN adduser -D -u 1000 mergeforge && mkdir -p /data && chown -R mergeforge:mergeforge /data /app
USER mergeforge
EXPOSE 8096
CMD ["python", "/app/server.py"]
