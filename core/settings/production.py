import logging
import logging.config

from logger_config import LOGGING

DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"]


logging.config.dictConfig(LOGGING)

async_logger = logging.getHandlerByName("async_queue")
async_logger.start_listener()

# =========================
# ! this section is handled by nginx

# SECURE_SSL_REDIRECT = True

# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# SECURE_HSTS_PRELOAD = True

# SECURE_HSTS_SECONDS = 120
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
# =========================
