from django.contrib import admin
from ..models import File
from .admins import FileAdmin

admin.site.register(File, FileAdmin)
