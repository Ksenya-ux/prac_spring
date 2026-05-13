# MUD

Пакет содержит клиент и сервер для MUD.

## Установка

```bash
pip install .
```

## Запуск

```bash
mood-server
mood-client username
```

В клиенте доступна команда `documentation`, открывающая установленную HTML-документацию через `webbrowser.open()`.

## Разработка

```bash
pip install -r requirements-dev.txt
doit html
doit test
```
