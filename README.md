# Запуск через докер
В файле .env необходимо указать значение переменных

Для работы необходим docker-compose.override.yml. Пример файла с необходимыми переменными

services:

  postgresql:
    build:
      args:
        POSTGRESQL_PASSWORD: 23456
    restart: 'no'
    ports:
      - "54321:5432/tcp"
  backend:
    environment:
      DATABASE_URL: 'postgresql+asyncpg://postgres:23456@postgresql:5432/postgres'

  celery_worker:
    environment:
      DATABASE_URL: 'postgresql+asyncpg://postgres:23456@postgresql:5432/postgres'
      REDIS_URL: "redis://redis:6379/0"
      OPENAI_API_KEY: "OPENAI_API_KEY"
      SOCKS5_URL: "SOCKS5_URL"

DATABASE_URL - адрес бд
REDIS_URL - адрес редис
OPENAI_API_KEY - апи кей с https://platform.openai.com/api-keys
SOCKS5_URL - адрес SOCKS5-прокси-сервера для работы запросов из России, в случае если сервер не в России оставить пустым  
для доступа изнутри контейнера локальную машину необходимо обозначить как 172.17.0.1
пример адреса "socks5://172.17.0.1:5000"


```console
$ docker compose build
```

После этого можно запускать проект
```console
$ docker compose up
```
Запрос по ссылке
"http://localhost:8000/process_sales"
