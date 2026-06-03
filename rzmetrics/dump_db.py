import os
import sys
import django

sys.path.append('C:\\Users\\user\\Desktop\\Artur\\Rzmetrics\\rzmetrics\\rzmetrics')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rzmetrics.settings')

# Инициализировать Django
django.setup()

from django.core.management import call_command


# Установить stdout в UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Открыть файл с UTF-8 кодировкой
with open('data.json', 'w', encoding='utf-8') as f:
    call_command(
        'dumpdata',
        exclude=['contenttypes', 'auth.permission'],
        natural_foreign=True,
        natural_primary=True,
        stdout=f
    )
print("Дамп успешно создан в data.json")