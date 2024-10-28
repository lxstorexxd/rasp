import aiohttp
import asyncio
import hashlib
import os
from datetime import datetime
from typing import List, Optional

class ScheduleChecker:
    def __init__(self, urls: List[str], download_folder: str = "schedule"):
        """
        Инициализация класса для проверки изменений расписания по нескольким ссылкам.
        
        :param urls: Список URL файлов расписания
        :param download_folder: Папка для хранения загруженных файлов
        """
        self.urls = urls
        self.download_folder = download_folder
        self.last_checksums = {url: None for url in urls}
        
        # Создаем папку для хранения файлов, если она не существует
        os.makedirs(self.download_folder, exist_ok=True)

    async def download_file(self, url: str) -> bytes:
        """
        Асинхронно загружает файл по указанному URL.
        
        :param url: URL файла
        :return: Содержимое файла в виде байтов
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    return await response.read()
        except aiohttp.ClientError as e:
            print(f"Ошибка загрузки файла по адресу {url}: {e}")
            return b""

    def calculate_checksum(self, data: bytes) -> str:
        """
        Вычисляет MD5 контрольную сумму для переданных данных.
        
        :param data: Данные для вычисления контрольной суммы
        :return: MD5 хэш строки
        """
        return hashlib.md5(data).hexdigest()

    def save_file(self, data: bytes, url: str) -> str:
        """
        Сохраняет загруженный файл в папку с текущей датой и временем в названии.
        
        :param data: Содержимое файла
        :param url: URL файла для создания уникального имени
        :return: Путь к сохраненному файлу
        """
        # Генерируем имя файла на основе текущей даты, времени и имени файла из URL
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = url.split("/")[-1].replace('.pdf', '')
        file_path = os.path.join(self.download_folder, f"{filename}_{timestamp}.pdf")
        
        # Сохраняем новый файл
        with open(file_path, "wb") as file:
            file.write(data)
        print(f"Сохранен новый файл: {file_path}")

        return file_path

    async def has_file_changed(self, url: str) -> bool:
        """
        Проверяет, изменился ли файл расписания по указанному URL.
        
        :param url: URL файла для проверки
        :return: True, если файл изменился, иначе False
        """
        file_data = await self.download_file(url)
        if not file_data:
            print("Файл не загружен, повторите попытку позже.")
            return False
        
        current_checksum = self.calculate_checksum(file_data)
        last_checksum = self.last_checksums.get(url)
        
        if last_checksum is None:
            # Если контрольная сумма отсутствует, инициализируем её
            self.last_checksums[url] = current_checksum
            print(f"Контрольная сумма для {url} инициализирована.")
            self.save_file(file_data, url)
            return False  # Первый запуск: изменений нет, только инициализация
        
        if current_checksum != last_checksum:
            # Обновляем контрольную сумму и сохраняем новый файл
            self.last_checksums[url] = current_checksum
            self.save_file(file_data, url)
            print(f"Обнаружено изменение в файле: {url}")
            return True
        
        print(f"Файл не изменился: {url}")
        return False

    async def check_all_files(self):
        """
        Проверяет все файлы из списка URL на наличие изменений.
        """
        tasks = [self.has_file_changed(url) for url in self.urls]
        results = await asyncio.gather(*tasks)
        if any(results):
            print("Некоторые файлы расписания обновлены!")
        else:
            print("Изменений в файлах расписания не обнаружено.")

async def main():
    schedule_urls = [
        "https://rasp.vksit.ru/spo.pdf",
        "https://rasp.vksit.ru/npo.pdf"
    ]
    checker = ScheduleChecker(schedule_urls)

    # Циклическая проверка обновлений
    while True:
        await checker.check_all_files()
        await asyncio.sleep(30)  # Проверка каждые 60 минут

# Запуск асинхронного цикла
asyncio.run(main())
