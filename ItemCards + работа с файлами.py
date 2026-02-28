import decimal
import json
import os
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import csv
from decimal import Decimal


class ItemCard:
    """
    Класс карточки товара.
    """

    def __init__(self,
                 name: str,
                 quantity: int,
                 state: str,
                 supplier: str,
                 manufacturer: str,
                 price: Decimal,
                 location: str,
                 category: str,
                 receipt_date: str,
                 warranty_months: int) -> None:
        """
        Инициализация карточки товара.

        :param name: Наименование товара.
        :param quantity: Количество товара на складе.
        :param state: Состояние товара (отличное, хорошее и т.д.).
        :param supplier: Поставщик товара.
        :param manufacturer: Производитель товара.
        :param price: Стоимость товара.
        :param location: Местоположение товара на складе.
        :param category: Категория товара.
        :param receipt_date: Дата поступления товара.
        :param warranty_months: Гарантийный срок в месяцах.
        """

        self.name = name
        self.quantity = quantity
        self.state = state
        self.supplier = supplier
        self.manufacturer = manufacturer
        self.price = price
        self.location = location
        self.category = category
        self.receipt_date = receipt_date
        self.warranty_months = warranty_months
        self.status = "принято к учёту"  # статус товара (по умолчанию - принят к учёту)

    def get_info(self) -> Dict[str, Any]:
        """
        Извлекает все данные карточки товара.

        :return: Dict[str, Any]: Словарь со всеми полями карточки.
        """

        return {
            'name': self.name,
            'quantity': self.quantity,
            'state': self.state,
            'supplier': self.supplier,
            'manufacturer': self.manufacturer,
            'price': self.price,
            'location': self.location,
            'category': self.category,
            'receipt_date': self.receipt_date,
            'warranty_months': self.warranty_months,
            'status': self.status
        }

    def update(self, **kwargs: Any) -> bool:
        """
        Обновляет данные карточки товара.

        :param kwargs: Пары ключ-значение для обновления полей.

        :return: bool: True в случае успешного обновления.

        :raises Exception: Если товар списан.
        """

        # проверяем, не списан ли товар
        if self.status == "списано":

            raise Exception("Нельзя изменять списанный товар")

        # перебираем все переданные параметры для обновления
        for key, value in kwargs.items():
            if hasattr(self, key):  # проверяем, существует ли такой атрибут у объекта
                setattr(self, key, value)  # устанавливаем новое значение атрибута

        return True

    def write_off(self) -> bool:
        """
        Списывает товар с учёта.

        :return: bool: True в случае успешного списания.

        :raises Exception: Если статус товара не 'принято к учёту'.
        """

        # проверяем, можно ли списать товар (только из статуса "принято к учёту")
        if self.status != "принято к учёту":

            raise Exception(f"Нельзя списать товар со статусом '{self.status}'")

        # если списали, меняем статус на "списано"
        self.status = "списано"

        return True

    def __str__(self) -> str:
        """
        Строковое представление карточки товара.

        :return: str: Краткая информация о товаре.
        """

        return f"{self.name} | {self.quantity} шт. | {self.status} | {self.price} руб."


class DataSerializer:
    """
    Базовый класс для сериализации и десериализации данных.
    """

    def __init__(self, filename: str) -> None:
        """
        Инициализация сериализатора.

        :param filename: Имя файла для хранения данных.
        """

        self.filename = filename

    def serialize(self, data: Dict[str, Any]) -> bool:
        """
        Сериализует данные в файл.

        :param data: Данные для сериализации.

        :return: bool: True в случае успеха.
        """

        raise NotImplementedError("Метод должен быть переопределен в дочернем классе")

    def deserialize(self) -> Dict[str, Any]:
        """
        Десериализует данные из файла.

        :return: Dict[str, Any]: Данные из файла.
        """

        raise NotImplementedError("Метод должен быть переопределен в дочернем классе")


