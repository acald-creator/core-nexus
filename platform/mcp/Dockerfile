FROM cgr.dev/chainguard/node:latest AS builder
USER root
WORKDIR /app
COPY package.json ./
RUN npm install
COPY tsconfig.json ./
COPY src/ src/
RUN npm run build

FROM cgr.dev/chainguard/node:latest
WORKDIR /app
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/build ./build
ENV NODE_ENV=production
EXPOSE 3001
CMD ["build/index.js"]
