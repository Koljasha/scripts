#!/usr/bin/env python3
"""Мониторинг таблиц OpenCode Go (лимиты запросов) и Zen (цены за 1M токенов, устаревание).

Скрипт периодически (cron) проверяет:
https://opencode.ai/docs/ru/go/
https://opencode.ai/docs/ru/zen/
хранит снапшот в state.json и при изменениях
(появление/пропажа моделей, смена Free → платная, изменение цен, устаревание)
шлёт уведомление в Telegram.

Зависимости: pip install requests beautifulsoup4

Настройка: создать рядом со скриптом файл .env с двумя строками:
    TG_BOT_TOKEN=<токен бота от BotFather>
    TG_CHAT_ID=<id чата или канала, напр. -1001234567890>

Лог — один файл monitor_opencode.log. В конце каждого запуска проверяется число строк:
если больше LOG_MAX_LINES (10000), старые строки удаляются, остаются последние
LOG_KEEP_LINES (1000).

Пример cron (запуск каждые 4 часа); в cron.err попадает только stderr — ошибки
и необработанные краши, обычный лог пишется скриптом в monitor_opencode.log:
0 */4 * * * /usr/bin/python3 /opt/opencode-monitor/monitor_opencode.py 2>> /opt/opencode-monitor/cron.err
"""

import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from typing import NotRequired, TypedDict

import requests
from bs4 import BeautifulSoup, Tag

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
STATE_PATH = os.path.join(BASE_DIR, "state.json")
LOG_PATH = os.path.join(BASE_DIR, "monitor_opencode.log")

LOG_MAX_LINES = 10000
LOG_KEEP_LINES = 1000
HTTP_TIMEOUT = 30

DEFAULT_UA = "Mozilla/5.0 (X11; Linux x86_64) opencode-price-monitor/1.0"

PAGES = {
    "Go": "https://opencode.ai/docs/ru/go/",
    "Zen": "https://opencode.ai/docs/ru/zen/",
}

GO_HEADERS = {"Model", "запросов за 5 часов"}
ZEN_HEADERS = {"Модель", "Cached Read"}
DEPRECATED_HEADERS = {"Модель", "Дата устаревания"}

FIELD_LABELS = {
    "Go": {"за 5 часов": "за 5 часов", "в неделю": "в неделю", "в месяц": "в месяц"},
    "Zen": {
        "вход": "Вход",
        "выход": "Выход",
        "cached_read": "Cached Read",
        "cached_write": "Cached Write",
    },
}

ModelTable = dict[str, dict[str, str]]
TariffEvent = tuple[str, str, str]
PriceChange = tuple[str, list[tuple[str, str, str]]]


class SourceData(TypedDict):
    models: ModelTable
    deprecated: NotRequired[dict[str, str]]


class SourceSnapshot(TypedDict):
    fetched_at: str
    models: ModelTable
    deprecated: NotRequired[dict[str, str]]


class SourceDiff(TypedDict):
    removed: list[str]
    added: list[str]
    tariff: list[TariffEvent]
    prices: list[PriceChange]
    deprecated: list[tuple[str, str, str | None]]


logger = logging.getLogger("opencode_monitor")