class JSONSerializer(DataSerializer):
    """
    Класс для сериализации данных в JSON формат.
    """

    def serialize(self, data: Dict[str, Any]) -> bool:
        """
        Сериализует данные в JSON файл.

        :param data: Данные для сериализации.

        :return: bool: True в случае успеха.

        :raises TypeError: Если входные данные имеют неверный тип или
                           содержат несериализуемые значения.
        :raises ValueError: Если у объектов ItemCard отсутствуют обязательные поля.
        :raises OSError: При ошибках создания директории или записи в файл.
        :raises Exception: При других критических ошибках.
        """

        try:
            # проверка входных данных
            if not isinstance(data, dict):

                raise TypeError(f"Ожидался словарь, получен {type(data).__name__}")

            # преобразуем объекты ItemCard в словари
            serializable_data = {}
            for key, item in data.items():
                if not isinstance(key, str):

                    raise TypeError(f"Ключ должен быть строкой, получен {type(key).__name__}")

                if isinstance(item, ItemCard):
                    item_dict = item.get_info()

                    # преобразуем Decimal в float для JSON сериализации
                    if 'price' in item_dict and isinstance(item_dict['price'], Decimal):
                        item_dict['price'] = float(item_dict['price'])

                    # проверка обязательных полей в ItemCard
                    required_fields = ['name', 'quantity', 'state', 'supplier',
                                       'manufacturer', 'price', 'location', 'category',
                                       'receipt_date', 'warranty_months', 'status']

                    missing = [f for f in required_fields if f not in item_dict]
                    if missing:

                        raise ValueError(f"У ItemCard '{key}' отсутствуют поля: {missing}")

                    serializable_data[key] = item_dict
                else:
                    # если не ItemCard, проверяем что это сериализуемый тип
                    try:
                        json.dumps(item)
                    except TypeError as e:

                        raise TypeError(f"Значение для ключа '{key}' не сериализуется в JSON: {e}")

                    serializable_data[key] = item

            # проверка директории
            directory = os.path.dirname(self.filename)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            # запись в файл
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"Неожиданная ошибка при сохранении в JSON: {e}")

            raise  # пробрасываем исключение дальше

    def deserialize(self) -> Dict[str, Any]:
        """
        Десериализует данные из JSON файла и создает объекты ItemCard.

        :return: Dict[str, ItemCard]: Словарь, где ключ - название товара,
                                      значение - объект ItemCard. В случае отсутствия файла
                                    возвращается пустой словарь.

        :raises Exception: Если файл содержит некорректный JSON.
        :raises Exception: Если структура данных не соответствует ожидаемой.
        :raises ValueError: Если отсутствуют обязательные поля.
        :raises ValueError: Если типы данных не соответствуют требованиям.
        :raises Exception: При других неожиданных ошибках.
        """

        # eсли файл не существует, возвращаем пустой словарь
        if not os.path.exists(self.filename):

            return {}

        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, dict):

                raise ValueError("Корневой элемент JSON должен быть словарем")

            items = {}
            for key, item_data in data.items():
                # проверка наличия всех обязательных полей
                required_fields = ['name', 'quantity', 'state', 'supplier',
                                   'manufacturer', 'price', 'location', 'category',
                                   'receipt_date', 'warranty_months']

                missing = [f for f in required_fields if f not in item_data]
                if missing:

                    raise ValueError(f"Для товара '{key}' отсутствуют поля: {missing}")

                # проверка типов
                if not isinstance(item_data['quantity'], (int, float)):

                    raise ValueError(f"quantity для '{key}' должно быть числом")

                if item_data['quantity'] < 0:

                    raise ValueError(f"quantity для '{key}' не может быть отрицательным")

                if not isinstance(item_data['price'], (int, float)):

                    raise ValueError(f"price для '{key}' должно быть числом")

                if item_data['price'] <= 0:

                    raise ValueError(f"price для '{key}' должно быть положительным")

                # преобразуем price из float в Decimal
                item_data['price'] = Decimal(str(item_data['price']))

                items[key] = ItemCard(**item_data)

            return items

        except json.JSONDecodeError as e:

            raise Exception(f"Файл {self.filename} содержит некорректный JSON: {e}")

        except ValueError as e:

            raise ValueError(f"Ошибка валидации данных в {self.filename}: {e}")

        except Exception as e:

            raise Exception(f"Неожиданная ошибка при загрузке {self.filename}: {e}")


