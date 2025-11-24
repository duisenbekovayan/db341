# Heroku Deployment Setup Guide

## Проблема: Connection refused to localhost

Если вы видите ошибку подключения к localhost, это означает, что:
1. PostgreSQL аддон не добавлен на Heroku
2. Или DATABASE_URL не установлен

## Решение (БЕЗ Heroku CLI - через веб-интерфейс):

### Шаг 1: Добавить PostgreSQL аддон через веб-интерфейс

1. Зайдите на https://dashboard.heroku.com
2. Войдите в свой аккаунт
3. Выберите ваше приложение
4. Перейдите в раздел **"Resources"** (вкладка вверху)
5. В поле "Add-ons" введите: `Heroku Postgres`
6. Нажмите на результат поиска
7. Выберите план **"Mini"** (бесплатный) или **"Essential"**
8. Нажмите **"Submit Order Form"**

После этого Heroku автоматически:
- Добавит PostgreSQL базу данных
- Установит переменную окружения `DATABASE_URL`
- Перезапустит приложение

### Шаг 2: Настроить базу данных через веб-консоль

**ПРАВИЛЬНЫЙ СПОСОБ:**

1. На странице вашего приложения на Heroku
2. Нажмите на кнопку **"More"** (справа вверху) → **"Run console"**
3. Выберите **"bash"**
4. В открывшейся консоли выполните:

```bash
# Сначала проверим, что DATABASE_URL установлен
echo $DATABASE_URL
```

5. **Подключитесь к базе данных:**
   ```bash
   psql "$DATABASE_URL"
   ```
   
   **ВАЖНО:** Используйте кавычки вокруг `$DATABASE_URL` и пробел между `psql` и `"$DATABASE_URL"`

6. После подключения вы увидите приглашение типа: `d1uniqip40coai=>`

7. **Теперь откройте файл `schema.sql` на вашем компьютере**, скопируйте ВСЁ его содержимое и вставьте в консоль Heroku

8. После выполнения всех команд из schema.sql, выйдите:
   ```bash
   \q
   ```

9. **Повторите для данных:**
   ```bash
   psql "$DATABASE_URL"
   ```
   
10. Откройте файл `insert_data.sql` на вашем компьютере, скопируйте ВСЁ его содержимое и вставьте в консоль

11. После выполнения выйдите:
    ```bash
    \q
    ```

**ЧАСТЫЕ ОШИБКИ:**

❌ **Неправильно:** `psql $DATABASE_URL` (без кавычек может не работать)
✅ **Правильно:** `psql "$DATABASE_URL"`

❌ **Неправильно:** `psql$DATABASE_URL` (нет пробела)
✅ **Правильно:** `psql "$DATABASE_URL"` (есть пробел)

❌ **Неправильно:** `psql $DATABASE_URL -f schema.sql` (файлы недоступны в консоли)
✅ **Правильно:** Скопировать содержимое файла и вставить в psql

**Альтернативный способ (если psql не работает):**

Можно использовать Python скрипт прямо в консоли:

```bash
# В консоли Heroku выполните:
python3
```

Затем в Python:
```python
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)

# Откройте schema.sql на компьютере, скопируйте содержимое
# и выполните:
with open('schema.sql', 'r') as f:
    schema = f.read()

# Но файлы недоступны, поэтому лучше использовать psql
```

## Решение (С Heroku CLI):

Если хотите установить Heroku CLI:

### Установка Heroku CLI:

**Linux:**
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

**Или через snap:**
```bash
sudo snap install heroku --classic
```

**Или через пакетный менеджер:**
```bash
# Ubuntu/Debian
sudo apt-get install heroku

# Или скачайте с https://devcenter.heroku.com/articles/heroku-cli
```

После установки:
```bash
heroku login
heroku addons:create heroku-postgresql:mini
```

### Шаг 3: Проверить, что все работает

1. Откройте ваше приложение в браузере (ссылка вида: `https://your-app-name.herokuapp.com`)
2. Проверьте, что нет ошибок подключения к базе данных
3. Попробуйте создать пользователя или просмотреть список пользователей

### Шаг 4: Проверить логи (если есть проблемы)

1. На странице приложения на Heroku
2. Перейдите в раздел **"More"** → **"View logs"**
3. Ищите ошибки подключения к базе данных

## Проверка через веб-интерфейс:

1. На странице приложения → **"Settings"**
2. Прокрутите до **"Config Vars"**
3. Должна быть переменная **`DATABASE_URL`** со значением типа `postgres://...`

## Если все еще не работает:

1. Убедитесь, что PostgreSQL аддон добавлен (Resources → должен быть "Heroku Postgres")
2. Убедитесь, что таблицы созданы (попробуйте открыть Users в приложении)
3. Проверьте логи на наличие ошибок
4. Убедитесь, что последний код задеплоен (Settings → увидите последний commit)

