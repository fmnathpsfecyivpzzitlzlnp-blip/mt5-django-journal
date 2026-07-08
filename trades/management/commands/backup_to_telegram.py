import os
import subprocess
import zipfile
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Создает бэкап БД, архивирует в ZIP, отправляет в Telegram и удаляет следы'

    def handle(self, *args, **kwargs):
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)

        if not bot_token or not chat_id:
            self.stdout.write(self.style.ERROR("❌ Не настроены TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID в .env"))
            return

        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings.get('HOST', 'localhost')
        db_port = db_settings.get('PORT', '5432')

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        dump_file = os.path.join(backup_dir, f"db_dump_{timestamp}.sql")
        zip_file = os.path.join(backup_dir, f"Journal_Backup_{timestamp}.zip")

        os.environ['PGPASSWORD'] = str(db_password)

        command = [
            'pg_dump',
            '-U', str(db_user),
            '-h', str(db_host),
            '-p', str(db_port),
            '-F', 'c',  # Формат custom (лучше сжимается)
            '-f', dump_file,
            str(db_name)
        ]

        try:
            # 1. Делаем дамп базы
            self.stdout.write(self.style.WARNING('⏳ Создание дампа PostgreSQL...'))
            subprocess.run(command, check=True)

            # 2. Пакуем в ZIP
            self.stdout.write(self.style.WARNING('🗜️ Архивация в ZIP...'))
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(dump_file, os.path.basename(dump_file))

            # 3. Отправляем в Telegram
            self.stdout.write(self.style.WARNING('🚀 Отправка архива в Telegram...'))
            url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

            with open(zip_file, 'rb') as doc:
                payload = {
                    'chat_id': chat_id,
                    'caption': f"📦 Авто-бэкап базы данных: {db_name}\n📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                }
                files = {'document': doc}
                res = requests.post(url, data=payload, files=files)

            if res.status_code == 200:
                self.stdout.write(self.style.SUCCESS('✅ Бэкап успешно отправлен в Telegram!'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Ошибка Telegram API: {res.text}'))

        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка базы данных (pg_dump): {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Критическая ошибка: {e}'))
        finally:
            # 4. Жесткая очистка (Удаляем всё, чтобы не занимать место на диске)
            self.stdout.write(self.style.WARNING('🧹 Очистка временных файлов...'))
            if os.path.exists(dump_file):
                os.remove(dump_file)
            if os.path.exists(zip_file):
                os.remove(zip_file)
            self.stdout.write(self.style.SUCCESS('🏁 Процесс завершен.'))