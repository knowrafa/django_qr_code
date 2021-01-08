from PyPDF2 import PdfFileReader, PdfFileWriter
from pdf2image import convert_from_path, convert_from_bytes
from django.conf import settings
import cv2
import pyzbar.pyzbar as pyzbar
import numpy as np
import os


class ManageQrCode():

    def cut_region(pdf_archive):
        """
        Recebe um arquivo pdf para poder cortar (link para o arquivo
        :param pdf_archive: link para o arquivo enviado em /media/
        :return: novo arquivo pdf com a região cortada
        """

        reader = PdfFileReader(pdf_archive, 'rb')
        output = PdfFileWriter()

        # Pegando a primeira página do pdf

        page = reader.getPage(0)
        pdf_size = page.mediaBox

        page.mediaBox.upperRight = (page.mediaBox.getUpperRight_x(), page.mediaBox.getUpperRight_y())

        # Quero entender como essa magia funciona
        value = int((pdf_size[3] * 8) / 10)
        value_b = int((pdf_size[2] * 8) / 10)

        page.mediaBox.lowerLeft = (page.mediaBox.getLowerLeft_x() + value_b, page.mediaBox.getLowerLeft_y() + value)
        # page.cropBox.upperLeft = (400,400)

        writer = PdfFileWriter()
        writer.addPage(page)

        with open('out_file.pdf', 'wb') as outfp:
            writer.write(outfp)

        # print(os.path.join(settings.BASE_DIR, 'venv', 'poppler-0.68.0', 'bin'))
        # pdf_image = convert_from_path('out_file.pdf', poppler_path=os.path.join(settings.BASE_DIR, 'venv', 'poppler-0.68.0', 'bin'), dpi=600)
        pdf_image = convert_from_path('out_file.pdf', poppler_path=os.path.join('..', 'venv', 'poppler-0.68.0', 'bin'),
                                      dpi=1000)

        # !TODO Ver como não salvar a imagem e pegar o array dela para continuar o tratamento
        for image in pdf_image:
            image.save("converted_image.jpg", "JPEG")

        # !TODO Verificar se o opencv 4.5.1 precisa de cv2.IMREAD_COLOR
        # image = cv2.UMat(image)

        kernel =  cv2.getStructuringElement(cv2.MORPH_CROSS, (5,5))
        # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))

        image = cv2.imread("converted_image.jpg", cv2.IMREAD_COLOR)


        # image = cv2.GaussianBlur(image, (5, 5), 0)
        #sharpen_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        #image = cv2.filter2D(image, -1, sharpen_kernel)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        for i in range(0, 1):
            image = cv2.medianBlur(image, 5)
            _, image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)

        # image = cv2.bilateralFilter(image, 9, 75, 75)
        cv2.imwrite("blurred_image.jpg", image)
        image = cv2.UMat(image)

        # Função nativa
        detector = cv2.QRCodeDetector()

        # Transformando o cv:Mat para um array (para desenhar as linhas)
        # O QRCodeDetector funciona com cv:UMat
        image = image.get()


        decodedObjects = pyzbar.decode(image)
        for obj in decodedObjects:
            print('Type : ', obj.type)
            print('Data : ', obj.data, '\n')

        print(decodedObjects)

# os.path
ManageQrCode.cut_region("C:\\Users\\Rafael\\Downloads\\201212173714.pdf")