class XMLDeserializer(DataSerializer):
    """
    Класс для десериализации данных из XML формата.
    """

    def deserialize(self) -> Dict[str, Any]:
        """
        Десериализует данные из XML файла и создает объекты ItemCard.

        :return: Dict[str, ItemCard]: Словарь с объектами ItemCard.
                 В случае отсутствия файла возвращается пустой словарь.

        :raises Exception: Если файл содержит некорректный XML.
        :raises Exception: Если структура данных не соответствует ожидаемой.
        :raises Exception: Если отсутствуют обязательные поля.
        :raises Exception: Если типы данных не соответствуют требованиям.
        """

        # проверяем существование файла
        if not os.path.exists(self.filename):

            return {}

        try:
            # парсим XML файл и получаем корневой элемент
            tree = ET.parse(self.filename)
            root = tree.getroot()

            # проверяем наличие корневого элемента
            if root is None:

                raise ValueError("XML файл не содержит корневого элемента")

            # проверяем, что корневой элемент называется "catalog"
            if root.tag != "catalog":

                raise ValueError(f"Корневой элемент должен быть <catalog>, получен <{root.tag}>")

            # словарь для хранения загруженных товаров
            items = {}
            item_count = 0

            # ищем все элементы с тегом "item" внутри корня
            for item_elem in root.findall("item"):
                # получаем название товара из атрибута
                name = item_elem.get("name")
                if not name:

                    raise ValueError(f"Элемент item ({item_count + 1}) не содержит атрибут name")

                # словарь для данных текущего товара
                item_data = {'name': name}

                # список обязательных полей
                required_fields = ['quantity', 'state', 'supplier', 'manufacturer',
                                   'price', 'location', 'category', 'receipt_date', 'warranty_months']

                # собираем все найденные поля
                found_fields = []

                # перебираем все дочерние элементы текущего товара
                for field_elem in item_elem:
                    field_name = field_elem.tag
                    field_value = field_elem.text
                    found_fields.append(field_name)

                    # проверяем, что поле не пустое
                    if field_value is None or not field_value.strip():

                        raise ValueError(f"Для товара '{name}' поле '{field_name}' не может быть пустым")

                    field_value = field_value.strip()

                    # преобразуем строки в нужные типы данных
                    try:
                        if field_name in ['quantity', 'warranty_months']:
                            # целочисленные поля
                            value = int(field_value)
                            if value < 0:

                                raise ValueError(f"Поле '{field_name}' не может быть отрицательным")

                            item_data[field_name] = value

                        elif field_name == 'price':
                            # поле с плавающей точкой
                            value = float(field_value)
                            if value <= 0:

                                raise ValueError(f"Цена должна быть положительным числом")

                            item_data[field_name] = Decimal(str(value))  # преобразуем в Decimal

                        else:
                            # остальные поля оставляем как строки
                            item_data[field_name] = field_value

                    except ValueError as e:

                        raise ValueError(f"Для товара '{name}', поле '{field_name}': {e}")

                # проверяем наличие всех обязательных полей
                missing_fields = [f for f in required_fields if f not in found_fields]
                if missing_fields:

                    raise ValueError(f"Для товара '{name}' отсутствуют поля: {missing_fields}")

                # создаем объект ItemCard из собранных данных
                items[name] = ItemCard(**item_data)
                item_count += 1

            return items

        except ET.ParseError as e:
            # ошибка парсинга XML
            error_msg = f"Файл {self.filename} содержит некорректный XML: {e}"
            print(f"{error_msg}")

            raise Exception(error_msg)

        except ValueError as e:
            # ошибка валидации данных
            error_msg = f"Ошибка валидации XML в {self.filename}: {e}"
            print(f"{error_msg}")

            raise Exception(error_msg)

        except Exception as e:
            # любая другая ошибка
            error_msg = f"Неожиданная ошибка при загрузке из XML {self.filename}: {e}"
            print(f"{error_msg}")

            raise Exception(error_msg)


