FROM denoland/deno:alpine

ENV DIR=./app/

WORKDIR /app

# Copy manifests first so the dependency install layer caches across
# source-only edits
COPY ${DIR}/deno.json ${DIR}/deno.lock ${DIR}/package.json* ./
RUN deno ci --prod --skip-types

# Then copy the rest of the source
COPY ${DIR} .

CMD ["deno", "run", "--allow-net", "main.ts"]
