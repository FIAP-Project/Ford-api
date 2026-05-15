FROM nginx:1.27-alpine

RUN apk add --no-cache openssl

WORKDIR /etc/nginx/certs
RUN openssl req -x509 -nodes -newkey rsa:2048 \
        -keyout server.key -out server.crt \
        -days 365 \
        -subj "/C=BR/ST=SP/L=SP/O=Ford-api/CN=localhost" \
    && chmod 600 server.key

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 8443