class TXTImporter:
    """
    Класс для импорта данных из текстового файла.
    """

    @staticmethod
    def import_from_txt(filename: str) -> Dict[str, ItemCard]:
        """
        Импортирует данные из текстового файла.

        :param filename: Имя файла для импорта.
        :return: Dict[str, ItemCard]: Импортированные карточки товаров.

        :raises ValueError: При некорректных данных.
        :raises Exception: При других ошибках чтения файла.
        """

        if not os.path.exists(filename):

            return {}

        items = {}
        line_count = 0

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                print(f"Читаем файл: {filename}")

                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # пропускаем пустые строки
                    if not line:
                        continue

                    parts = line.split(';')

                    try:
                        # очищаем цену от возможных символов "руб."
                        price_str = parts[5].split()[0] if ' ' in parts[5] else parts[5]

                        # валидация названия
                        name = parts[0].strip()
                        if not name:

                            raise ValueError(f"Строка {line_num}: название товара не может быть пустым")

                        # валидация количества
                        try:
                            quantity = int(parts[1])
                            if quantity < 0:

                                raise ValueError(f"Строка {line_num}: количество не может быть отрицательным")

                        except ValueError:

                            raise ValueError(
                                f"Строка {line_num}: количество должно быть целым числом, получено '{parts[1]}'")

                        # валидация состояния
                        state = parts[2].strip()
                        if not state:

                            raise ValueError(f"Строка {line_num}: состояние не может быть пустым")

                        # валидация поставщика
                        supplier = parts[3].strip()
                        if not supplier:

                            raise ValueError(f"Строка {line_num}: поставщик не может быть пустым")

                        # валидация производителя
                        manufacturer = parts[4].strip()
                        if not manufacturer:

                            raise ValueError(f"Строка {line_num}: производитель не может быть пустым")

                        # валидация цены
                        try:
                            price = Decimal(price_str)
                            if price <= 0:

                                raise ValueError(f"Строка {line_num}: цена должна быть положительным числом")

                        except (ValueError, decimal.InvalidOperation):

                            raise ValueError(f"Строка {line_num}: цена должна быть числом, получено '{price_str}'")

                        # валидация местоположения
                        location = parts[6].strip()
                        if not location:

                            raise ValueError(f"Строка {line_num}: местоположение не может быть пустым")

                        # валидация категории
                        category = parts[7].strip()
                        if not category:

                            raise ValueError(f"Строка {line_num}: категория не может быть пустой")

                        # валидация даты
                        receipt_date = parts[8].strip()
                        if not receipt_date:

                            raise ValueError(f"Строка {line_num}: дата поступления не может быть пустой")

                        # валидация гарантии
                        try:
                            warranty_months = int(parts[9])
                            if warranty_months < 0:

                                raise ValueError(f"Строка {line_num}: гарантия не может быть отрицательной")

                        except ValueError:

                            raise ValueError(
                                f"Строка {line_num}: гарантия должна быть целым числом, получено '{parts[9]}'")

                        data = {
                            'name': name,
                            'quantity': quantity,
                            'state': state,
                            'supplier': supplier,
                            'manufacturer': manufacturer,
                            'price': price,
                            'location': location,
                            'category': category,
                            'receipt_date': receipt_date,
                            'warranty_months': warranty_months
                        }

                        items[name] = ItemCard(**data)
                        line_count += 1
                        print(f"Добавлен: {name}")

                    except ValueError as e:

                        raise  # пробрасываем ошибки валидации дальше

                if line_count == 0:

                    raise ValueError("Файл не содержит корректных данных")

                print(f"\nИмпортировано {line_count} записей из {filename}")

                return items

        except Exception as e:

            raise Exception(f"Ошибка при импорте из TXT {filename}: {e}")


