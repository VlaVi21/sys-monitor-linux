#!/usr/bin/env python3
"""
Збирач системної телеметрії для Linux (WSL: температура зазвичай недоступна).

Кожні INTERVAL секунд записує у CSV: температуру CPU, навантаження CPU та
використання RAM. Зупинка: Ctrl+C.
"""
import time
import csv
import os
from datetime import datetime

# Шлях до файлу логів (у продакшні краще абсолютний)
LOG_FILE = "telemetry.csv"
# Інтервал збору даних (секунди); він же вікно усереднення навантаження CPU
INTERVAL = 5


def get_cpu_temp():
    """Повертає температуру CPU в °C або "N/A", якщо датчик недоступний."""
    temp_path = "/sys/class/thermal/thermal_zone0/temp"
    try:
        with open(temp_path, "r") as f:
            temp_raw = f.read().strip()
            # Ядро віддає міліградуси
            return round(float(temp_raw) / 1000.0, 1)
    except FileNotFoundError:
        # Для WSL або систем без датчика температури
        return "N/A"


def get_ram_usage():
    """Повертає відсоток використання RAM за /proc/meminfo (0.0 при помилці)."""
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()

        mem_total = 0
        mem_available = 0

        for line in lines:
            if line.startswith("MemTotal:"):
                mem_total = int(line.split()[1])
            elif line.startswith("MemAvailable:"):
                mem_available = int(line.split()[1])

        if mem_total > 0:
            usage_percent = ((mem_total - mem_available) / mem_total) * 100
            return round(usage_percent, 1)
        return 0.0
    except Exception as e:
        # Збій однієї метрики не повинен зупиняти збір
        return 0.0


def get_cpu_times():
    """Повертає (idle, total) — кумулятивний час CPU з /proc/stat.

    Для навантаження потрібна різниця між двома вимірюваннями.
    """
    try:
        with open("/proc/stat", "r") as f:
            lines = f.readlines()
            for line in lines:
                # Пробіл після "cpu" відсікає рядки cpu0, cpu1, ...
                if line.startswith("cpu "):
                    parts = [float(p) for p in line.split()[1:]]
                    idle = parts[3] + parts[4] # idle + iowait
                    non_idle = parts[0] + parts[1] + parts[2] + parts[5] + parts[6] + parts[7]
                    total = idle + non_idle
                    return idle, total
    except Exception:
        return 0, 0


def main():
    # Перевіряємо до відкриття, щоб знати, чи писати заголовок
    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, mode='a', newline='') as csv_file:
        fieldnames = ['Timestamp', 'Temp_C', 'CPU_Load_%', 'RAM_Usage_%']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        print(f"Збір телеметрії розпочато. Логи записуються у {LOG_FILE}")
        print("Натисніть Ctrl+C для зупинки.\n")

        prev_idle, prev_total = get_cpu_times()

        try:
            while True:
                time.sleep(INTERVAL)

                # Розрахунок навантаження CPU за інтервал
                curr_idle, curr_total = get_cpu_times()
                total_diff = curr_total - prev_total
                idle_diff = curr_idle - prev_idle

                cpu_load = 0.0
                # Захист від ділення на нуль при збої читання
                if total_diff > 0:
                    # Увага: +5 у float дає зсув ~+0.5 п.п.
                    cpu_load = round((1000 * (total_diff - idle_diff) / total_diff + 5) / 10, 1)

                prev_idle, prev_total = curr_idle, curr_total

                # Збір інших метрик
                temp = get_cpu_temp()
                ram = get_ram_usage()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Запис у CSV
                writer.writerow({
                    'Timestamp': timestamp,
                    'Temp_C': temp,
                    'CPU_Load_%': cpu_load,
                    'RAM_Usage_%': ram
                })
                csv_file.flush() # Примусовий запис з буфера на диск

        except KeyboardInterrupt:
            print("\nМоніторинг зупинено.")


if __name__ == "__main__":
    main()
