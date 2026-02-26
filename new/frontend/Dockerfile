FROM node:20-alpine AS build
WORKDIR /app
# Build context is new/ (parent of frontend/) so we can reach docs/
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
# Copy static docs into public/ so Vite includes them in the build output
COPY docs/ ./public/docs/
ARG VITE_API_URL=http://localhost:8001
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# SPA routing: serve static files directly; fall back to index.html for app routes
RUN printf 'server {\n  listen 80;\n  root /usr/share/nginx/html;\n  index index.html;\n  location /docs/ { try_files $uri $uri/ =404; }\n  location / { try_files $uri $uri/ /index.html; }\n}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
