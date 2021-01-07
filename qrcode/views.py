import os

from django.core.files.storage import FileSystemStorage
from django.conf import settings
# Rest import
from rest_framework import status
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser

# For managing qrcode
from .manage_qr_code import ManageQrCode

# Create your views here.


class QrCodeView(APIView):
    parser_class = (FileUploadParser,)
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'QRCodeTemplate/simple_upload.html'

    @staticmethod
    def get(request):
        return Response()

    @staticmethod
    def post(request):
        if request.FILES['myfile']:
            myfile = request.FILES['myfile']
            fs = FileSystemStorage()
            # Salvou em '/media/' o arquivo enviado por upload (com o nome .name e o arquivo myfile)
            filename = fs.save(myfile.name, myfile)
            # Obtendo o link para o arquivo em /media/
            uploaded_file_url = fs.url(filename)
            # Retornando para a view
            print(fs.path(name=filename))
            print(fs.url(name=filename))
            ManageQrCode.cut_region(pdf_archive=fs.path(name=filename))

            return Response({'uploaded_file_url': uploaded_file_url}, status=status.HTTP_200_OK)

        return Response({}, status=status.HTTP_400_BAD_REQUEST)