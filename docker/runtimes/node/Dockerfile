FROM node:20-alpine

ENV NODE_ENV=production

RUN adduser -D -u 1000 sandbox && \
    mkdir -p /runner /workspace /tmp && \
    chown -R sandbox:sandbox /runner /workspace /tmp

COPY runner.js /runner/runner.js

USER sandbox
WORKDIR /workspace

ENTRYPOINT ["node", "/runner/runner.js"] 