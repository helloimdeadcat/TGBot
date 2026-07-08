# Telegram-бот для поиска работы (Германия)

Бот ищет вакансии на **Arbeitsagentur** (Jobcenter), **Indeed.de** и **StepStone.de** по ключевым словам, отсеивает уже обработанные объявления и присылает дайджест в Telegram один раз в день.

## Возможности

- Поиск по ключевым словам и опциональной локации
- Дедупликация через SQLite
- Ежедневная рассылка в заданное время
- Команды `/start`, `/search`, `/status`
- Расширяемая архитектура scrapers для новых сайтов

## Быстрый старт

### 1. Создайте Telegram-бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot` и следуйте инструкциям
3. Скопируйте токен бота

### 2. Узнайте свой Chat ID

1. Напишите боту `/start`
2. Откройте в браузере:
   ```
   https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates
   ```
3. Найдите `"chat":{"id":123456789}` — это ваш `TELEGRAM_CHAT_ID`

### 3. Настройте окружение

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
TELEGRAM_BOT_TOKEN=ваш_токен
TELEGRAM_CHAT_ID=ваш_chat_id
SEARCH_KEYWORDS=python,developer,software
SEARCH_LOCATION=Berlin
DAILY_DIGEST_HOUR=9
DAILY_DIGEST_MINUTE=0
```

### 4. Установка и запуск (Windows)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 5. Запуск через Docker

```bash
docker compose up -d --build
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и текущие настройки |
| `/search` | Внеплановый поиск прямо сейчас |
| `/status` | Статистика базы и последней рассылки |

## Структура проекта

```
TGBot/
├── main.py                 # Точка входа
├── config.py               # Настройки из .env
├── scrapers/               # Источники вакансий
├── services/               # Оркестратор, фильтр, форматирование
├── storage/                # SQLite
├── bot/                    # Telegram handlers
└── scheduler/              # Ежедневная рассылка
```

## Добавление нового сайта

1. Создайте файл в `scrapers/`, унаследуйте `BaseScraper`
2. Реализуйте метод `search()`
3. Зарегистрируйте в `scrapers/registry.py`
4. Добавьте имя в `ENABLED_SOURCES` в `.env`

## Примечания

- **Arbeitsagentur** использует публичный REST API и работает наиболее стабильно
- **Indeed** и **StepStone** парсят HTML/JSON — при блокировке бот продолжит работу с остальными источниками
- ПК должен быть включён в момент рассылки (или используйте VPS + Docker)
