from PyPDF2 import PdfFileReader, PdfFileWriter
from pdf2image import convert_from_path, convert_from_bytes
from django.conf import settings
import cv2
import numpy as np
import os
from PIL import Image
import pyzbar.pyzbar as pyzbar
import timeit


class ManageQrCode:
    images_path = None
    decoded_text = None

    def __init__(self, pdf_path, side='right'):
        start_time = timeit.default_timer()
        reader = PdfFileReader(pdf_path, 'rb')
        self.images_path = pdf_path.split(".pdf")[0]

        # self.images_path = self.images_path.replace(" ", "_")
        page = self.cut_region(reader, side)
        path_to_pdf = self.save_cropped_pdf(page)
        image = self.pdf_to_image(path_to_pdf)
        image = self.threshold(image)
        print(self.find_qrcode(image))
        elapsed = timeit.default_timer() - start_time
        print(f"Tempo total: {elapsed}s")

    @staticmethod
    def cut_region(reader, side):

        # Pegando a primeira página do pdf
        page = reader.getPage(0)
        pdf_size = page.mediaBox

        half_pdf_y = int((pdf_size[3] * 8) / 10) # Corta 80% do pdf
        half_pdf_x = int((pdf_size[2] * 8) / 10) # Corta 80% do pdf

        if side == 'right':
            page.mediaBox.upperRight = (page.mediaBox.getUpperRight_x(), page.mediaBox.getUpperRight_y())
            page.mediaBox.lowerLeft = (page.mediaBox.getLowerLeft_x() + half_pdf_x,
                                       page.mediaBox.getLowerLeft_y() + half_pdf_y)
        # page.cropBox.upperLeft = (400,400)
        elif side == 'left':

            page.mediaBox.upperRight = (page.mediaBox.getUpperRight_x() - half_pdf_x, page.mediaBox.getUpperRight_y())
            page.mediaBox.lowerLeft = (page.mediaBox.getLowerLeft_x(), page.mediaBox.getLowerLeft_y() + half_pdf_y)
        else:
            print("Todo o pdf será convertido para imagem")

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

    @staticmethod
    def pdf_to_image(path_to_pdf):
        # pdf_image = convert_from_path(path_to_pdf, poppler_path=os.path.join('..', 'venv', 'poppler-0.68.0', \
        # 'bin'), dpi=1000) !NOTE É PRECISO DEFINIR O DIRETÓRIO DO POPPLER NO WINDOWS OU INSTALAR NO LINUX
        pdf_image = convert_from_path(
            path_to_pdf,
            poppler_path=os.path.join(settings.BASE_DIR, 'venv', 'poppler-0.68.0', 'bin'),
            dpi=1000)

        # !TODO Ver como não salvar a imagem e pegar o array dela para continuar o tratamento

        # Saving image (Optional)
        # file_name = "converted_image.png"
        # converted_image_path = os.path.join(self.images_path, file_name)
        # for image in pdf_image:
        #     image.save(converted_image_path)

        image = np.asarray(pdf_image.pop())

        return image

    def threshold(self, image):
        # !TODO Verificar se o
        # opencv 4.5.1 precisa de cv2.IMREAD_COLOR
        image = cv2.UMat(image)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        for i in range(0, 1):
            image = cv2.medianBlur(image, 5)
            _, image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)

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
            # qr_code_detector = cv2.QRCodeDetector()
            # decoded_text, points, _ = qr_code_detector.detectAndDecode(image)
            # if decoded_text is not None:
            #      self.decoded_text = decoded_text
            #      return self.decoded_text
            # else:
            #     self.decoded_text = None
            return "QRCode not found"

    def get_decoded_text(self):
        return self.decoded_text

    def get_images_path(self):
        return self.images_path

# ManageQrCode("C:\\Users\\Rafael\\Downloads\\2011181654140001.pdf")
