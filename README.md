# Receipts Bot - Telegram Bot for Store Receipt Collection

Телеграм бот для сбора оплаченных чеков в сети магазинов с поддержкой узбекского и каракалпакского языков.

## Пошаговое развертывание

### 1. Подготовка системы

#### Установка Python (если не установлен)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### Установка Node.js и PM2
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
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
source venv/bin/activate

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

### 4. Настройка базы данных

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 5. Локальный запуск (для разработки)

```bash
python manage.py runserver 0.0.0.0:8000
python run_bot.py
```

### 6. Настройка PM2 (для продакшн)

```bash
# Создайте файл конфигурации PM2
cp ecosystem.config.js.example ecosystem.config.js
```

```bash
# Редактирование конфигурации PM2
nano ecosystem.config.js
```

### 7. Запуск бота через PM2

```bash
# Запуск бота через PM2
pm2 start ecosystem.config.js

# Просмотр статуса
pm2 status

# Просмотр логов
pm2 logs all

# Перезапуск
pm2 restart all

# Остановка
pm2 stop all
```

### 8. Автозапуск при загрузке системы

```bash
# Сохранение текущих процессов PM2
pm2 save

# Настройка автозапуска
pm2 startup

# Следуйте инструкциям, которые выведет PM2
```