from django.contrib import admin

from apps.bienes.models import Siga, Bien
from apps.bienes.models.area import Area
from apps.bienes.models.sede import Sede

# Register your models here.
admin.site.register(Siga)
admin.site.register(Bien)
admin.site.register(Area)
admin.site.register(Sede)