class CSVImporter:
    """
    Класс для импорта данных из CSV файла.
    """

    @staticmethod
    def import_from_csv(filename: str) -> Dict[str, ItemCard]:
        """
        Импортирует данные из CSV файла.

        :param filename: Имя файла для импорта.
        :return: Dict[str, ItemCard]: Словарь импортированных карточек товаров.

        :raises ValueError: Если отсутствуют обязательные поля или данные некорректны.
        :raises csv.Error: При ошибках парсинга CSV.
        :raises Exception: При других неожиданных ошибках.
        """

        if not os.path.exists(filename):

            return {}

        items = {}
        line_num = 1

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')

                # проверка наличия заголовков
                if not reader.fieldnames:

                    raise ValueError("Файл не содержит заголовков")

                # проверка наличия обязательных полей
                required = ['name', 'quantity', 'state', 'supplier', 'manufacturer',
                            'price', 'location', 'category', 'receipt_date', 'warranty_months']

                missing_fields = [f for f in required if f not in reader.fieldnames]
                if missing_fields:

                    raise ValueError(f"Отсутствуют обязательные поля: {missing_fields}")

                for row_num, row in enumerate(reader, start=2):
                    line_num = row_num

                    try:
                        name = str(row['name']).strip()
                        quantity = int(row['quantity'])
                        state = str(row['state']).strip()
                        supplier = str(row['supplier']).strip()
                        manufacturer = str(row['manufacturer']).strip()
                        price = Decimal(str(row['price']))
                        location = str(row['location']).strip()
                        category = str(row['category']).strip()
                        receipt_date = str(row['receipt_date']).strip()
                        warranty_months = int(row['warranty_months'])

                        if quantity < 0 or warranty_months < 0 or price <= 0:

                            raise ValueError("Некорректные числовые значения")

                        data = {
                            'name': name,
                            'quantity': quantity,
                            'state': state,
                            'supplier': supplier,
                            'manufacturer': manufacturer,
                            'price': price,
                            'location': location,
                            'category': category,
                            'receipt_date': receipt_date,
                            'warranty_months': warranty_months
                        }

                        items[name] = ItemCard(**data)

                    except (ValueError, KeyError, decimal.InvalidOperation) as e:

                        raise ValueError(f"Строка {row_num}: {e}")

                if not items:

                    raise ValueError("Файл не содержит корректных данных")

                print(f"Импортировано {len(items)} записей из {filename}")

                return items

        except csv.Error as e:

            raise csv.Error(f"Ошибка парсинга CSV в строке {line_num}: {e}")

        except Exception as e:

            raise Exception(f"Неожиданная ошибка при импорте из CSV: {e}")


