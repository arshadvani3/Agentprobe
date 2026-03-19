FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage — nginx to serve static files + proxy to backend
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Template config — API_BACKEND_URL is substituted at container startup
COPY nginx.conf.template /etc/nginx/templates/nginx.conf.template

EXPOSE 80

# envsubst replaces ${API_BACKEND_URL} only, leaving nginx vars ($host etc.) intact
CMD ["/bin/sh", "-c", \
  "envsubst '${API_BACKEND_URL}' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
