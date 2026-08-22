# Stage 1: Build the React application
FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
ARG VITE_API_GATEWAY_URL=http://localhost:3100
ENV VITE_API_GATEWAY_URL=$VITE_API_GATEWAY_URL
RUN npm run build

# Stage 2: Serve the application with NGINX
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
