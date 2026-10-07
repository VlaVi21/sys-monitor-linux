# System Resource Monitor

Скрипт для фонового збору телеметрії системи (CPU, RAM, Temp) у файл формату CSV. Реалізовано виключно базовими засобами Python через читання системних файлів `/proc/` та `/sys/`.

## Особливості використання у WSL
Цей скрипт повністю сумісний із WSL Debian. Оскільки WSL не емулює апаратні датчики температури, поле `Temp_C` записуватиметься як `N/A`. Systemd у нових версіях WSL підтримується, але його необхідно увімкнути у `wsl.conf`.

## Розгортання та запуск як демона (systemd)

1. **Підготовка файлів:**
   Створіть директорію для скрипта і скопіюйте туди `sys_monitor.py`:
   ```bash
   sudo mkdir -p /opt/sys_monitor
   sudo cp sys_monitor.py /opt/sys_monitor/
   sudo chmod +x /opt/sys_monitor/sys_monitor.py
