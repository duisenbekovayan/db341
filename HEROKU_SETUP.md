# Heroku Deployment Setup Guide

## Проблема: Connection refused to localhost

Если вы видите ошибку подключения к localhost, это означает, что:
1. PostgreSQL аддон не добавлен на Heroku
2. Или DATABASE_URL не установлен

## Решение:

### Шаг 1: Добавить PostgreSQL аддон

```bash
heroku addons:create heroku-postgresql:mini
```

Или через веб-интерфейс Heroku:
1. Зайдите на https://dashboard.heroku.com
2. Выберите ваше приложение
3. Перейдите в раздел "Resources"
4. В поиске аддонов найдите "Heroku Postgres"
5. Добавьте план "Mini" (бесплатный)

### Шаг 2: Проверить DATABASE_URL

```bash
heroku config:get DATABASE_URL
```

Должен вернуть что-то вроде:
```
postgres://user:password@host:port/database
```

### Шаг 3: Настроить базу данных

После добавления PostgreSQL аддона, нужно создать таблицы:

```bash
# Вариант 1: Через heroku pg:psql
heroku pg:psql < schema.sql

# Вариант 2: Интерактивно
heroku pg:psql
# Затем скопируйте и вставьте содержимое schema.sql
```

Затем вставьте данные:

```bash
heroku pg:psql < insert_data.sql
```

### Шаг 4: Перезапустить приложение

```bash
heroku restart
```

### Шаг 5: Проверить логи

Если все еще есть проблемы, проверьте логи:

```bash
heroku logs --tail
```

## Альтернативный способ: Через веб-консоль Heroku

1. Зайдите на https://dashboard.heroku.com
2. Выберите ваше приложение
3. Перейдите в "More" → "Run console"
4. Выберите "bash"
5. Выполните:
   ```bash
   psql $DATABASE_URL -f schema.sql
   psql $DATABASE_URL -f insert_data.sql
   ```

## Проверка

После настройки проверьте:
1. `heroku config:get DATABASE_URL` - должен быть установлен
2. `heroku logs --tail` - не должно быть ошибок подключения
3. Откройте приложение в браузере - должно работать

