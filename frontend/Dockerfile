# Frontend Dockerfile for Google Cloud Run
# Multi-stage build: Node for building, Nginx for serving

# ============================================
# Stage 1: Build the React application
# ============================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Environment variables for the build (set via --set-build-env-vars)
# These are read by Vite during build
ARG VITE_API_URL
ARG VITE_MAPBOX_ACCESS_TOKEN
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_MAPBOX_ACCESS_TOKEN=${VITE_MAPBOX_ACCESS_TOKEN}

# Build the production bundle
RUN echo "Building with API URL: $VITE_API_URL" && npm run build

# ============================================
# Stage 2: Serve with Nginx
# ============================================
FROM nginx:alpine

# Copy the built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Cloud Run uses PORT environment variable (default 8080)
EXPOSE 8080

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
