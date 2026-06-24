
import os
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Создает полную резервную копию базы данных PostgreSQL'

    def handle(self, *args, **kwargs):
        # Достаем настройки базы из settings.py
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings.get('HOST', 'localhost')
        db_port = db_settings.get('PORT', '5432')

        # Папка для бэкапов (будет лежать рядом с кодом на диске D:)
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # Формируем имя файла с текущей датой
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_file = os.path.join(backup_dir, f"{db_name}_backup_{timestamp}.sql")

        # Передаем пароль в переменные среды, чтобы утилита не просила его ввести
        os.environ['PGPASSWORD'] = str(db_password)

        # Команда дампа (экспорта) базы
        command = [
            'pg_dump',
            '-U', str(db_user),
            '-h', str(db_host),
            '-p', str(db_port),
            '-F', 'c',  # Формат 'c' (custom) - сжатый, идеально для восстановления
            '-f', backup_file,
            str(db_name)
        ]

        try:
            self.stdout.write(self.style.WARNING(f'Запуск создания бэкапа: {backup_file}...'))
            subprocess.run(command, check=True)
            self.stdout.write(self.style.SUCCESS('✅ Бэкап успешно создан!'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка при создании бэкапа: {e}'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                '❌ Утилита pg_dump не найдена! Убедись, что путь к bin папке PostgreSQL '
                '(например, C:\\Program Files\\PostgreSQL\\15\\bin) добавлен в системную переменную PATH Windows.'
            ))