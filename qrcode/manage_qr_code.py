from PyPDF2 import PdfFileReader, PdfFileWriter
from pdf2image import convert_from_path, convert_from_bytes
from django.conf import settings
import cv2
import numpy as np
import os


class ManageQrCode:
    images_path = None
    decoded_text = None

    def __init__(self, pdf_path):
        reader = PdfFileReader(pdf_path, 'rb')
        self.images_path = pdf_path.split(".")[0]

        page = self.cut_region(reader)
        path_to_pdf = self.save_cropped_pdf(page)
        image = self.pdf_to_image(path_to_pdf)
        image = self.threshold(image)
        print(self.find_qrcode(image))

    def cut_region(self, reader):

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

        os.mkdir(self.images_path)

        cropped_pdf_path = os.path.join(self.images_path, 'cropped_pdf.pdf')
        with open(cropped_pdf_path, 'wb') as cropped_pdf:
            writer.write(cropped_pdf)
        return cropped_pdf_path

    def pdf_to_image(self, path_to_pdf):
        pdf_image = convert_from_path(path_to_pdf, poppler_path=os.path.join(settings.BASE_DIR, 'venv', 'poppler-0.68.0', 'bin'), dpi=600)

        # !TODO Ver como não salvar a imagem e pegar o array dela para continuar o tratamento
        converted_image_path = os.path.join(self.images_path, 'converted_image.png')
        for image in pdf_image:
            image.save(converted_image_path)
        image = cv2.imread(converted_image_path, cv2.IMREAD_COLOR)
        return image

    def threshold(self, image):
        # !TODO Verificar se o opencv 4.5.1 precisa de cv2.IMREAD_COLOR
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = cv2.UMat(image)
        _, image = cv2.threshold(image, 127, 255, cv2.THRESH_OTSU)

        converted_otsu_image_path = os.path.join(self.images_path, 'converted_otsu_image.png')
        cv2.imwrite(converted_otsu_image_path, image)

        return image.get()

    def find_qrcode(self, image):
        detector = cv2.QRCodeDetector()
        decoded_text, points, _ = detector.detectAndDecode(image)

        if points is not None:
            # QR Code detected handling code
            # points é uma tupla de (1,4,2) e precisa ser acessado a partir do primeiro objeto dela, por isso points[0]
            points = points[0]
            number_of_points = len(points)

            # Mudando cor apenas para pintar (luxo)
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

            for i in range(number_of_points):
                next_point_i = (i + 1) % number_of_points
                shift = (5, 5)
                cv2.line(image, tuple(points[i]), tuple(points[next_point_i]), (255, 0, 0), 5)

            # Voltando para UMat, pois só salva assim nessa versão
            image = cv2.UMat(image)
            # print(decoded_text)
            qrcode_image_path = os.path.join(self.images_path, "qrcode_image.jpg")
            cv2.imwrite(qrcode_image_path, image)
            self.decoded_text = decoded_text
            return decoded_text

        return None

    def get_decoded_text(self):
        return self.decoded_text

    def get_images_path(self):
        return self.images_path

# ManageQrCode("../media/Evolução Assinada.pdf")