#!/usr/bin/env bash

SERVICE_TITLE="Mouse Mover"
SERVICE_NAME="mouse-mover.service"
LOG_LINES=10

# ── Цвета ──────────────────────────────────────────
CLR_RESET="\033[0m"
CLR_GREEN="\033[1;32m"
CLR_RED="\033[1;31m"
CLR_YELLOW="\033[1;33m"
CLR_CYAN="\033[1;36m"
CLR_DIM="\033[2m"

# ── Получить статус systemd ────────────────────────
get_state() {
  systemctl --user show "$SERVICE_NAME" --property=ActiveState --value 2>/dev/null
}

# ── Проверки состояний ─────────────────────────────
is_active() {
  [[ "$(get_state)" == "active" ]]
}

is_reloading() {
  [[ "$(get_state)" == "reloading" ]]
}

# ── Показать логи ──────────────────────────────────
show_logs() {
  echo ""
  echo -e "  ${CLR_DIM}── Последние $LOG_LINES строк лога ──${CLR_RESET}"
  journalctl --user -u "$SERVICE_NAME" -n "$LOG_LINES" --no-pager 2>/dev/null \
    | sed 's/^/    /'
  echo ""
}

# ── Показать статус ────────────────────────────────
show_status() {
  local state
  state=$(get_state)

  echo ""
  case "$state" in
    active)
      echo -e "  ${CLR_GREEN}▶ Сервис ==$SERVICE_TITLE== ЗАПУЩЕН${CLR_RESET}"
      ;;
    reloading)
      echo -e "  ${CLR_YELLOW}↻ Сервис ==$SERVICE_TITLE== ПЕРЕЗАПУСКАЕТСЯ...${CLR_RESET}"
      ;;
    inactive)
      echo -e "  ${CLR_RED}○ Сервис ==$SERVICE_TITLE== ОСТАНОВЛЕН${CLR_RESET}"
      ;;
    failed)
      echo -e "  ${CLR_RED}✖ Сервис ==$SERVICE_TITLE== ОШИБКА${CLR_RESET}"
      ;;
    *)
      echo -e "  ${CLR_DIM}? Сервис ==$SERVICE_TITLE== СТАТУС: $state${CLR_RESET}"
      ;;
  esac
  echo ""
}

# ── Показать меню ──────────────────────────────────
show_menu() {
  if is_active; then
    echo "  [1] Перезапустить  │  [0] Остановить  │  [Enter] Выйти"
  elif is_reloading; then
    echo "  [1] Принудительно перезапустить  │  [0] Остановить  │  [Enter] Выйти"
  else
    echo "  [1] Запустить  │  [0] Остановить  │  [Enter] Выйти"
  fi
  echo ""
}

# ════════════════════════════════════════════════════
#  ГЛАВНЫЙ ЦИКЛ
# ════════════════════════════════════════════════════

clear
show_status
show_logs
show_menu

echo -n "  Выбор: "
read -n 1 -r choice
echo ""

case "$choice" in
  1)
    if is_reloading; then
      echo -e "  ${CLR_YELLOW}Принудительная перезагрузка...${CLR_RESET}"
      systemctl --user restart "$SERVICE_NAME"
    elif is_active; then
      echo -e "  ${CLR_CYAN}Перезапускаем...${CLR_RESET}"
      systemctl --user restart "$SERVICE_NAME"
    else
      echo -e "  ${CLR_CYAN}Запускаем...${CLR_RESET}"
      systemctl --user start "$SERVICE_NAME"
    fi
    sleep 1
    show_status
    ;;

  0)
    if is_active || is_reloading; then
      echo -e "  ${CLR_RED}Останавливаем...${CLR_RESET}"
      systemctl --user stop "$SERVICE_NAME"
      sleep 1
      show_status
    else
      echo -e "  ${CLR_DIM}Сервис уже остановлен${CLR_RESET}"
    fi
    ;;

  *)
    echo -e "  ${CLR_DIM}Выход без изменений${CLR_RESET}"
    ;;
esac

echo ""

