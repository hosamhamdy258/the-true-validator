import os
import random
import time
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

UserModel = get_user_model()

if not UserModel.objects.filter(username="admin").exists():
    UserModel.objects.create_superuser("admin", "admin@example.com", "admin")

NUM_USERS = 4

users = {f"user{i}" for i in range(1, NUM_USERS + 1)}

existing_usernames = set(UserModel.objects.values_list("username", flat=True))
for username in users - existing_usernames:
    UserModel.objects.create_user(username=username, email=f"{username}@example.com", password="test")

SPACER = 10 * "="
print(SPACER, "Database population script finished.", SPACER)
