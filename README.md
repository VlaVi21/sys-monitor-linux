# System Resource Monitor

Легкий скрипт для фонового збору телеметрії системи (температура CPU, навантаження CPU, використання RAM) у CSV-файл. Написаний лише на стандартній бібліотеці Python: дані читаються напряму з `/proc/` та `/sys/`, без сторонніх залежностей.

## Можливості

- Збір метрик з заданим інтервалом (за замовчуванням 5 секунд)
- Запис у CSV з автоматичним створенням заголовка
- Негайний запис на диск після кожного виміру (`flush`), тож дані не губляться при збої
- Запуск у терміналі або як systemd-демон з автоперезапуском
- Працює у WSL (з обмеженням щодо температури, див. нижче)

## Метрики

| Колонка       | Опис                                           | Джерело                                  |
|---------------|------------------------------------------------|------------------------------------------|
| `Timestamp`   | Час виміру (`YYYY-MM-DD HH:MM:SS`)             | системний годинник                       |
| `Temp_C`      | Температура CPU, °C (або `N/A`, якщо датчика немає) | `/sys/class/thermal/thermal_zone0/temp` |
| `CPU_Load_%`  | Навантаження CPU за інтервал, %                | `/proc/stat`                             |
| `RAM_Usage_%` | Використання оперативної пам'яті, %            | `/proc/meminfo`                          |

Приклад виводу `telemetry.csv`:

```csv
Timestamp,Temp_C,CPU_Load_%,RAM_Usage_%
2026-10-07 12:00:05,45.0,12.3,38.7
2026-10-07 12:00:10,45.5,8.1,38.8
```

## Вимоги

- Linux (або WSL)
- Python 3.6+
- systemd (лише для запуску як демона)

## Швидкий старт

```bash
git clone https://github.com/VlaVi21/sys-monitor-linux.git
cd sys-monitor-linux
python3 sys_monitor.py
```

Лог записується у `telemetry.csv` у поточній директорії. Зупинити скрипт можна через `Ctrl+C`.

## Конфігурація

Параметри задаються константами на початку `sys_monitor.py`:

| Змінна     | За замовчуванням | Опис                         |
|------------|------------------|------------------------------|
| `LOG_FILE` | `telemetry.csv`  | Шлях до файлу з логами       |
| `INTERVAL` | `5`              | Інтервал збору даних, секунд |

## Розгортання як демона (systemd)

1. **Підготуйте файли.** Створіть директорію й скопіюйте скрипт:

```bash
   sudo mkdir -p /opt/sys_monitor
   sudo cp sys_monitor.py /opt/sys_monitor/
   sudo chmod +x /opt/sys_monitor/sys_monitor.py
```

2. **Встановіть unit-файл:**

```bash
   sudo cp monitor.service /etc/systemd/system/
```

3. **Запустіть сервіс і додайте його в автозавантаження:**

```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now monitor.service
```

4. **Перевірте статус:**

```bash
   systemctl status monitor.service
```

Сервіс запускається з `WorkingDirectory=/opt/sys_monitor`, тому лог буде тут: `/opt/sys_monitor/telemetry.csv`. При збої сервіс автоматично перезапускається через 10 секунд.

### Корисні команди

```bash
# Перегляд журналу сервісу
journalctl -u monitor.service -f

# Перегляд останніх записів телеметрії
tail -f /opt/sys_monitor/telemetry.csv

# Зупинка / вимкнення
sudo systemctl stop monitor.service
sudo systemctl disable monitor.service
```

## Особливості використання у WSL

Скрипт повністю сумісний із WSL Debian. WSL не емулює апаратні датчики температури, тому поле `Temp_C` матиме значення `N/A`.

Щоб використовувати systemd у WSL, увімкніть його у `/etc/wsl.conf`:

```ini
[boot]
systemd=true
```

Потім перезапустіть WSL з Windows: `wsl --shutdown`.

## Структура проєкту

```
.
├── sys_monitor.py    # Скрипт збору телеметрії
├── monitor.service   # Unit-файл systemd
└── README.md
```

## Ліцензія

Додайте файл `LICENSE` (наприклад, MIT) і вкажіть його тут.
