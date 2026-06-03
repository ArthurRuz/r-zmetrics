# R&Z Metrics
___
## Агрегатор футбольных событий

Этот проект представляет собой веб-приложение, позволяющее следить за футбольными событиями, 
положением лиг, командами и игроками. Состоит из backend (python, django) и frontend (html, css, js) частей.


## Установка
1.  Клонируйте репозиторий:
    ```bash
    git clone https://github.com/ArthurRuz/r-zmetrics.git
    cd rzmetrics
    ```
2.  Создайте и активируйте виртуальное окружение:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3.  Установите необходимые библиотеки:
    ```bash
    pip install -r requirements.txt
    ```
    
4. Настройте .env файл по шаблону из .env.example:
    ```bash
    SECRET_KEY=your_django_secret_key
    FOOTBALL_DATA_TOKEN=your_fd_token
    THESPORTSDB_TOKEN=your_sd_token
    API_FOOTBALL_TOKEN=your_af_token
    ```
   
5. Скачайте готовую БД со [ссылке](https://disk.yandex.ru/d/hysnOPjGtwh4cw) и поместите в корень проекта.
6. По той же [ссылке](https://disk.yandex.ru/d/hysnOPjGtwh4cw) вы можете скачать статику 
(логотипы команд, фото игроков, логитипы лиг). Вставьте в папку `football/static/football`


## Использование
#### Для запуска сервера введите команду в терминал
```
python manage.py runserver
```

## Структура проекта

Проект состоит из 3 приложений:
1. football: основная часть проекта, реализующая функции визуализации данных.
2. users: отвечает за регистрацию, авторизацию и управление пользователями.
3. integrations: выполняет сбор данных из различных источников.

## Лицензия
Этот проект распространяется под лицензией MIT.