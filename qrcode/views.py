import glob
import os

from rest_framework import status
from rest_framework.parsers import FileUploadParser
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

# For managing qrcode
from .manage_qr_code import ManageQrCode


class QrCodeView(APIView):
    parser_class = (FileUploadParser,)
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'QRCodeTemplate/simple_upload.html'


    @staticmethod
    def get(request):
        return Response()

    @staticmethod
    def insert_pdf_in_db():
        # Caminho para o pdf
        path = ("/home/knowrafa/")
        files_pdf = glob.glob(path + "*.pdf")

        for pdf_path in files_pdf:
            filter_name = os.path.split(pdf_path)[1]
            qr_code = ManageQrCode(pdf_path)
            decoded_text = qr_code.get_decoded_text()
            payload = {}
            if decoded_text is not None:
                payload['name'] = filter_name
                payload['qr_code'] = decoded_text
                try:
                    payload['qr_code_image'] = qr_code.qr_code_image64.decode('utf-8')
                except:
                    pass
            else:
                payload['decoded_text'] = "Seu QR Code não foi identificado"
        return Response()

    @staticmethod
    def post(request):
        if request.FILES['myfile']:
            myfile = request.FILES['myfile']
            qr_code = ManageQrCode(myfile.file)
            decoded_text = qr_code.get_decoded_text()
            payload = {}
            if decoded_text is not None:
                payload['decoded_text'] = decoded_text
                payload['image'] = qr_code.qr_code_image64.decode('utf-8')
            else:
                payload['decoded_text'] = "Seu QR Code não foi identificado"
            return Response(payload, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

