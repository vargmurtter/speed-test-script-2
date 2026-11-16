#!/usr/bin/env python3
"""Измеряет скорость скачивания, последовательно запрашивая один URL 10 раз."""

from __future__ import annotations

import argparse
import http.client
import sys
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

REQUEST_COUNT = 10
CHUNK_SIZE = 64 * 1024
USER_AGENT = "url-download-speed-test/1.0"
BYTES_PER_MIB = 1024 * 1024


@dataclass(frozen=True)
class DownloadResult:
    """Результаты измерений одного полностью полученного HTTP-ответа."""

    status: int
    size_bytes: int
    elapsed_seconds: float


def positive_float(value: str) -> float:
    """Разбирает строго положительное число для интерфейса командной строки."""
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def format_size(size_bytes: int) -> str:
    """Возвращает размер в удобочитаемом двоичном формате."""
    return f"{size_bytes / BYTES_PER_MIB:.2f} MiB"


def format_speed(bytes_per_second: float) -> str:
    """Переводит байты в секунду в десятичные мегабиты в секунду."""
    return f"{bytes_per_second * 8 / 1_000_000:.2f} Mbit/s"


def download_once(url: str, timeout: float) -> DownloadResult:
    """Скачивает тело ответа полностью и измеряет затраченное время."""
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
            "Accept-Encoding": "identity",
        },
    )

    started = time.perf_counter()
    with urlopen(request, timeout=timeout) as response:
        status = response.getcode()
        content_length_header = response.headers.get("Content-Length")
        expected_size = (
            int(content_length_header) if content_length_header is not None else None
        )

        received = 0
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            received += len(chunk)

    elapsed = time.perf_counter() - started

    # Более короткое тело означает, что ответ получен не полностью.
    if expected_size is not None and received != expected_size:
        raise http.client.IncompleteRead(b"", expected_size - received)

    return DownloadResult(
        status=status,
        size_bytes=received,
        elapsed_seconds=elapsed,
    )


def run(url: str, timeout: float) -> int:
    """Выполняет все запросы, логирует каждый и выводит итоговую сводку."""
    total_bytes = 0
    total_seconds = 0.0

    for index in range(1, REQUEST_COUNT + 1):
        print(f"[{index}/{REQUEST_COUNT}] GET {url}", flush=True)
        try:
            result = download_once(url, timeout)
        except HTTPError as exc:
            print(
                f"[{index}/{REQUEST_COUNT}] FAILED: HTTP {exc.code} {exc.reason}",
                file=sys.stderr,
            )
            return 1
        except (URLError, TimeoutError, OSError, http.client.HTTPException) as exc:
            print(f"[{index}/{REQUEST_COUNT}] FAILED: {exc}", file=sys.stderr)
            return 1

        total_bytes += result.size_bytes
        total_seconds += result.elapsed_seconds
        request_speed = result.size_bytes / result.elapsed_seconds

        print(
            f"[{index}/{REQUEST_COUNT}] HTTP {result.status} | "
            f"{format_size(result.size_bytes)} ({result.size_bytes:,} bytes) | "
            f"{result.elapsed_seconds:.3f} s | {format_speed(request_speed)}",
            flush=True,
        )

    average_seconds = total_seconds / REQUEST_COUNT
    average_speed = total_bytes / total_seconds if total_seconds else 0.0

    print()
    print("Summary")
    print("-------")
    print(f"Requests completed:    {REQUEST_COUNT}")
    print(f"Average request time:  {average_seconds:.3f} s")
    print(f"Total downloaded:      {format_size(total_bytes)} ({total_bytes:,} bytes)")
    print(f"Download speed:        {format_speed(average_speed)}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download one URL 10 times sequentially and report average request "
            "time, total downloaded data, and throughput."
        )
    )
    parser.add_argument("url", help="absolute HTTP or HTTPS URL to download")
    parser.add_argument(
        "--timeout",
        type=positive_float,
        default=60.0,
        metavar="SECONDS",
        help="timeout for each connection/read operation (default: 60)",
    )
    args = parser.parse_args(argv)

    parsed = urlparse(args.url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        parser.error("URL must be an absolute http:// or https:// URL")

    return args


def main() -> int:
    args = parse_args()
    try:
        return run(args.url, args.timeout)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
