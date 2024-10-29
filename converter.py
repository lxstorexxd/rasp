import fitz
from PIL import Image, ImageChops
import os

class PDFConverter:
    def __init__(self, pdf_path: str, output_folder: str, dpi: int = 300, padding: int = 10):
        """
        Инициализирует класс PDFConverter для преобразования PDF в изображения.

        :param pdf_path: Путь к PDF-файлу
        :param output_folder: Папка для сохранения изображений
        :param dpi: Разрешение изображений (точек на дюйм)
        :param padding: Отступ, добавляемый вокруг содержимого после обрезки
        """
        self.pdf_path = pdf_path
        self.output_folder = output_folder
        self.dpi = dpi
        self.padding = padding

        # Создаем папку для изображений, если она не существует
        os.makedirs(self.output_folder, exist_ok=True)

    def trim_whitespace(self, img: Image.Image) -> Image.Image:
        """
        Обрезает пустые поля изображения и добавляет отступы.

        :param img: Изображение для обработки
        :return: Обрезанное изображение с отступами
        """
        bg = Image.new(img.mode, img.size, img.getpixel((0, 0)))
        diff = ImageChops.difference(img, bg)
        bbox = diff.getbbox()

        if bbox:
            cropped_img = img.crop(bbox)
            width, height = cropped_img.size
            padded_img = Image.new(img.mode, (width + 2 * self.padding, height + 2 * self.padding), img.getpixel((0, 0)))
            padded_img.paste(cropped_img, (self.padding, self.padding))
            return padded_img
        return img

    def convert_to_images(self):
        """
        Преобразует страницы PDF в изображения, обрезает пустые поля и сохраняет с отступами.
        """
        # Открываем PDF-документ
        doc = fitz.open(self.pdf_path)
        print(f"Открыт файл PDF: {self.pdf_path}")

        for page_num in range(len(doc)):
            # Загружаем страницу и преобразуем в изображение с высоким разрешением
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=self.dpi)
            
            # Конвертируем изображение в формат Pillow для обработки
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Обрезаем пустые поля и добавляем отступ
            trimmed_img = self.trim_whitespace(img)
            
            # Генерируем имя файла для сохранения
            output_path = os.path.join(self.output_folder, f"{os.path.basename(self.pdf_path).replace('.pdf', '')}_page_{page_num + 1}.png")
            trimmed_img.save(output_path, "PNG")
            print(f"Сохранено изображение: {output_path}")
        print("Конвертация, обрезка и добавление отступов завершены!")