"""
WSGI config for aetherchat project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import shutil
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aetherchat.settings')

# --- VERCEL EPHEMERAL DATABASE HACK ---
# Vercel serverless has a Read-Only filesystem, which crashes SQLite writes.
# But Vercel allows Read-Write in the '/tmp' directory.
# If we are on Vercel, copy the pre-migrated DB into /tmp so the website works!
if os.environ.get('VERCEL_URL') or os.environ.get('VERCEL'):
    tmp_db_path = '/tmp/db.sqlite3'
    local_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
    if not os.path.exists(tmp_db_path) and os.path.exists(local_db_path):
        shutil.copy2(local_db_path, tmp_db_path)

application = get_wsgi_application()
app = application
