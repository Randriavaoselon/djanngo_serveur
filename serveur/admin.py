from django.contrib import admin
from .models import ClientInfo
# Register your models here.
@admin.register(ClientInfo)
class ClientInfoAdmin(admin.ModelAdmin):
    list_display = ('pc_name', 'os_name', 'ip_address', 'capture_time')



