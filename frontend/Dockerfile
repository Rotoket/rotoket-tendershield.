FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Простой nginx-контейнер для статики
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
# Конфиг nginx для фронтенда и прокси на backend добавим в папке infra
COPY infra/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]