def load_env() -> dict[str, str]:
    """Читает секреты Telegram из файла .env рядом со скриптом.

    Returns:
        Словарь конфигурации; значения пустые, если .env отсутствует
        или переменная не задана.
    """
    cfg = {"TG_BOT_TOKEN": "", "TG_CHAT_ID": ""}
    if not os.path.exists(ENV_PATH):
        return cfg
    with open(ENV_PATH, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            cfg[key.strip()] = value.strip().strip('"').strip("'")
    return cfg


def setup_logging() -> None:
    """Настраивает логгирование: INFO в файл, ERROR в stderr.

    Обычные записи идут только в monitor_opencode.log; stderr (cron.err)
    получает лишь ошибки и необработанные краши.
    """
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
    fh.setFormatter(fmt)
    root.addHandler(fh)
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    sh.setLevel(logging.ERROR)
    root.addHandler(sh)


def trim_log() -> None:
    """Обрезает лог до последних LOG_KEEP_LINES строк, если строк больше LOG_MAX_LINES.

    При размере ниже порога ничего не делает; факт обрезки логируется.
    """
    if not os.path.exists(LOG_PATH):
        return
    try:
        with open(LOG_PATH, encoding="utf-8") as fh:
            lines = fh.readlines()
        if len(lines) > LOG_MAX_LINES:
            with open(LOG_PATH, "w", encoding="utf-8") as fh:
                fh.writelines(lines[-LOG_KEEP_LINES:])
            logger.info(
                "Лог обрезан: было %d строк, осталось %d", len(lines), LOG_KEEP_LINES
            )
    except OSError as err:
        logger.error("Не удалось обрезать лог: %s", err)


def fetch_html(url: str, timeout: int) -> str:
    """GET-запрос страницы с 3 попытками и экспоненциальной паузой.

    Args:
        url: адрес страницы.
        timeout: таймаут запроса в секундах.

    Returns:
        HTML-разметка страницы в кодировке UTF-8.

    Raises:
        RuntimeError: если все попытки неудачны.
    """
    last_err = None
    for attempt in range(3):
        try:
            resp = requests.get(
                url, headers={"User-Agent": DEFAULT_UA}, timeout=timeout
            )
            resp.raise_for_status()
            resp.encoding = "utf-8"
            return resp.text
        except requests.RequestException as err:
            last_err = err
            logger.warning(
                "Сеть: попытка %d/3 для %s не удалась: %s", attempt + 1, url, err
            )
            time.sleep(2**attempt)
    raise RuntimeError(f"Не удалось получить {url}: {last_err}")


def _normalize(value: str) -> str:
    """Схлопывает подряд идущие пробелы и обрезает строку."""
    return re.sub(r"\s+", " ", value).strip()


def _find_table(soup: BeautifulSoup, expected_headers: set[str]) -> Tag | None:
    """Ищет первую таблицу, чей заголовок содержит все ожидаемые колонки.

    Args:
        soup: распарсенный HTML страницы.
        expected_headers: подмножество имён колонок, идентифицирующих таблицу.

    Returns:
        Элемент таблицы или None, если таблица не найдена.
    """
    for table in soup.find_all("table"):
        header_row = table.find("tr")
        if header_row is None:
            continue
        cells = [
            _normalize(c.get_text(" ", strip=True))
            for c in header_row.find_all(["th", "td"])
        ]
        if set(expected_headers) <= set(cells):
            return table
    return None


def _table_rows(table: Tag) -> list[list[str]]:
    """Возвращает строки данных таблицы (без заголовка) как списки ячеек.

    Пропускаются пустые строки.
    """
    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = [
            _normalize(c.get_text(" ", strip=True)) for c in tr.find_all(["td", "th"])
        ]
        if cells and any(cells):
            rows.append(cells)
    return rows


def _header_indexes(table: Tag) -> list[str]:
    """Возвращает имена колонок таблицы (заголовок)."""
    header_row = table.find("tr")
    return [
        _normalize(c.get_text(" ", strip=True))
        for c in header_row.find_all(["th", "td"])
    ]


def parse_go(soup: BeautifulSoup) -> ModelTable:
    """Парсит таблицу лимитов запросов Go.

    Returns:
        Словарь {модель: {"за 5 часов": ..., "в неделю": ..., "в месяц": ...}}.

    Raises:
        RuntimeError: таблица не найдена или пуста (структура страницы изменилась).
    """
    table = _find_table(soup, GO_HEADERS)
    if table is None:
        raise RuntimeError("Не найдена таблица запросов Go на странице")
    headers = _header_indexes(table)
    idx = {
        name: headers.index(name)
        for name in (
            "Model",
            "запросов за 5 часов",
            "запросов в неделю",
            "запросов в месяц",
        )
    }
    models = {}
    for cells in _table_rows(table):
        if len(cells) <= max(idx.values()):
            continue
        models[cells[idx["Model"]]] = {
            "за 5 часов": cells[idx["запросов за 5 часов"]],
            "в неделю": cells[idx["запросов в неделю"]],
            "в месяц": cells[idx["запросов в месяц"]],
        }
    if not models:
        raise RuntimeError(
            "Таблица запросов Go пуста — возможно, изменилась структура страницы"
        )
    return models


def parse_zen(soup: BeautifulSoup) -> tuple[ModelTable, dict[str, str]]:
    """Парсит таблицу цен Zen и таблицу устаревания.

    Returns:
        Кортеж (модели, deprecated): модели — {модель: {вход, выход, cached_read,
        cached_write}}, deprecated — {модель: дата устаревания}.

    Raises:
        RuntimeError: таблица цен не найдена или пуста.
    """
    table = _find_table(soup, ZEN_HEADERS)
    if table is None:
        raise RuntimeError("Не найдена таблица цен Zen на странице")
    headers = _header_indexes(table)
    idx = {
        name: headers.index(name)
        for name in ("Модель", "Вход", "Выход", "Cached Read", "Cached Write")
    }
    models = {}
    for cells in _table_rows(table):
        if len(cells) <= max(idx.values()):
            continue
        models[cells[idx["Модель"]]] = {
            "вход": cells[idx["Вход"]],
            "выход": cells[idx["Выход"]],
            "cached_read": cells[idx["Cached Read"]],
            "cached_write": cells[idx["Cached Write"]],
        }
    if not models:
        raise RuntimeError(
            "Таблица цен Zen пуста — возможно, изменилась структура страницы"
        )

    deprecated = {}
    dtable = _find_table(soup, DEPRECATED_HEADERS)
    if dtable is None:
        logger.warning("Zen: таблица устаревания не найдена — страница изменилась?")
    else:
        dheaders = _header_indexes(dtable)
        didx = {name: dheaders.index(name) for name in ("Модель", "Дата устаревания")}
        for cells in _table_rows(dtable):
            if len(cells) <= max(didx.values()):
                continue
            deprecated[cells[didx["Модель"]]] = cells[didx["Дата устаревания"]]
    return models, deprecated


def diff_models(
    prev: ModelTable, curr: ModelTable
) -> tuple[list[str], list[str], list[TariffEvent], list[PriceChange]]:
    """Сравнивает два снапшота моделей.

    Пара «X Free» и «X» распознаётся как смена тарифа (одно событие), а не как
    пропажа и появление. Дубли имён (варианты лимитов токенов, например
    «Claude Sonnet 4.5 (≤ 200K tokens)» и «(> 200K tokens)») — отдельные модели.

    Returns:
        Кортеж (пропали, появились, смены тарифа, изменения цен).
    """
    prev_keys, curr_keys = set(prev), set(curr)
    removed = prev_keys - curr_keys
    added = curr_keys - prev_keys
    tariff = []

    for name in list(removed):
        if name.endswith(" Free"):
            base = name[: -len(" Free")]
            if base in added:
                tariff.append((name, base, "платной"))
                removed.discard(name)
                added.discard(base)

    for name in list(added):
        if name.endswith(" Free"):
            base = name[: -len(" Free")]
            if base in removed:
                tariff.append((base, name, "бесплатной"))
                added.discard(name)
                removed.discard(base)

    price_changes = []
    for name in prev_keys & curr_keys:
        if prev[name] != curr[name]:
            fields = [
                (k, prev[name].get(k), curr[name].get(k))
                for k in curr[name]
                if prev[name].get(k) != curr[name].get(k)
            ]
            price_changes.append((name, fields))

    return sorted(removed), sorted(added), tariff, price_changes


def build_message(changes: dict[str, SourceDiff], now_str: str) -> str:
    """Собирает текст уведомления для Telegram.

    Args:
        changes: обнаруженные изменения по источникам Go/Zen.
        now_str: дата и время в человекочитаемом формате.

    Returns:
        Текст сообщения, обрезанный до 4000 символов (лимит Telegram).
    """
    out = [f"📡 OpenCode-монитор — изменения ({now_str})", ""]

    removed = [f"{s}: {n}" for s in ("Go", "Zen") for n in changes[s]["removed"]]
    added = [f"{s}: {n}" for s in ("Go", "Zen") for n in changes[s]["added"]]
    tariff = [
        f"{s}: {old} → {new} (стала {label})"
        for s in ("Go", "Zen")
        for (old, new, label) in changes[s]["tariff"]
    ]
    prices = []
    for s in ("Go", "Zen"):
        for name, fields in changes[s]["prices"]:
            bits = [f"{FIELD_LABELS[s][k]}: {old} → {new}" for k, old, new in fields]
            prices.append(f"{s}: {name} — {', '.join(bits)}")
    dep_events = []
    for name, new_date, old_date in changes["Zen"]["deprecated"]:
        tail = f"{new_date}" if old_date is None else f"{new_date} (было: {old_date})"
        dep_events.append(f"Zen: {name} — дата устаревания {tail}")

    def add(title: str, items: list[str]) -> None:
        """Добавляет секцию с заголовком и строками, если строки есть."""
        if items:
            out.append(title)
            out.extend(f"  {x}" for x in items)
            out.append("")

    add("❌ Пропали:", removed)
    add("🆕 Появились:", added)
    add("🔄 Смена тарифа:", tariff)
    add("💰 Изменены цены:", prices)
    add("⏳ Устаревание:", dep_events)

    while out and out[-1] == "":
        out.pop()
    text = "\n".join(out)
    if len(text) > 4000:
        text = text[:3950] + "\n✂️ ...(обрезано, слишком много изменений)"
    return text


def send_tg(cfg: dict[str, str], text: str) -> None:
    """Отправляет текст в Telegram через sendMessage.

    Если токен или chat_id не заданы, отправка пропускается с предупреждением.
    Ошибки сети логируются, но не роняют скрипт.
    """
    token = cfg.get("TG_BOT_TOKEN", "").strip()
    chat = cfg.get("TG_CHAT_ID", "").strip()
    if not token or not chat:
        logger.warning(
            "TG не настроен (TG_BOT_TOKEN/TG_CHAT_ID пустые) — уведомление пропущено"
        )
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(url, data={"chat_id": chat, "text": text}, timeout=30)
        resp.raise_for_status()
        logger.info("TG: уведомление отправлено (%d символов)", len(text))
    except requests.RequestException as err:
        logger.error("TG: не удалось отправить уведомление: %s", err)


def load_state() -> dict[str, SourceSnapshot] | None:
    """Читает снапшот из state.json.

    Returns:
        Словарь состояния или None, если файл отсутствует либо повреждён
        (в этом случае будет повторная инициализация).
    """
    if not os.path.exists(STATE_PATH):
        return None
    try:
        with open(STATE_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as err:
        logger.error("state.json повреждён (%s) — будет повторная инициализация", err)
        return None


def save_state(state: dict[str, SourceSnapshot]) -> None:
    """Записывает снапшот состояния в state.json."""
    with open(STATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)


def main() -> int:
    """Основной цикл: загрузка страниц, сравнение со снапшотом, лог и TG.

    При первом запуске (нет state.json) сохраняет снапшот без уведомлений.

    Returns:
        Код выхода: 0 — успех; 1 — фатальная ошибка (отрабатывается в __main__).
    """
    cfg = load_env()
    setup_logging()

    fresh: dict[str, SourceData] = {}
    for source, url in PAGES.items():
        html = fetch_html(url, HTTP_TIMEOUT)
        soup = BeautifulSoup(html, "html.parser")
        if source == "Go":
            fresh["Go"] = {"models": parse_go(soup)}
        else:
            models, deprecated = parse_zen(soup)
            fresh["Zen"] = {"models": models, "deprecated": deprecated}

    now = datetime.now().astimezone()
    now_iso = now.isoformat(timespec="seconds")
    now_human = now.strftime("%Y-%m-%d %H:%M:%S")
    prev = load_state()

    if prev is None:
        state: dict[str, SourceSnapshot] = {
            s: {"fetched_at": now_iso, **data} for s, data in fresh.items()
        }
        save_state(state)
        for s, data in fresh.items():
            logger.info(
                "Инициализация %s: %d моделей, %d записей устаревания",
                s,
                len(data["models"]),
                len(data.get("deprecated", {})),
            )
        logger.info("Первый запуск: снапшот сохранён в state.json, изменений нет")
        return 0

    changes: dict[str, SourceDiff] = {}
    total = 0
    for s in ("Go", "Zen"):
        old = prev.get(s, {}).get("models", {})
        removed, added, tariff, prices = diff_models(old, fresh[s]["models"])
        changes[s] = {
            "removed": removed,
            "added": added,
            "tariff": tariff,
            "prices": prices,
            "deprecated": [],
        }
        total += len(removed) + len(added) + len(tariff) + len(prices)
        for n in removed:
            logger.info("%s: модель пропала: %s", s, n)
        for n in added:
            logger.info("%s: модель появилась: %s", s, n)
        for old_n, new_n, label in tariff:
            logger.info("%s: смена тарифа: %s → %s (%s)", s, old_n, new_n, label)
        for name, fields in prices:
            logger.info("%s: изменены цены: %s", s, name)

    dep_events = []
    old_dep = prev.get("Zen", {}).get("deprecated")
    new_dep = fresh["Zen"]["deprecated"]
    if old_dep is None:
        logger.info(
            "Zen: начинаем отслеживать таблицу устаревания (%d записей)", len(new_dep)
        )
    else:
        for name in sorted(set(new_dep) - set(old_dep)):
            dep_events.append((name, new_dep[name], None))
            logger.info(
                "Zen: модель добавлена в список устаревающих: %s (%s)",
                name,
                new_dep[name],
            )
        for name in sorted(set(new_dep) & set(old_dep)):
            if new_dep[name] != old_dep[name]:
                dep_events.append((name, new_dep[name], old_dep[name]))
                logger.info(
                    "Zen: изменена дата устаревания %s: %s → %s",
                    name,
                    old_dep[name],
                    new_dep[name],
                )
    changes["Zen"]["deprecated"] = dep_events
    total += len(dep_events)

    state = {s: {"fetched_at": now_iso, **fresh[s]} for s in fresh}
    save_state(state)

    if total == 0:
        logger.info("Нет изменений")
        return 0

    logger.info("Найдено изменений: %d", total)
    send_tg(cfg, build_message(changes, now_human))
    return 0


if __name__ == "__main__":
    code = 0
    try:
        code = main()
    except Exception as err:
        logging.getLogger("opencode_monitor").exception("Фатальная ошибка: %s", err)
        code = 1
    trim_log()
    sys.exit(code)
