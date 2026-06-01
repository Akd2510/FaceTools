FROM nginx:alpine

# Remove the default configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom configuration directly into the image
COPY nginx.conf /etc/nginx/nginx.conf

# The image will now always use this config without needing a local mount
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
