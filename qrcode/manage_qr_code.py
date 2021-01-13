from PyPDF2 import PdfFileReader, PdfFileWriter
from pdf2image import convert_from_path, convert_from_bytes
from django.conf import settings
import cv2
import numpy as np
import os
from PIL import Image
import pyzbar.pyzbar as pyzbar
import timeit
import glob
import shutil
from PyPDF2.utils import PyPdfError


class ManageQrCode:
    pdf_path = None
    images_path = None
    decoded_text = None
    total_time = 0
    reader = None
    page = None
    image = None
    half_image = None
    cropped_pdf = None

    # 94% DE acurácia com essas configurações
    rotate = [False, True]
    degrees = [0, 1, 2, 358, 359]
    sides = ['right', 'left', 'half']
    region_to_cut = [8, 6]

    # Configs for testing
    # rotate = [False]
    # degrees = [0, 2, 358]
    # sides = ['right']
    # region_to_cut = [8]

    # 'right', 9, False

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.create_dir()
        try:
            self.run()
        except PyPdfError:
            raise PyPdfError

    def run(self):
        start = timeit.default_timer()

        for region in self.region_to_cut:
            for rotate in self.rotate:
                for side in self.sides:
                    print(side, self.degrees, region, "rotated" if rotate else "not rotated")
                    self.reader = None
                    try:
                        self.reader = PdfFileReader(pdf_file)
                    except PyPdfError:
                        print("PDF INVÁLIDO!")
                        with open(self.images_path + "\\..\\" + "corrupted_log.txt", "a") as corrupted_log:
                            corrupted_log.write(self.pdf_path + "\n")

                        raise PyPdfError

                    self.cut_region(side=side, rotate=rotate, region=region)
                    self.save_cropped_pdf()
                    self.pdf_to_image()

                    for degree in self.degrees:
                        self.threshold(degree=degree)
                        self.find_qrcode()
                        self.image = cv2.UMat(self.image)
                        if self.decoded_text is not None:
                            self.log()
                            self.total_time = timeit.default_timer() - start
                            return

        self.log()
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

    def save_cropped_pdf(self):
        writer = PdfFileWriter()
        writer.addPage(self.page)
        cropped_pdf_path = os.path.join(self.images_path, 'cropped_pdf.pdf')
        with open(cropped_pdf_path, 'wb') as cropped_pdf:
            writer.write(cropped_pdf)
        self.cropped_pdf = cropped_pdf_path

    def pdf_to_image(self):
        pdf_image = convert_from_path(self.cropped_pdf, poppler_path=os.path.join(
            '..', 'venv', 'poppler-0.68.0', 'bin'), dpi=1000)

        self.image = cv2.UMat(np.asarray(pdf_image.pop()))
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

    def threshold(self, degree):
        for i in range(0, 1):
            self.image = cv2.medianBlur(self.image, 5)
            _, self.image = cv2.threshold(
                self.image, 127, 255, cv2.THRESH_BINARY)

        file_name = 'image_threshold' + f"_{degree}degrees"+ '.png'
        image_threshold_path = os.path.join(self.images_path, file_name)

        image_pil = Image.fromarray(self.image.get())
        image_pil = image_pil.rotate(degree % 360)
        image_pil.save(image_threshold_path)

        self.image = np.asarray(image_pil)

    def find_qrcode(self):
        symbols = [pyzbar.ZBarSymbol.QRCODE]
        decoded_objects = pyzbar.decode(self.image)
        qr_code_detector_cv2 = cv2.QRCodeDetector()
        try:
            decoded_text_cv2, points, _ = qr_code_detector_cv2.detectAndDecode(self.image)
        except:
            decoded_text_cv2 = ""
            pass
        if decoded_text_cv2 != "":
            print("DECODED-OPENCV: ", decoded_text_cv2)

        for obj in decoded_objects:
            (x, y, w, h) = obj.rect
            shift = 5
            roi = self.image[y-shift:y+h+shift, x-shift:x+w+shift]
            file_name = 'qr_code_detected.png'
            # cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            qr_code_image_path = os.path.join(self.images_path, file_name)
            image4save = Image.fromarray(roi)
            image4save.save(qr_code_image_path)


        if len(decoded_text_cv2) != 0 and False:
            (x, y, w, h) = points
            shift = 5
            roi = self.image[y - shift:y + h + shift, x - shift:x + w + shift]
            file_name = 'qr_code_detected.png'
            # cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            qr_code_image_path = os.path.join(self.images_path, file_name)
            image4save = Image.fromarray(roi)
            image4save.save(qr_code_image_path)

        if decoded_objects:
            self.decoded_text = decoded_objects[0].data.decode("utf-8")
            print("DECODED-ZBAR: " + self.decoded_text)
            return self.decoded_text
        elif len(decoded_text_cv2) != 0:
            print("---only detected by opencv--")
            self.decoded_text = decoded_text_cv2

            return self.decoded_text
        else:
            return None

    def log(self):
        print("Salvando log dos arquivos")
        with open(self.images_path + "\\..\\" + "log.txt", "a") as file:
            log_text = "CAMINHO DO ARQUIVO: " + self.images_path + ".pdf\n"
            if self.decoded_text is not None:
                log_text += "DECODED TEXT:" + str(self.decoded_text) + "\n"
            else:
                log_text += "DECODED TEXT: QR CODE NÃO ENCONTRADO\n"

            log_text += "TEMPO DECORRIDO (total): " + \
                str(self.total_time) + "\n"
            file.write(log_text)

        if self.decoded_text is None:
            with open(self.images_path + "\\..\\" + "log_failed.txt", "a") as file_fail:
                log_text_failed = "CAMINHO DO ARQUIVO: " + self.images_path + ".pdf\n"
                file_fail.write(log_text_failed)

    def create_dir(self):
        self.images_path = self.pdf_path.split(".pdf")[0]
        try:
            os.mkdir(self.images_path)
        except:
            pass

    def cut_half_image(self):
        """
        Need to be an nparray type
        :return:
        """
        image = self.image.get() # note: image needs to be in the opencv format
        height, width = image.shape
        self.half_image = image[0:int(height/2), 0:int(width)]
        self.half_image = cv2.UMat(self.half_image)

    def get_decoded_text(self):
        return self.decoded_text

    def get_images_path(self):
        return self.images_path


