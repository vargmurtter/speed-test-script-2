# URL Download Speed Test

Консольный скрипт для измерения скорости скачивания. Он 10 раз последовательно
запрашивает один URL, полностью читает каждый ответ и выводит среднее время
запроса, суммарный объём данных и скорость.

## Требования

- Python 3
- Внешние зависимости не нужны — используется только стандартная библиотека

## Запуск

```bash
python3 speed_test.py "<URL>"
```

Пример:

```bash
python3 speed_test.py "https://images.wallpaperscraft.ru/image/single/olen_osen_les_1763874_3840x2160.jpg"
```

Скрипт можно запускать и напрямую:

```bash
./speed_test.py "<URL>"
```

Таймаут одной операции подключения/чтения задаётся параметром `--timeout`
(по умолчанию 60 секунд):

```bash
python3 speed_test.py "<URL>" --timeout 30
```

Справка:

```bash
python3 speed_test.py --help
```

## Результат

```text
[1/10] GET https://example.com/image.jpg
[1/10] HTTP 200 | 1.88 MiB (1,966,356 bytes) | 0.719 s | 21.87 Mbit/s
...
Summary
-------
Requests completed:    10
Average request time:  1.234 s
Total downloaded:      18.75 MiB (19,663,560 bytes)
Download speed:        12.75 Mbit/s
```

**Скорость измеряется в мегабитах в секунду (Mbit/s)**, а не в мегабайтах:
1 Мбит = 1 000 000 бит. Итоговая скорость рассчитывается как общий объём
скачанных данных в битах, делённый на суммарное время всех запросов. Объём
данных при этом отображается в MiB.
