from django.urls import path
from . import views

app_name = 'qrcode'
urlpatterns = [
    path('', views.QrCodeView.as_view(), name='QR Code View'),
]
