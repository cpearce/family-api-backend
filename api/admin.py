from django.contrib import admin
from api.models import Individual, Family

models = [
    Individual,
    Family,
]
for model in models:
    admin.site.register(model)
