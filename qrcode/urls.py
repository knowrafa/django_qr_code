from django.urls import path
from . import views

app_name = 'qrcode'
urlpatterns = [
    path('detect/', views.QrCodeView.as_view(), name='detect'),
]
