# Stage 1: Build the React application
FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
ARG VITE_API_GATEWAY_URL=http://localhost:3100
ARG VITE_AUTH_ENDPOINT=
ARG VITE_DEV_AUTH_BYPASS=false
ENV VITE_API_GATEWAY_URL=$VITE_API_GATEWAY_URL
ENV VITE_AUTH_ENDPOINT=$VITE_AUTH_ENDPOINT
ENV VITE_DEV_AUTH_BYPASS=$VITE_DEV_AUTH_BYPASS
RUN npm run build

# Stage 2: Serve the application with NGINX (unprivileged — port 8080)
FROM nginxinc/nginx-unprivileged:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
