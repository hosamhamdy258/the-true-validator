FROM python:3.13-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    gettext \
    redis-server \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install wheel
RUN pip install --no-cache-dir -r requirements.txt

RUN rm /etc/nginx/sites-enabled/default
COPY ./config/nginx/nginx.conf /etc/nginx/sites-enabled/default

COPY ./config/supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY . .

RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]

EXPOSE 80 443 8000 9000

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

