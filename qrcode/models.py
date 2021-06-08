# from django.db import models
# from django.utils.translation import gettext_lazy as _
# import uuid
# from django.utils.html import format_html
# from base64 import b64decode
#
#
# class DocumentModel(models.Model):
#     id = models.UUIDField(primary_key=True, verbose_name=_('uuid'), default=uuid.uuid4, unique=True)
#     name = models.CharField("Nome do documento", max_length=255)
#     qr_code = models.CharField("Código do QR Code", max_length=255)
#     qr_code_image = models.TextField("Imagem do QR Code (Base64)")
#
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     def image_thumb(self):
#         if self.qr_code_image:
#             return format_html(f'<img src="data:image/png;base64, {self.qr_code_image}" alt="QR Code" width="100"/>')
#     image_thumb.short_description = "Imagem do QR Code"
#
#     def __str__(self):
#         return str(self.name)
