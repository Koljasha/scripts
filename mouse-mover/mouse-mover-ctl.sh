#!/usr/bin/env bash

SERVICE_NAME="mouse-mover.service"

# ── Проверка статуса ───────────────────────────────
is_active() {
  systemctl --user is-active --quiet "$SERVICE_NAME" 2>/dev/null
}

# ── Показать статус красиво ────────────────────────
show_status() {
  if is_active; then
  echo -e "
  [1;32mСервис ЗАПУЩЕН[0m"
  else
  echo -e "
  [1;31mСервис ОСТАНОВЛЕН[0m"
  fi
  echo ""
}

# ── Меню ───────────────────────────────────────────
show_menu() {
  if is_active; then
  echo "  [1] Перезапустить  │  [0] Остановить  │  [Enter] Выйти"
  else
  echo "  [1] Запустить  │  [0] Остановить  │  [Enter] Выйти"
  fi
  echo ""
  echo -n "  Выбор: "
}

# ── Главный цикл ───────────────────────────────────
clear
show_status
show_menu

read -n 1 -r choice

case "$choice" in
  1)
  echo ""
  if is_active; then
  echo -e "  Перезапускаем..."
  systemctl --user restart "$SERVICE_NAME"
  else
  echo -e "  Запускаем..."
  systemctl --user start "$SERVICE_NAME"
  fi
  sleep 1
  show_status
  ;;
  0)
  echo ""
  if is_active; then
  echo -e "  Останавливаем..."
  systemctl --user stop "$SERVICE_NAME"
  else
  echo -e "  Сервис уже остановлен"
  fi
  sleep 1
  show_status
  ;;
  *)
  echo ""
  echo -e "  Выход без изменений"
  ;;
esac

echo ""
