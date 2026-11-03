# =============================================================================
# JalSense: Production React Frontend Container Image
# Multi-stage Node 20 build + Nginx Alpine static server
# =============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application source & build production bundle
COPY . .
RUN npm run build

# Stage 2: Minimal Production Nginx Server
FROM nginx:alpine

# Copy compiled static assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy Nginx reverse proxy configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

# Health check probe
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
