"""
WSGI config for dianisma_project.
"""
import os
import pymysql

# Allow PyMySQL to be used as a drop-in replacement for mysqlclient.
pymysql.install_as_MySQLdb()

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dianisma_project.settings')
application = get_wsgi_application()
