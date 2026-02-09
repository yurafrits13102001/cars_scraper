#!/usr/bin/env bash
# Виходимо при будь-якій помилці
set -o errexit

pip install -r requirements.txt
# Встановлюємо ТІЛЬКИ браузер, без системних залежностей (--with-deps),
# бо на Render немає прав root.
playwright install chromium
