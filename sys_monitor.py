#!/usr/bin/env python3
import time
import csv
import os
from datetime import datetime

# Шлях до файлу логів
LOG_FILE = "telemetry.csv"
# Інтервал збору даних (секунди)
INTERVAL = 5

def get_cpu_temp():
    """Зчитує температуру процесора. У WSL може бути недоступно."""
    temp_path = "/sys/class/thermal/thermal_zone0/temp"
    try:
        with open(temp_path, "r") as f:
            temp_raw = f.read().strip()
            return round(float(temp_raw) / 1000.0, 1)
    except FileNotFoundError:
        # Для WSL або систем без датчика температури
        return "N/A"

def get_ram_usage():
    """Рахує відсоток використання RAM парсячи /proc/meminfo."""
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
        return 0.0

def get_cpu_times():
    """Зчитує час роботи CPU з /proc/stat для розрахунку навантаження."""
    try:
        with open("/proc/stat", "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("cpu "):
                    parts = [float(p) for p in line.split()[1:]]
                    idle = parts[3] + parts[4] # idle + iowait
                    non_idle = parts[0] + parts[1] + parts[2] + parts[5] + parts[6] + parts[7]
                    total = idle + non_idle
                    return idle, total
    except Exception:
        return 0, 0

def main():
    # Ініціалізація файлу
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
                if total_diff > 0:
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