# found = 0
# not_found = 0
path = ("C:\\Users\\Rafael\\Documents\\PDF_QRCODE\\enviados\\")
temp = "*\\"
dirs = glob.glob(path + temp)
dirs = list(map(lambda d: d[:-1] + ".pdf", dirs))

files_pdf = glob.glob(path + "*.pdf")
filtered_files = list(filter(lambda f: f not in dirs, files_pdf))
# filtered_files = [f for f in files_pdf if f not in dirs]


total = len(files_pdf)
found = len(dirs)
not_found = 0
start_time = timeit.default_timer()
for pdf_file in filtered_files:
    print("Decoding: " + pdf_file)
    try:
        qr_code = ManageQrCode(pdf_path=pdf_file)
    except PyPdfError:
        # Não contabiliza o pdf corrompido, mas guarda em corrupted_log
        continue

    if qr_code.get_decoded_text() is not None:
        found += 1
    else:
        not_found += 1

    print("TEMPO PARA LER O PDF: " + "{:.2f}".format(qr_code.total_time) + "s" )

    print(f"Quantidade de pdfs reconhecidos: {found}")
    print(f"Quantidade de pdfs não reconhecidos: {not_found} ")
    elapsed = timeit.default_timer() - start_time
    with open(pdf_file.split(".pdf")[0] + "\\..\\" + "log.txt", "a") as file:
        file.write("TEMPO PARA LER O PDF: " + "{:.2f}".format(qr_code.total_time) + "s\n" +
                   f"TOTAL DE PDFS DECODIFICADOS: {found}\n"
                   f"TOTAL DE PDFS NÃO IDENTIFICADOS: {not_found}\n"
                   f"TEMPO ACUMULADO: {elapsed}\n"
                   f"-------------------------------\n")
print(f"ACURÁCIA: {found*100/(found+not_found)}")
with open(path + "\\" + "log.txt", "a") as file:
    file.write(f"ACURÁCIA: {found*100/(found+not_found)}")


'''
file1 = open("C:\\Users\\Rafael\\Documents\\PDF_QRCODE\\enviados\\log_failed.txt", 'r')
file2 = open("C:\\Users\\Rafael\\Documents\\PDF_QRCODE\\enviados\\corrupted_log.txt", 'r')

Lines = file1.readlines()
Lines2 = file2.readlines()

for line in Lines2:
    try:
        os.remove(line[:-1])
    except:
        print(f"File {os.path.split(line)[1]} not found")
        pass


for line in Lines:
    path = line.split("CAMINHO DO ARQUIVO: ")[1][:-1]
    dir_path = path.split(".pdf")[0]
    try:
        shutil.rmtree(dir_path)
    except:
        print(f"DIR -> {os.path.split(dir_path)[1]} not found")
        pass
    # shutil.move(path, os.path.split(path)[0] + "\\FAILED\\" + os.path.split(path)[1])
    # os.replace(path, os.path.split(path)[0] + "\\FAILED\\" + os.path.split(path)[1])
'''