release: python manage.py migrate
web: gunicorn main.wsgi:application --workers 3 --log-file -