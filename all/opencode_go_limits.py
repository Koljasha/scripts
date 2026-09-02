#!/usr/bin/env python3
"""Получает с https://opencode.ai/docs/ru/go/ таблицу лимитов OpenCode Go,
сортирует строки по количеству запросов в месяц (по убыванию)
и выводит на экран с выравниванием колонок."""

import re
import sys
import html
from html.parser import HTMLParser
from urllib.request import Request, urlopen

URL = "https://opencode.ai/docs/ru/go/"
ANCHOR = "В таблице ниже приведено примерное количество запросов на основе типичных сценариев использования Go:"
UA = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


class TableParser(HTMLParser):
    """Извлекает из переданного фрагмента HTML единственную таблицу."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(html.unescape(" ".join("".join(self._cell).split())))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None


def fetch_page(url: str) -> str:
    """Скачивает страницу и возвращает её HTML-код в текстовом виде."""
    req = Request(url, headers=UA)
    with urlopen(req, timeout=30) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


def parse_table(page: str) -> list[list[str]]:
    """Находит таблицу после фразы-маркера и возвращает её строки (списки ячеек)."""
    pos = page.find(ANCHOR)
    if pos == -1:
        raise RuntimeError(
            "Не найдена фраза-маркер на странице (возможно, изменилась структура)."
        )
    start = page.find("<table", pos)
    if start == -1:
        raise RuntimeError("Не найдена таблица после маркера.")
    end = page.find("</table>", start)
    if end == -1:
        raise RuntimeError("Не найден конец таблицы.")
    parser = TableParser()
    parser.feed(page[start : end + len("</table>")])
    if not parser.rows:
        raise RuntimeError("Таблица пуста.")
    return parser.rows


def sort_by_month(rows: list[list[str]]) -> list[list[str]]:
    """Возвращает строки данных, отсортированные по запросам в месяц по убыванию."""

    def month_value(row: list[str]) -> int:
        try:
            return int(re.sub(r"[^\d]", "", row[-1]))
        except (IndexError, ValueError):
            raise RuntimeError(
                f"Не удалось прочитать количество запросов в месяц в строке: {row!r}"
            )

    return sorted(rows[1:], key=month_value, reverse=True)


def fmt_num(s: str) -> str:
    """Форматирует строку с числом, добавляя разделитель тысяч."""
    digits = re.sub(r"[^\d]", "", s)
    return f"{int(digits):,}".replace(",", "\u2009") if digits else s


def render(header: list[str], rows: list[list[str]]) -> str:
    """Собирает таблицу в текст с выровненными колонками и разделителем."""
    table = [header] + rows
    widths = [max(len(str(row[i])) for row in table) for i in range(len(header))]
    lines = [
        " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        for row in table
    ]
    sep = "-+-".join("-" * w for w in widths)
    return "\n".join([lines[0], sep, *lines[1:]])


def main() -> int:
    """Точка входа: скачивает страницу, печатает отсортированную таблицу."""
    try:
        page = fetch_page(URL)
        rows = parse_table(page)
        header, data = rows[0], sort_by_month(rows)
        for row in data:
            row[1:] = [fmt_num(c) for c in row[1:]]
        print(render(header, data))
        return 0
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
