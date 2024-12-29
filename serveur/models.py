from django.db import models
from django.core.exceptions import ValidationError
import uuid
import os

def client_screenshot_upload_path(instance, filename):
    return os.path.join("client_screenshots", f"{instance.ip_address}_{filename}")

class ClientInfo(models.Model):
    nom_client = models.CharField(max_length=255, null=True, blank=True)
    pc_name = models.CharField(max_length=255, null=True)
    os_name = models.CharField(max_length=255, null=True)
    ip_address = models.GenericIPAddressField(protocol='both', unpack_ipv4=True, null=True, unique=True, default=uuid.uuid1)
    capture_time = models.DateTimeField(auto_now_add=True)
    screenshot = models.ImageField(upload_to=client_screenshot_upload_path, null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)

    # def save(self, *args, **kwargs):
    #     if ClientInfo.objects.filter(ip_address=self.ip_address).exists() and not self.pk:
    #         raise ValidationError(f"Adresse IP {self.ip_address} déjà existante.")
    #     super().save(*args, **kwargs)

    
