from PyPDF2 import PdfFileReader, PdfFileWriter
from pdf2image import convert_from_path, convert_from_bytes
from django.conf import settings
import cv2
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

        print(os.path.join(settings.BASE_DIR, 'venv', 'poppler-0.68.0', 'bin'))
        pdf_image = convert_from_path('out_file.pdf', poppler_path=os.path.join(settings.BASE_DIR, 'venv', 'poppler-0.68.0', 'bin'), dpi=600)

        # !TODO Ver como não salvar a imagem e pegar o array dela para continuar o tratamento
        for image in pdf_image:
            image.save("converted_image.jpg", "JPEG")

        # !TODO Verificar se o opencv 4.5.1 precisa de cv2.IMREAD_COLOR
        image = cv2.imread("converted_image.jpg", cv2.IMREAD_COLOR)
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        image = cv2.UMat(image)

        # Continuar com OTSU
        _, image = cv2.threshold(image, 127, 255, cv2.THRESH_OTSU)

        # Salvando sample !TODO criar pasta samples
        cv2.imwrite("converted_image_otsu.jpg", image)

        # Função nativa
        detector = cv2.QRCodeDetector()

        # Transformando o cv:Mat para um array (para desenhar as linhas)
        # O QRCodeDetector funciona com cv:UMat
        image = image.get()
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
                cv2.line(image, tuple(points[i]), tuple(points[next_point_i]), (255, 0, 0), 5)

            # Voltando para UMat, pois só salva assim
            image = cv2.UMat(image)
            print(decoded_text)
            cv2.imwrite("image_qrcode.jpg", image)

        else:
            print("QR code not detected")

        # page.cropBox.setLowerLeft((42, 115))
        # page.cropBox.setUpperRight((500, 245))
        # writer.addPage(page)