class ItemManager:
    """
    Класс-меню карточек товаров.
    """

    def __init__(self, filename: str) -> None:
        """
        Инициализация менеджера карточек.

        :param filename: Имя файла для загрузки данных (поддерживаются JSON, XML, CSV, TXT).
        """

        self.filename = filename
        self.json_serializer = JSONSerializer("items.json")  # для сохранения всегда в JSON
        self.items = {}

        # определяем формат файла по расширению
        file_extension = os.path.splitext(filename)[1].lower()

        # загружаем данные в зависимости от расширения
        if file_extension == '.json':
            self.items = JSONSerializer(filename).deserialize()
            print(f"Загружено {len(self.items)} записей из JSON файла")

        elif file_extension == '.xml':
            self.items = XMLDeserializer(filename).deserialize()
            print(f"Загружено {len(self.items)} записей из XML файла")

        elif file_extension == '.csv':
            self.items = CSVImporter.import_from_csv(filename)
            print(f"Загружено {len(self.items)} записей из CSV файла")

        elif file_extension == '.txt':
            self.items = TXTImporter.import_from_txt(filename)
            print(f"Загружено {len(self.items)} записей из TXT файла")

        else:
            print(f"Неподдерживаемый формат файла: {file_extension}")
            print("Создан пустой каталог.")

        # если данные загружены, сохраняем их в JSON для дальнейшей работы
        if self.items:
            self._save_to_json()

    def _save_to_json(self) -> None:
        """
        Сохраняет текущие данные в JSON файл.
        """

        self.json_serializer.serialize(self.items)

    def create(self, **data: Any) -> Tuple[bool, str]:
        """
        Создаёт новую карточку товара.

        :param data: Данные для создания карточки.

        :return: Tuple[bool, str]: Кортеж (успех, сообщение).
        """

        # проверяем, есть ли уже товар с таким названием
        if data['name'] in self.items:

            return False, "Товар с таким названием уже существует"

        self.items[data['name']] = ItemCard(**data) # если нет, создаём новую карточку и добавляем в словарь
        self._save_to_json()  # сохраняем изменения

        return True, "Карточка создана"

    def get(self, name: str) -> Optional[ItemCard]:
        """
        Получает карточку товара по названию.

        :param name: Название товара.

        :return: Optional[ItemCard]: Карточка товара или None.
        """

        return self.items.get(name)

    def update(self, name: str, **data: Any) -> Tuple[bool, str]:
        """
        Обновляет существующую карточку товара.

        :param name: Название товара для обновления.

        :param data: Новые данные для обновления.

        :return: Tuple[bool, str]: Кортеж (успех, сообщение).
        """

        item = self.items.get(name)  # ищем карточку по названию

        # если карточка не найдена, возвращаем ошибку
        if not item:

            return False, "Карточка не найдена"

        try:
            # пытаемся обновить данные карточки
            item.update(**data)

            # если изменилось название, обновляем ключ в словаре
            if 'name' in data and data['name'] != name:
                self.items[data['name']] = self.items.pop(name)

            self._save_to_json()  # сохраняем изменения

            return True, "Карточка обновлена"

        # в случае ошибки возвращаем сообщение об ошибке
        except Exception as e:

            return False, str(e)

    def write_off(self, name: str) -> Tuple[bool, str]:
        """
        Списывает товар с учёта.

        :param name: Название товара для списания.

        :return: Tuple[bool, str]: Кортеж (успех, сообщение).
        """

        item = self.items.get(name)  # ищем карточку по названию

        # если карточка не найдена, возвращаем ошибку
        if not item:

            return False, "Карточка не найдена"

        try:
            item.write_off() # пытаемся списать товар
            self._save_to_json()  # Сохраняем изменения

            return True, "Товар списан"

        # в случае ошибки возвращаем сообщение об ошибке
        except Exception as e:

            return False, str(e)

    def delete(self, name: str) -> Tuple[bool, str]:
        """
        Удаляет карточку товара.

        :param name: Название товара для удаления.

        :return: Tuple[bool, str]: Кортеж (успех, сообщение).
        """

        # проверяем, существует ли карточка с таким названием
        if name in self.items:
            del self.items[name]  # удаляем карточку из словаря
            self._save_to_json()  # Сохраняем изменения

            return True, "Карточка удалена"

        # если карточка не найдена, возвращаем ошибку
        return False, "Карточка не найдена"

    def list_all(self) -> List[ItemCard]:
        """
        Возвращает список всех карточек.

        :return: List[ItemCard]: Список карточек товаров.
        """

        return list(self.items.values())


