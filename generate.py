import random
import json

def create_random_dicts_and_save(data: dict, data_card: dict, count: int, prefix="result"):
    keys = list(data.keys())

    # Копируем словарь data_card для исключения повторений
    available_card_values = {k: v.copy() for k, v in data_card.items()}

    for i in range(1, count + 1):
        entry = {}
        biography = {}
        cards_entry = {}
        imt_value = None
        height_value = None

        for key in keys:
            values = data[key]
            if key == "Персональный навык":
                skills_with_scores = [
                    {"навык": skill, "оценка": random.randint(0, 10)}
                    for skill in values
                ]
                entry[key] = skills_with_scores
            elif key == "Индекс массы тела":
                if values:
                    imt_value = random.choice(values)
            elif key in ("Пол", "Возраст", "Ориентация"):
                if values:
                    biography[key] = random.choice(values)
                else:
                    biography[key] = None
            else:
                if values:
                    val = random.choice(values)
                    entry[key] = val
                    if key == "Рост":
                        height_value = val
                else:
                    entry[key] = None

        # Формируем вложенный словарь "Карточки" с уникальными значениями из data_card
        for card_key, card_values in available_card_values.items():
            if card_values:
                chosen_value = random.choice(card_values)
                cards_entry[card_key] = chosen_value
                card_values.remove(chosen_value)
            else:
                cards_entry[card_key] = None

        # Добавляем словарь "Карточки" если он не пустой
        if cards_entry:
            entry["Карточки"] = cards_entry

        # Обработка пола и роста
        if biography.get("Пол") == "женский" and height_value is not None:
            try:
                height_int = int(height_value)
                height_int -= 7
                entry["Рост"] = str(height_int)
                height_value = str(height_int)
            except (ValueError, TypeError):
                pass

        # Расчёт веса
        if imt_value is not None and height_value is not None:
            try:
                imt_float = float(imt_value.replace(',', '.'))
                height_int = int(height_value)
                weight = imt_float * height_int * height_int / 10000
                entry["Вес"] = round(weight, 2)
            except (ValueError, TypeError):
                entry["Вес"] = None

        # Добавляем biography, если он не пустой
        if biography:
            entry["Биография"] = biography

        filename = f"{prefix}_{i}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False, indent=4)
        print(f"✅ Сохранён файл {filename}")



def create_random_dicts_one(data: dict, data_card: dict):
    keys = list(data.keys())

    # Копируем словарь data_card для исключения повторений
    available_card_values = {k: v.copy() for k, v in data_card.items()}

    entry = {}
    biography = {}
    cards_entry = {}
    imt_value = None
    height_value = None

    for key in keys:
        values = data[key]
        if key == "Персональный навык":
            skills_with_scores = [
                {"навык": skill, "оценка": random.randint(0, 10)}
                for skill in values
            ]
            entry[key] = skills_with_scores
        elif key == "Индекс массы тела":
            if values:
                imt_value = random.choice(values)
        elif key in ("Пол", "Возраст", "Ориентация"):
            if values:
                biography[key] = random.choice(values)
            else:
                biography[key] = None
        else:
            if values:
                val = random.choice(values)
                entry[key] = val
                if key == "Рост":
                    height_value = val
            else:
                entry[key] = None

    # Формируем вложенный словарь "Карточки" с уникальными значениями из data_card
    for card_key, card_values in available_card_values.items():
        if card_values:
            chosen_value = random.choice(card_values)
            cards_entry[card_key] = chosen_value
            card_values.remove(chosen_value)
        else:
            cards_entry[card_key] = None

    # Добавляем словарь "Карточки" если он не пустой
    if cards_entry:
        entry["Карточки"] = cards_entry

    # Обработка пола и роста
    if biography.get("Пол") == "женский" and height_value is not None:
        try:
            height_int = int(height_value)
            height_int -= 7
            entry["Рост"] = str(height_int)
            height_value = str(height_int)
        except (ValueError, TypeError):
            pass

    # Расчёт веса
    if imt_value is not None and height_value is not None:
        try:
            imt_float = float(imt_value.replace(',', '.'))
            height_int = int(height_value)
            weight = imt_float * height_int * height_int / 10000
            entry["Вес"] = round(weight, 2)
        except (ValueError, TypeError):
            entry["Вес"] = None

    # Добавляем biography, если он не пустой
    if biography:
        entry["Биография"] = biography
    
    return entry


def create_random_dicts(data: dict, data_card: dict, count: int, forced_gender: str | None = None) -> list[dict]:
    """
    Генерирует список записей (count штук) из всех полей Google Sheets, включая вложенные разделы.
    Возвращает список словарей entry.
    """
    keys = list(data.keys())

    # Копируем словарь data_card для исключения повторений между игроками
    available_card_values = {k: v.copy() for k, v in data_card.items()}

    entries: list[dict] = []

    for _ in range(count):
        entry: dict = {}
        biography: dict = {}
        cards_entry: dict = {}
        imt_value = None
        height_value = None

        for key in keys:
            values = data[key]
            if key == "Персональный навык":
                skills_with_scores = [
                    {"навык": skill, "оценка": random.randint(0, 10)}
                    for skill in values
                ]
                entry[key] = skills_with_scores
            elif key == "Индекс массы тела":
                if values:
                    imt_value = random.choice(values)
                    entry["Индекс массы тела"] = imt_value
            elif key in ("Пол", "Возраст", "Ориентация"):
                if key == "Пол" and forced_gender:
                    biography[key] = forced_gender
                else:
                    if values:
                        biography[key] = random.choice(values)
                    else:
                        biography[key] = None
            else:
                if values:
                    val = random.choice(values)
                    entry[key] = val
                    if key == "Рост":
                        height_value = val
                else:
                    entry[key] = None

        # Формируем вложенный словарь "Карточки" с уникальными значениями из data_card
        for card_key, card_values in available_card_values.items():
            if card_values:
                chosen_value = random.choice(card_values)
                cards_entry[card_key] = chosen_value
                card_values.remove(chosen_value)
            else:
                cards_entry[card_key] = None

        if cards_entry:
            entry["Карточки"] = cards_entry

        # Обработка пола и роста (с учётом принудительного пола)
        if biography.get("Пол") == "женский" and height_value is not None:
            try:
                height_int = int(height_value)
                height_int -= 7
                entry["Рост"] = str(height_int)
                height_value = str(height_int)
            except (ValueError, TypeError):
                pass

        # Расчёт веса
        if imt_value is not None and height_value is not None:
            try:
                imt_float = float(imt_value.replace(',', '.'))
                height_int = int(height_value)
                weight = imt_float * height_int * height_int / 10000
                entry["Вес"] = round(weight, 2)
            except (ValueError, TypeError):
                entry["Вес"] = None

        if biography:
            entry["Биография"] = biography

        entries.append(entry)

    return entries

