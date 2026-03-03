import sqlite3
import os
from datetime import datetime

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
DB_PATH     = os.path.join(SCRIPT_DIR, 'database', 'kondee.db')

BACKUP_DIR  = SCRIPT_DIR
backup_name = f"kondee_backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db"
BACKUP_PATH = os.path.join(BACKUP_DIR, backup_name)


def create_backup():
    if not os.path.exists(DB_PATH):
        print(f"Ошибка: файл базы данных не найден по пути {DB_PATH}")
        return

    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(BACKUP_PATH)

    try:
        src.backup(dst)
        size = os.path.getsize(BACKUP_PATH)
        print(f"Резервная копия успешно создана:")
        print(f"  Файл: {backup_name}")
        print(f"  Путь: {os.path.abspath(BACKUP_PATH)}")
        print(f"  Размер: {size} байт")
        print(f"  Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    finally:
        dst.close()
        src.close()


if __name__ == '__main__':
    create_backup()