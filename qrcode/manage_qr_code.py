from PyPDF2 import PdfFileReader, PdfFileWriter
from pdf2image import convert_from_path, convert_from_bytes
from django.conf import settings
import os


class ManageQrCode():

    def cut_region(pdf_archive):
        '''
        Recebe um arquivo pdf para poder cortar (link para o arquivo
        :param pdf_archive: link para o arquivo enviado em /media/
        :return: novo arquivo pdf com a região cortada
        '''
        reader = PdfFileReader(pdf_archive, 'rb')
        output = PdfFileWriter()
        # Pegando a primeira página do pdf
        page = reader.getPage(0)
        pdfsize = page.mediaBox

        # Y, X
        pdf_center_coordinate = (int(pdfsize[2]/2), int(pdfsize[3]/2))
        # aparentemente funciona em Y, X
        pdf_lower_left = (pdf_center_coordinate[1], 0)
        pdf_lower_right = (pdfsize[2]-1, 0)
        pdf_upper_left = pdf_center_coordinate
        pdf_upper_right = (pdfsize[2]-1, pdf_center_coordinate[0])
        # Centro
        '''
        page.cropBox.setLowerRight(pdf_lower_right)
        page.cropBox.setLowerLeft(pdf_lower_left)
        page.cropBox.setUpperRight(pdf_upper_right)
        page.cropBox.setUpperLeft(pdf_upper_left)

        page_crop = page.cropBox

        page.pdfsize = page.cropBox
        page.mediaBox = page_crop
        page.cropBox = page_crop
        page.trimBox = page_crop
        page.artBox = page_crop
        page.creedBox = page_crop
        page.bleedBox = page_crop
        '''


        # page.cropBox.lowerLeft = (pdfsize[1],pdfsize[0])
        # page.cropBox.upperRight = pdf_center_coordinate

        page.mediaBox.upperRight = (page.mediaBox.getUpperRight_x(), page.mediaBox.getUpperRight_y())
        # value = int(pdfsize[3]*0.9)
        # print(type(pdfsize[3]), (pdfsize[3]*8)/10)
        value = int((pdfsize[3]*8)/10)
        value_b = int((pdfsize[2]*8)/10)
        print(page.mediaBox.getLowerLeft_x())
        print(page.mediaBox.getLowerLeft_y())
        page.mediaBox.lowerLeft = (page.mediaBox.getLowerLeft_x() + value_b, page.mediaBox.getLowerLeft_y() + value)
        # page.cropBox.upperLeft = (400,400)

        writer = PdfFileWriter()
        writer.addPage(page)


        with open('out_file.pdf', 'wb') as outfp:
            writer.write(outfp)
        print(os.path.join(settings.BASE_DIR, 'venv', 'poppler-0.68.0', 'bin'))
        pdf_image = convert_from_path('out_file.pdf', poppler_path=os.path.join(settings.BASE_DIR, 'venv', 'poppler-0.68.0', 'bin'), dpi=500)

        for image in pdf_image:
            image.save("converted_image.png", "JPEG")
        # page.cropBox.setLowerLeft((42, 115))
        # page.cropBox.setUpperRight((500, 245))
        # writer.addPage(page)
