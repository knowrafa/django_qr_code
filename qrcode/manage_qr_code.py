import logging
from base64 import b64encode
from sys import platform

import cv2
import io
import numpy as np
import os
import pyzbar.pyzbar as pyzbar
import timeit
from PIL import Image
from PyPDF2 import PdfFileReader, PdfFileWriter
from PyPDF2.utils import PyPdfError
from django.conf import settings
from pdf2image import convert_from_bytes

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)


class ManageQrCode:
    pdf_path = None
    images_path = None
    decoded_text = None
    total_time = 0
    reader = None
    page = None
    image = None
    half_image = None
    cropped_bytes_pdf = None
    qr_code_image64 = None

    # Configurações (podem ser alteradas)
    rotate = [False, True]
    degrees = [0, 1, 2, 358, 359]
    sides = ['left', 'half', 'right']
    region_to_cut = [8]

    def __init__(self, pdf_path=None):

        self.pdf_path = pdf_path
        try:
            self.run()
        except PyPdfError:
            raise PyPdfError
        except FileNotFoundError:
            raise FileNotFoundError
        except PermissionError:
            raise PermissionError

    def run(self):
        start = timeit.default_timer()

        for region in self.region_to_cut:
            for rotate in self.rotate:
                for side in self.sides:
                    self.reader = None
                    try:
                        self.reader = PdfFileReader(self.pdf_path)
                    except PyPdfError:
                        raise PyPdfError
                    except FileNotFoundError:
                        raise FileNotFoundError
                    except PermissionError:
                        raise PermissionError

                    self.cut_region(side=side, rotate=rotate, region=region)
                    self.save_cropped_bytes_pdf()
                    self.pdf_to_image()

                    for degree in self.degrees:
                        self.threshold(degree=degree)
                        self.find_qrcode()
                        self.image = cv2.UMat(self.image)
                        if self.decoded_text is not None:
                            self.total_time = timeit.default_timer() - start
                            return

        self.total_time = timeit.default_timer() - start

    def cut_region(self, side, rotate, region):
        page = self.reader.getPage(0)

        if rotate:
            page.rotateCounterClockwise(180)

        region = region
        pdf_size = page.mediaBox

        half_pdf_y = int((pdf_size[3] * region) / 10)  # Corta 80% do pdf
        half_pdf_x = int((pdf_size[2] * region) / 10)  # Corta 80% do pdf

        if not rotate:
            if side == 'right':
                page.mediaBox.upperRight = (
                    page.mediaBox.getUpperRight_x(), page.mediaBox.getUpperRight_y())
                page.mediaBox.lowerLeft = (page.mediaBox.getLowerLeft_x() + half_pdf_x,
                                           page.mediaBox.getLowerLeft_y() + half_pdf_y)
            elif side == 'left':
                page.mediaBox.upperRight = (page.mediaBox.getUpperRight_x(
                ) - half_pdf_x, page.mediaBox.getUpperRight_y())
                page.mediaBox.lowerLeft = (page.mediaBox.getLowerLeft_x(
                ), page.mediaBox.getLowerLeft_y() + half_pdf_y)
            elif side == 'half':
                page.mediaBox.upperRight = (page.mediaBox.getUpperRight_x(
                ), page.mediaBox.getUpperRight_y())
                page.mediaBox.lowerLeft = (page.mediaBox.getLowerLeft_x(
                ), page.mediaBox.getLowerLeft_y()+half_pdf_y)
        elif rotate:
            if side == 'right':
                page.mediaBox.upperRight = (page.mediaBox.getUpperRight_x(
                ), page.mediaBox.getUpperRight_y() - half_pdf_y)
                page.mediaBox.lowerLeft = (page.mediaBox.getLowerLeft_x(
                ) + half_pdf_x, page.mediaBox.getLowerLeft_y())
            elif side == 'left':
                page.mediaBox.upperRight = (page.mediaBox.getUpperRight_x(
                ) - half_pdf_x, page.mediaBox.getUpperRight_y() - half_pdf_y)
                page.mediaBox.lowerLeft = (
                    page.mediaBox.getLowerLeft_x(), page.mediaBox.getLowerLeft_y())
            elif side == 'half':
                page.mediaBox.upperRight = (page.mediaBox.getUpperRight_x(
                ), page.mediaBox.getUpperRight_y() - half_pdf_y)
                page.mediaBox.lowerLeft = (page.mediaBox.getLowerLeft_x(
                ), page.mediaBox.getLowerLeft_y())
        else:
            print("Todo o pdf será convertido para imagem")

        # return page
        self.page = page

    def save_cropped_bytes_pdf(self):
        writer = PdfFileWriter()
        self.cropped_bytes_pdf = io.BytesIO()
        writer.addPage(self.page)
        writer.write(self.cropped_bytes_pdf)
        # Quesito de configuração, volta o io para o começo
        self.cropped_bytes_pdf.seek(0)
        self.cropped_bytes_pdf = self.cropped_bytes_pdf.read()

    def pdf_to_image(self):
        if platform == 'linux' or platform == 'linux2':
            pdf_image = convert_from_bytes(self.cropped_bytes_pdf, dpi=1000)
        else: # platform == 'win32':
            pdf_image = convert_from_bytes(self.cropped_bytes_pdf,
                                           poppler_path=os.path.join(settings.BASE_DIR, 'venv', 'poppler-0.68.0',
                                                                     'bin'),
                                           dpi=1000)
        self.image = cv2.UMat(np.asarray(pdf_image.pop()))
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

    def threshold(self, degree):
        for i in range(0, 1):
            self.image = cv2.medianBlur(self.image, 5)
            _, self.image = cv2.threshold(
                self.image, 127, 255, cv2.THRESH_BINARY)
        image_pil = Image.fromarray(self.image.get())
        image_pil = image_pil.rotate(degree % 360)

        self.image = np.asarray(image_pil)

    def find_qrcode(self):
        symbols = [pyzbar.ZBarSymbol.QRCODE]
        decoded_objects = pyzbar.decode(self.image)
        qr_code_detector_cv2 = cv2.QRCodeDetector()
        try:
            decoded_text_cv2, points, _ = qr_code_detector_cv2.detectAndDecode(self.image)
        except all:
            decoded_text_cv2 = ""
            pass

        for obj in decoded_objects:
            (x, y, w, h) = obj.rect
            shift = 5
            roi = self.image[y-shift:y+h+shift, x-shift:x+w+shift]
            buff = io.BytesIO()
            roi_img = Image.fromarray(roi)
            roi_img.thumbnail([320, 240], Image.ANTIALIAS)
            try:
                roi_img.save(buff, format='PNG')
            except AttributeError:
                print("Erro no arquivo: " + self.pdf_path)
                raise AttributeError
            self.qr_code_image64 = b64encode(buff.getvalue())
        if decoded_objects:
            self.decoded_text = decoded_objects[0].data.decode("utf-8")
            return self.decoded_text
        elif len(decoded_text_cv2) != 0:
            self.decoded_text = decoded_text_cv2

            return self.decoded_text
        else:
            return None

    def get_decoded_text(self):
        return self.decoded_text

    def get_images_path(self):
        return self.images_path