def process_choice(choice: str, manager: ItemManager) -> bool:
    """
    Обрабатывает выбор пользователя.

    :param choice: Выбранный пункт меню.
    :param manager: Экземпляр менеджера карточек.

    :return: bool: False для выхода, True для продолжения.
    """

    # обработка выбора 1
    if choice == "1":
        try:
            # собираем данные от пользователя
            data = {
                "name": input("Название: "),
                "quantity": int(input("Количество: ")),
                "state": input("Состояние: "),
                "supplier": input("Поставщик: "),
                "manufacturer": input("Производитель: "),
                "price": Decimal(input("Цена: ")),
                "location": input("Местоположение: "),
                "category": input("Категория: "),
                "receipt_date": input("Дата поступления (ГГГГ-ММ-ДД): "),
                "warranty_months": int(input("Гарантия (мес): "))
            }
            success, message = manager.create(**data) # передаём данные в менеджер для создания карточки
            print(message)
        except ValueError as e:
            # обработка ошибок ввода (например, если ввели буквы вместо цифр)
            print(f"Ошибка ввода: {e}")

    # обработка выбора 2
    elif choice == "2":
        items = manager.list_all()  # получаем список всех карточек
        if items:
            # выводим каждую карточку
            for item in items:
                print(item)
        else:
            print("Нет карточек")

    # обработка выбора 3
    elif choice == "3":
        name = input("Название: ")
        item = manager.get(name)  # ищем карточку по названию
        if item:
            # если нашли, выводим всю информацию о товаре
            for key, value in item.get_info().items():
                print(f"{key}: {value}")
        else:
            print("Не найдено")

    # обработка выбора 4
    elif choice == "4":
        name = input("Название редактируемого товара: ")
        item = manager.get(name)  # получаем карточку для редактирования
        if item:
            print("Оставьте пустым, если не хотите менять")
            data = {}

            # запрашиваем новые значения (можно оставить пустыми)
            new_name = input(f"Новое название [{name}]: ")
            if new_name:
                data['name'] = new_name

            qty_input = input(f"Количество [{item.quantity}]: ")
            if qty_input:
                data['quantity'] = int(qty_input)

            price_input = input(f"Цена [{item.price}]: ")
            if price_input:
                try:
                    data['price'] = Decimal(price_input)
                except decimal.InvalidOperation:
                    print("Некорректный формат цены")

                    return True

            state_input = input(f"Состояние [{item.state}]: ")
            if state_input:
                data['state'] = state_input

            location_input = input(f"Местоположение [{item.location}]: ")
            if location_input:
                data['location'] = location_input

            # если есть что обновлять, делаем это, вызывая метод update
            if data:
                success, message = manager.update(name, **data)
                print(message)
            else:
                print("Нет изменений")
        else:
            print("Не найдено")

    # обработка выбора "5
    elif choice == "5":
        name = input("Название товара для списания: ")
        success, message = manager.write_off(name)  # списываем товар
        print(message)

    # обработка выбора 6
    elif choice == "6":
        name = input("Название товара для удаления: ")
        success, message = manager.delete(name)  # удаляем карточку
        print(message)

    # обработка выбора 0
    elif choice == "0":
        print("До свидания!")

        return False

    # обработка некорректного выбора
    else:
        print("Неверный выбор. Пожалуйста, выберите пункт от 0 до 6.")

    return True


def display_menu() -> None:
    """
    Отображает меню программы.
    """

    print("\n" + "=" * 40)
    print("УПРАВЛЕНИЕ КАТАЛОГОМ ТОВАРОВ")
    print("=" * 40)
    print("1. Создать новую карточку")
    print("2. Просмотреть все карточки")
    print("3. Найти по названию")
    print("4. Редактировать карточку")
    print("5. Списать товар")
    print("6. Удалить карточку")
    print("0. Выход")
    print("=" * 40)


def main() -> None:
    """
    Главная функция с консольным интерфейсом для взаимодействия с пользователем.
    """

    print("Программа управления каталогом товаров запущена.")
    print("Поддерживаемые форматы: JSON, XML, CSV, TXT")

    # запрашиваем имя файла у пользователя
    filename = input("Введите имя файла для загрузки данных (например, items.json): ")

    if not filename:
        print("Имя файла не может быть пустым.")
    else:
        # создаём экземпляр менеджера с указанным файлом
        manager = ItemManager(filename)

        print(f"Данные загружены из файла: {filename}")

        running = True  # флаг для продолжения работы программы

        # цикл с условием
        while running:
            display_menu()  # отображаем меню

            choice = input("Выберите действие: ")  # получаем выбор пользователя

            running = process_choice(choice, manager)  # обрабатываем выбор и обновляем флаг running


if __name__ == "__main__":
    main()