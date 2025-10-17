import multiprocessing

pythonpath = "/app"

wsgi_app = "core.wsgi:application"

bind = "unix:///run/gunicorn.sock"

workers = 4 if multiprocessing.cpu_count() * 2 >= 4 else 2

capture_output = True

preload_app = True

reload = True

errorlog = "/app/logs/gunicorn/error.log"

loglevel = "error"
