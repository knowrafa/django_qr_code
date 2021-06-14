import glob
import os

from rest_framework.parsers import FileUploadParser
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView



class LoginView(APIView):
    template_name = 'login/login.html'

    @staticmethod
    def get(request):
        return Response()
