from PyPDF2 import PdfFileReader, PdfFileWriter
from pdf2image import convert_from_path, convert_from_bytes
from django.conf import settings
import cv2
import numpy as np
import os
from PIL import Image
import pyzbar.pyzbar as pyzbar


class ManageQrCode:
    images_path = None
    decoded_text = None

    def __init__(self, pdf_path):
        reader = PdfFileReader(pdf_path, 'rb')
        self.images_path = pdf_path.split(".pdf")[0]

        # self.images_path = self.images_path.replace(" ", "_")

        page = self.cut_region(reader)
        path_to_pdf = self.save_cropped_pdf(page)
        image = self.pdf_to_image(path_to_pdf)
        image = self.threshold(image)
        print(self.find_qrcode(image))

    def cut_region(self, reader):
        print(self.images_path)
        # Pegando a primeira página do pdf
        page = reader.getPage(0)
        pdf_size = page.mediaBox
        page.mediaBox.upperRight = (page.mediaBox.getUpperRight_x(), page.mediaBox.getUpperRight_y())

        # Quero entender como essa magia funciona
        value = int((pdf_size[3] * 8) / 10)
        value_b = int((pdf_size[2] * 8) / 10)

        page.mediaBox.lowerLeft = (page.mediaBox.getLowerLeft_x() + value_b, page.mediaBox.getLowerLeft_y() + value)
        # page.cropBox.upperLeft = (400,400)
        return page

    def save_cropped_pdf(self, page):
        writer = PdfFileWriter()
        writer.addPage(page)

        try:
            os.mkdir(self.images_path)
        except:
            pass
        cropped_pdf_path = os.path.join(self.images_path, 'cropped_pdf.pdf')
        with open(cropped_pdf_path, 'wb') as cropped_pdf:
            writer.write(cropped_pdf)
        return cropped_pdf_path

    def pdf_to_image(self, path_to_pdf):
        # pdf_image = convert_from_path(path_to_pdf, poppler_path=os.path.join('..', 'venv', 'poppler-0.68.0', 'bin'), dpi=1000)
        # !NOTE É PRECISO DEFINIR O DIRETÓRIO DO POPPLER NO WINDOWS OU INSTALAR NO LINUX
        pdf_image = convert_from_path(path_to_pdf, poppler_path=os.path.join(settings.BASE_DIR, 'venv', 'poppler-0.68.0', 'bin'), dpi=1000)

        # !TODO Ver como não salvar a imagem e pegar o array dela para continuar o tratamento
        file_name = "converted_image.png"
        converted_image_path = os.path.join(self.images_path, file_name)

        # Saving image (Optional)
        # for image in pdf_image:
        #     image.save(converted_image_path)

        image = np.asarray(pdf_image.pop())

        return image

    def threshold(self, image):
        # !TODO Verificar se o
        # opencv 4.5.1 precisa de cv2.IMREAD_COLOR
        image = cv2.UMat(image)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, image = cv2.threshold(image, 127, 255, cv2.THRESH_OTSU)

        file_name = 'image_threshold.png'
        image_threshold_path = os.path.join(self.images_path, file_name)
        image4save = Image.fromarray(image.get())
        image4save.save(image_threshold_path)
        # cv2.imwrite(image_threshold_path, image)

        return image.get()

    def find_qrcode(self, image):
        decoded_objects = pyzbar.decode(image)

        for obj in decoded_objects:
            print('Type : ', obj.type)
            print('Data : ', obj.data, '\n')

        if decoded_objects:
            self.decoded_text = decoded_objects[0].data
            return decoded_objects[0].data
        else:
            return "QRCode not found"

    def get_decoded_text(self):
        return self.decoded_text

    def get_images_path(self):
        return self.images_path

# ManageQrCode("../media/Evolução Assinada.pdf")