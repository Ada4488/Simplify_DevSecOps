# Stage 1: Build the React application
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
# Install dependencies using npm ci for reliable builds from package-lock.json
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve the application using Nginx
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# Copy a default nginx config if needed, or rely on the base image's default
# EXPOSE 80 # Already exposed by base Nginx image
CMD ["nginx", "-g", "daemon off;"]
