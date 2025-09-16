# Receipts Bot - Telegram Bot for Store Receipt Collection

Телеграм бот для сбора оплаченных чеков в сети магазинов с поддержкой узбекского и каракалпакского языков.

## Описание

Бот позволяет пользователям:
- Выбирать язык интерфейса (узбекский/каракалпакский)
- Регистрироваться через контакт
- Указывать Instagram аккаунт и подписываться на указанный профиль
- Выбирать филиал магазина
- Отправлять чеки (PDF, JPG, PNG) размером до 2MB
- Получать уведомления о статусе обработки чека

## Технологический стек

- **Backend**: Django 4.2.7
- **Bot Framework**: aiogram 3.3.0
- **Database**: SQLite (по умолчанию)
- **Language**: Python 3.8+
- **Process Manager**: PM2

## Требования к системе

- Python 3.8 или выше
- Node.js и npm (для PM2)
- 2GB RAM (минимум)
- 5GB свободного места на диске

## Пошаговое развертывание

### 1. Подготовка системы

#### Установка Python (если не установлен)
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# macOS (с Homebrew)
brew install python3

# CentOS/RHEL
sudo yum install python3 python3-pip
```

#### Установка Node.js и PM2
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS (с Homebrew)
brew install node

# CentOS/RHEL
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# Установка PM2 глобально
sudo npm install -g pm2
```

### 2. Клонирование и настройка проекта

```bash
# Клонирование репозитория (или распаковка архива)
git clone <repository_url> receipts_bot
cd receipts_bot

# Создание виртуального окружения
python3 -m venv venv

# Активация виртуального окружения
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\\Scripts\\activate

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Настройка окружения

```bash
# Копирование файла конфигурации
cp .env.example .env

# Редактирование конфигурации
nano .env
```

Заполните следующие переменные в файле `.env`:

```bash
BOT_TOKEN=your_telegram_bot_token_here
DJANGO_SECRET_KEY=your_django_secret_key_here
DEBUG=False
INSTAGRAM_PROFILE_URL=https://instagram.com/your_profile
ALLOWED_HOSTS=your_domain.com,localhost,127.0.0.1
```

#### Получение токена бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/botfather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте токен и вставьте в `.env` файл

#### Генерация Django Secret Key

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Настройка базы данных

```bash
# Создайте миграции и выполните их
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 5. Локальный запуск (для разработки)

```bash
# Запустите Django сервер
python manage.py runserver 0.0.0.0:8000

# В новом терминале запустите бота
python run_bot.py
```

### 6. Настройка PM2 (для продакшн)

```bash
# Редактирование конфигурации PM2
nano ecosystem.config.js
```

Обновите пути в файле `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [
    {
      name: 'receipts-bot',
      script: 'bot/main.py',
      interpreter: 'python3',
      cwd: '/полный/путь/к/receipts_bot',  // Замените на полный путь
      env: {
        PYTHONPATH: '/полный/путь/к/receipts_bot',  // Замените на полный путь
        DJANGO_SETTINGS_MODULE: 'receipts_project.settings'
      },
      // ... остальные настройки
    }
  ]
};
```

### 7. Запуск бота через PM2

```bash
# Запуск бота через PM2
pm2 start ecosystem.config.js

# Просмотр статуса
pm2 status

# Просмотр логов
pm2 logs receipts-bot

# Перезапуск бота
pm2 restart receipts-bot

# Остановка бота
pm2 stop receipts-bot
```

### 8. Автозапуск при загрузке системы

```bash
# Сохранение текущих процессов PM2
pm2 save

# Настройка автозапуска
pm2 startup

# Следуйте инструкциям, которые выведет PM2
```

### 9. Доступ к админ-панели Django

После локального запуска Django сервера:
1. Откройте браузер и перейдите по адресу: `http://localhost:8000/admin/`
2. Войдите используя созданные при `createsuperuser` учетные данные

**Важно**: Django сервер нужен для:
- Доступа к админ-панели
- Просмотра загруженных файлов чеков
- Управления пользователями и настройками

## Управление через Django админку

### Пользователи
- Просмотр всех зарегистрированных пользователей
- Фильтрация по языку, статусу подписки
- Поиск по Telegram ID, username, имени

### Филиалы
- Добавление новых филиалов
- Редактирование названий на двух языках
- Управление активностью филиалов

### Чеки
- Просмотр всех поданных чеков
- Одобрение/отклонение чеков
- Просмотр файлов чеков
- Фильтрация по статусу и филиалам

### Настройки бота
- Изменение ссылки на Instagram профиль

## Мониторинг

### PM2 команды

```bash
# Статус процессов
pm2 status

# Логи в реальном времени
pm2 logs receipts-bot --lines 50

# Мониторинг ресурсов
pm2 monit
```

## Обслуживание

```bash
# Обновление
pm2 stop receipts-bot
pip install -r requirements.txt
python manage.py migrate
pm2 start receipts-bot

# Резервное копирование
cp db.sqlite3 backups/db_$(date +%Y%m%d).sqlite3
```

## Решение проблем

### Основные команды

```bash
# Статус бота
pm2 status

# Логи
pm2 logs receipts-bot

# Перезапуск
pm2 restart receipts-bot

# Миграции
python manage.py migrate

# Проверка файлов
chmod -R 755 media/
```

## Продакшн настройки

### PostgreSQL
```bash
pip install psycopg2-binary
```

### Nginx
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location /media/ {
        alias /path/to/receipts_bot/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### SSL
```bash
sudo certbot --nginx -d your_domain.com
```