import aiohttp
import asyncio
import hashlib
import os
from datetime import datetime
from typing import Optional

class ScheduleChecker:
    def __init__(self, url: str, download_folder: str = "schedule"):
        """
        Инициализация класса для проверки изменений расписания.
        
        :param url: URL файла расписания
        :param download_folder: Папка для хранения загруженных файлов
        """
        self.url = url
        self.download_folder = download_folder
        self.last_checksum: Optional[str] = None
        
        # Создаем папку для хранения файлов, если она не существует
        os.makedirs(self.download_folder, exist_ok=True)

    async def download_file(self) -> bytes:
        """
        Асинхронно загружает файл по указанному URL.
        
        :return: Содержимое файла в виде байтов
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, timeout=10) as response:
                    response.raise_for_status()
                    return await response.read()
        except aiohttp.ClientError as e:
            print(f"Ошибка загрузки файла: {e}")
            return b""

    def calculate_checksum(self, data: bytes) -> str:
        """
        Вычисляет MD5 контрольную сумму для переданных данных.
        
        :param data: Данные для вычисления контрольной суммы
        :return: MD5 хэш строки
        """
        return hashlib.md5(data).hexdigest()

    def save_file(self, data: bytes) -> str:
        """
        Сохраняет загруженный файл в папку с текущей датой и временем в названии.
        
        :param data: Содержимое файла
        :return: Путь к сохраненному файлу
        """
        # Генерируем имя файла на основе текущей даты и времени
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(self.download_folder, f"schedule_{timestamp}.xls")
        
        # Сохраняем новый файл
        with open(file_path, "wb") as file:
            file.write(data)
        print(f"Сохранен новый файл: {file_path}")

        return file_path

    async def has_file_changed(self) -> bool:
        """
        Проверяет, изменился ли файл расписания.
        
        :return: True, если файл изменился, иначе False
        """
        file_data = await self.download_file()
        if not file_data:
            print("Файл не загружен, повторите попытку позже.")
            return False
        
        current_checksum = self.calculate_checksum(file_data)
        if self.last_checksum is None:
            self.last_checksum = current_checksum
            print("Контрольная сумма инициализирована.")
            return False  # Первый запуск: изменений нет, только инициализация
        
        if current_checksum != self.last_checksum:
            self.last_checksum = current_checksum
            self.save_file(file_data)  # Сохраняем новый файл
            print("Обнаружено изменение в файле.")
            return True
        
        print("Файл не изменился.")
        return False

async def main():
    schedule_url = "https://rasp.vksit.ru/spo.pdf"
    checker = ScheduleChecker(schedule_url)

    # Циклическая проверка обновлений
    while True:
        if await checker.has_file_changed():
            print("Расписание обновлено и сохранено!")
        else:
            print("Расписание не изменилось.")
        await asyncio.sleep(10)  # Проверка каждые 60 минут

# Запуск асинхронного цикла
asyncio.run(main())
