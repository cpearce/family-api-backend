from django.contrib import admin
from api.models import Individual, Family, PasswordResetRequest

models = [
    Individual,
    Family,
    PasswordResetRequest,
]
for model in models:
    admin.site.register(model)
