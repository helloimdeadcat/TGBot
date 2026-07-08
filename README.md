# Telegram-бот для поиска работы (Германия)

Бот ищет вакансии на **Arbeitsagentur** (Jobcenter), **Indeed.de** и **StepStone.de** по ключевым словам, отсеивает уже обработанные объявления и присылает дайджест в Telegram один раз в день.

## Возможности

- Поиск по ключевым словам и опциональной локации
- Дедупликация через SQLite
- Ежедневная рассылка в заданное время
- **Бесплатный хостинг через GitHub Actions** (без сервера)
- Команды `/start`, `/search`, `/status` (только при локальном запуске `main.py`)
- Расширяемая архитектура scrapers для новых сайтов

## Бесплатный запуск через GitHub Actions (рекомендуется)

Не нужен сервер, карта или включённый ПК. GitHub раз в день запускает поиск и шлёт результат в Telegram.

### 1. Создайте Telegram-бота

1. Откройте [@BotFather](https://t.me/BotFather)
2. `/newbot` → скопируйте токен

### 2. Узнайте Chat ID

1. Напишите боту любое сообщение
2. Откройте: `https://api.telegram.org/bot<ТОКЕН>/getUpdates`
3. Найдите `"chat":{"id":123456789}`

### 3. Загрузите код на GitHub

```bash
git add .
git commit -m "Add GitHub Actions daily digest"
git push -u origin main
```

### 4. Настройте секреты и переменные

В репозитории: **Settings → Secrets and variables → Actions**

**Secrets** (обязательные):

| Имя | Значение |
|-----|----------|
| `TELEGRAM_BOT_TOKEN` | токен от BotFather |
| `TELEGRAM_CHAT_ID` | ваш chat id |

**Variables** (вкладка Variables, опционально):

| Имя | Пример |
|-----|--------|
| `SEARCH_KEYWORDS` | `python,developer,software` |
| `SEARCH_LOCATION` | `Berlin` |
| `ENABLED_SOURCES` | `arbeitsagentur,indeed,stepstone` |

Если Variables не заданы, используются значения по умолчанию из `config.py`.

### 5. Запустите вручную для проверки

**Actions → Daily Job Digest → Run workflow**

Через 1–2 минуты в Telegram должен прийти дайджест.

### 6. Расписание

По умолчанию: **каждый день в 07:00 UTC** (≈ 09:00 Berlin летом).

Изменить время: отредактируйте `cron` в [`.github/workflows/daily.yml`](.github/workflows/daily.yml).  
[Cron calculator](https://crontab.guru/) — время указывается в **UTC**.

### Как хранятся обработанные вакансии

SQLite-база кэшируется между запусками через GitHub Actions Cache — дубликаты не приходят повторно.

### Ограничения GitHub Actions

- Нет команд `/search` и `/status` в Telegram (бот не работает постоянно)
- Рассылка только по расписанию (+ ручной запуск в Actions)
- Для интерактивного бота запускайте `python main.py` локально

---

## Локальный запуск (с командами /search)

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
- **GitHub Actions** — бесплатно для личного репозитория
- Локальный `main.py` нужен только если хотите команды `/search` в Telegram
