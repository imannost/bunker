from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify, current_app
import random
import string
import parsing
import generate
import os
import json
import uuid
from copy import deepcopy


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

games = {}

SPREADSHEET_ID = "1dzufUPb0ONrTXV7Vk8az5VuQGb81Nmb_F7cNst1-SS4"
GID_USERS = "1858649706"
GID_CARDS = "707566028"
GID_BUNKER = "2017093968"
GID_EVENTS = "818304491"
GID_BUNKER = "2017093968"
GID_RESOURCES = "427745024"


@app.route('/update_field', methods=['POST'])
def update_field():
    player_index = int(request.form.get('player_index', -1))
    field_name = request.form.get('field_name')
    new_value = request.form.get('new_value')

    game_code = session.get('game_code')
    if not game_code or game_code not in games:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    game_state = games[game_code]
    
    if player_index < 0 or not field_name:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

    player = game_state['players'][player_index]
    field_data = next((f for f in player['fields'] if f['name'] == field_name), None)
    
    if not field_data:
        return jsonify({'success': False, 'error': f'Field "{field_name}" not found'}), 404

    # Персональные навыки
    if field_name == 'Персональный навык':
        import json
        try:
            skills = json.loads(new_value)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Invalid skills data: {e}'}), 400

        if 'base_value' not in field_data:
            field_data['base_value'] = deepcopy(field_data['value'])

        base_map = {s['навык']: s['оценка'] for s in field_data['base_value']}
        updated_skills = []

        for skill in skills:
            name = skill.get('навык')
            try:
                score = int(skill.get('оценка'))
            except (TypeError, ValueError):
                score = base_map.get(name, 0)
            updated_skills.append({'навык': name, 'оценка': score})

        field_data['value'] = updated_skills
    else:
        if 'old_value' not in field_data:
            field_data['old_value'] = field_data['value']  # Сохраняем исходное значение
        field_data['value'] = new_value

    return jsonify({'success': True})

@app.route('/reveal_all_player_fields', methods=['GET'])
def reveal_all_player_fields():
    code = session.get('game_code')
    player_name = session.get('player_name')
    player_index = request.args.get('player_index', type=int)
    
    if not code or not player_name or code not in games:
        return redirect(url_for('index'))
    
    game = games[code]
    players = game['players']
    
    # Проверяем права доступа
    is_master = (player_name == game['master'])
    is_own_card = (player_name == players[player_index]['name'])
    
    if not (is_master or is_own_card):
        return "Недостаточно прав", 403
    
    # Открываем все характеристики у выбранного игрока
    for field in players[player_index]['fields']:
        field['revealed'] = True
    
    return redirect(url_for('game', selected=player_index))

@app.route('/reveal_all', methods=['GET'])
def reveal_all():
    code = session.get('game_code')
    player_name = session.get('player_name')
    
    if not code or not player_name or code not in games:
        return redirect(url_for('index'))
    
    game = games[code]
    
    # Проверяем, является ли текущий игрок мастером
    if player_name != game['master']:
        return "Только мастер может открывать все характеристики", 403
    
    # Открываем все характеристики у всех игроков
    for player in game['players']:
        for field in player['fields']:
            field['revealed'] = True
    
    return redirect(url_for('game'))

@app.route('/reveal_player', methods=['GET'])
def reveal_player():
    code = session.get('game_code')
    player_name = session.get('player_name')
    player_index = request.args.get('player_index', type=int)
    
    if not code or not player_name or code not in games:
        return redirect(url_for('index'))
    
    game = games[code]
    
    # Проверяем, является ли текущий игрок мастером
    if player_name != game['master']:
        return "Только мастер может открывать характеристики игрока", 403
    
    # Проверяем валидность индекса игрока
    if player_index is None or player_index < 0 or player_index >= len(game['players']):
        return "Неверный индекс игрока", 400
    
    # Открываем все характеристики у выбранного игрока
    for field in game['players'][player_index]['fields']:
        field['revealed'] = True
    
    return redirect(url_for('game', selected=player_index))

def fetch_resources():
    """Читает список ресурсов и продюсеров (колонки A и B) и кэширует его."""
    global _CACHED_RESOURCES, _CACHED_PRODUCERS
    try:
        _CACHED_RESOURCES
        _CACHED_PRODUCERS
    except NameError:
        _CACHED_RESOURCES = None
        _CACHED_PRODUCERS = None

    if _CACHED_RESOURCES is not None and _CACHED_PRODUCERS is not None:
        return _CACHED_RESOURCES, _CACHED_PRODUCERS

    base_dir = os.path.dirname(os.path.abspath(__file__))
    cache_resources = os.path.join(base_dir, 'data', 'cache_resources.json')
    cache_producers = os.path.join(base_dir, 'data', 'cache_producers.json')
    try:
        rows = parsing.parse_google_sheet_to_rows(SPREADSHEET_ID, GID_RESOURCES, skip_rows=0, timeout=2.0, retries=1)
        resources = []
        producers = []
        for r in rows:
            # Пропускаем пустые строки
            if len(r) < 2:
                continue
            if r[0] and r[0].strip():
                resources.append(r[0].strip())
            if r[1] and r[1].strip():
                producers.append(r[1].strip())
                
        _CACHED_RESOURCES = resources
        _CACHED_PRODUCERS = producers
        
        # Сохраняем кэш
        os.makedirs(os.path.join(base_dir, 'data'), exist_ok=True)
        with open(cache_resources, 'w', encoding='utf-8') as f:
            json.dump(_CACHED_RESOURCES, f, ensure_ascii=False)
        with open(cache_producers, 'w', encoding='utf-8') as f:
            json.dump(_CACHED_PRODUCERS, f, ensure_ascii=False)
        return _CACHED_RESOURCES, _CACHED_PRODUCERS
    except Exception:
        # Фоллбэк на кэш
        try:
            with open(cache_resources, 'r', encoding='utf-8') as f:
                _CACHED_RESOURCES = json.load(f)
            with open(cache_producers, 'r', encoding='utf-8') as f:
                _CACHED_PRODUCERS = json.load(f)
            return _CACHED_RESOURCES, _CACHED_PRODUCERS
        except Exception:
            return [], []


def fetch_source_data():
    # Глобальный кэш — читаем Google один раз при первом обращении,
    # дальше используем сохранённые данные без повторных запросов
    global _CACHED_USERS_DATA, _CACHED_CARDS_DATA, _SOURCE_INITIALIZED
    try:
        _SOURCE_INITIALIZED
    except NameError:
        _SOURCE_INITIALIZED = False
        _CACHED_USERS_DATA = None
        _CACHED_CARDS_DATA = None

    if _SOURCE_INITIALIZED and _CACHED_USERS_DATA is not None and _CACHED_CARDS_DATA is not None:
        return _CACHED_USERS_DATA, _CACHED_CARDS_DATA

    # Только Google Sheets. Если недоступно — пробуем прочитать последний кэш
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cache_users = os.path.join(base_dir, 'data', 'cache_users.json')
    cache_cards = os.path.join(base_dir, 'data', 'cache_cards.json')
    try:
        users_data = parsing.parse_google_sheet_to_json(
            SPREADSHEET_ID, GID_USERS, skip_rows=1, output_file=None, timeout=2.0, retries=1
        )
        cards_data = parsing.parse_google_sheet_to_json(
            SPREADSHEET_ID, GID_CARDS, skip_rows=0, output_file=None, timeout=2.0, retries=1
        )
        _CACHED_USERS_DATA, _CACHED_CARDS_DATA = users_data, cards_data
        _SOURCE_INITIALIZED = True
        # Пишем кэш снапшота
        os.makedirs(os.path.join(base_dir, 'data'), exist_ok=True)
        with open(cache_users, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False)
        with open(cache_cards, 'w', encoding='utf-8') as f:
            json.dump(cards_data, f, ensure_ascii=False)
        return _CACHED_USERS_DATA, _CACHED_CARDS_DATA
    except Exception:
        # Пытаемся использовать последний успешный кэш
        try:
            with open(cache_users, 'r', encoding='utf-8') as f:
                _CACHED_USERS_DATA = json.load(f)
            with open(cache_cards, 'r', encoding='utf-8') as f:
                _CACHED_CARDS_DATA = json.load(f)
            _SOURCE_INITIALIZED = True
            return _CACHED_USERS_DATA, _CACHED_CARDS_DATA
        except Exception:
            # Если кэша нет — даём понятную ошибку наверх
            raise


def fetch_bunkers():
    """Читает список бункеров (колонки A-D) и кэширует его.
    Возвращает список словарей вида {'A':..., 'B':..., 'C':..., 'D':...}.
    """
    global _CACHED_BUNKERS
    try:
        _CACHED_BUNKERS
    except NameError:
        _CACHED_BUNKERS = None

    if _CACHED_BUNKERS is not None:
        return _CACHED_BUNKERS

    base_dir = os.path.dirname(os.path.abspath(__file__))
    cache_bunkers = os.path.join(base_dir, 'data', 'cache_bunkers.json')
    try:
        rows = parsing.parse_google_sheet_to_rows(SPREADSHEET_ID, GID_BUNKER, skip_rows=0, timeout=2.0, retries=1)
        bunkers = []
        for r in rows:
            cols = (r + [None, None, None, None])[:4]
            item = {'A': cols[0], 'B': cols[1], 'C': cols[2], 'D': cols[3]}
            if any([item['A'], item['B'], item['C'], item['D']]):
                bunkers.append(item)
        _CACHED_BUNKERS = bunkers
        # Сохраняем кэш
        os.makedirs(os.path.join(base_dir, 'data'), exist_ok=True)
        with open(cache_bunkers, 'w', encoding='utf-8') as f:
            json.dump(_CACHED_BUNKERS, f, ensure_ascii=False)
        return _CACHED_BUNKERS
    except Exception:
        # Фоллбэк на кэш
        with open(cache_bunkers, 'r', encoding='utf-8') as f:
            _CACHED_BUNKERS = json.load(f)
        return _CACHED_BUNKERS


def fetch_events():
    """Читает список случайных событий (только первый столбец, пропуская первую строку) и кэширует."""
    global _CACHED_EVENTS
    try:
        _CACHED_EVENTS
    except NameError:
        _CACHED_EVENTS = None

    if _CACHED_EVENTS is not None:
        return _CACHED_EVENTS

    base_dir = os.path.dirname(os.path.abspath(__file__))
    cache_events = os.path.join(base_dir, 'data', 'cache_events.json')
    try:
        rows = parsing.parse_google_sheet_to_rows(SPREADSHEET_ID, GID_EVENTS, skip_rows=1, timeout=2.0, retries=1)
        events = []
        for r in rows:
            if not r:
                continue
            val = r[0].strip() if isinstance(r[0], str) else r[0]
            if val:
                events.append(val)
        _CACHED_EVENTS = events
        os.makedirs(os.path.join(base_dir, 'data'), exist_ok=True)
        with open(cache_events, 'w', encoding='utf-8') as f:
            json.dump(_CACHED_EVENTS, f, ensure_ascii=False)
        return _CACHED_EVENTS
    except Exception:
        with open(cache_events, 'r', encoding='utf-8') as f:
            _CACHED_EVENTS = json.load(f)
        return _CACHED_EVENTS


def fetch_bunkers():
    """Читает список бункеров (колонки A-D) и кэширует его.
    Возвращает список словарей вида {'A':..., 'B':..., 'C':..., 'D':...}.
    """
    global _CACHED_BUNKERS
    try:
        _CACHED_BUNKERS
    except NameError:
        _CACHED_BUNKERS = None

    if _CACHED_BUNKERS is not None:
        return _CACHED_BUNKERS

    base_dir = os.path.dirname(os.path.abspath(__file__))
    cache_bunkers = os.path.join(base_dir, 'data', 'cache_bunkers.json')
    try:
        rows = parsing.parse_google_sheet_to_rows(SPREADSHEET_ID, GID_BUNKER, skip_rows=0, timeout=2.0, retries=1)
        bunkers = []
        for r in rows:
            cols = (r + [None, None, None, None])[:4]
            item = {'A': cols[0], 'B': cols[1], 'C': cols[2], 'D': cols[3]}
            if any([item['A'], item['B'], item['C'], item['D']]):
                bunkers.append(item)
        _CACHED_BUNKERS = bunkers
        # Сохраняем кэш
        os.makedirs(os.path.join(base_dir, 'data'), exist_ok=True)
        with open(cache_bunkers, 'w', encoding='utf-8') as f:
            json.dump(_CACHED_BUNKERS, f, ensure_ascii=False)
        return _CACHED_BUNKERS
    except Exception:
        # Фоллбэк на кэш
        with open(cache_bunkers, 'r', encoding='utf-8') as f:
            _CACHED_BUNKERS = json.load(f)
        return _CACHED_BUNKERS


def build_fields_from_entry(entry: dict):
    fields = []

    def add_field(name: str, value):
        fields.append({"name": name, "value": value, "revealed": False})

    def get_from_any(keys: list[str]):
        for key in keys:
            if key in entry:
                return entry.get(key)
        return None

    # 1. Биография: Пол/Возраст/Ориентация
    bio = entry.get("Биография") if isinstance(entry.get("Биография"), dict) else {}
    bio_parts = []
    for k in ("Пол", "Возраст", "Ориентация"):
        v = bio.get(k)
        if v is not None and v != "":
            bio_parts.append(str(v))
    add_field("Биография", "/".join(bio_parts) if bio_parts else None)

    # 2. Рост
    add_field("Рост", entry.get("Рост"))

    # 3. Вес
    add_field("Вес", entry.get("Вес"))

    # 4. Национальность (fallback на Страна)
    nationality = get_from_any(["Национальность", "Страна"])
    add_field("Национальность", nationality)

    # 5-6. Языки: Знание корейского и Доп языки
    def extract_languages():
        # Предпочитаем явные поля
        know_korean = entry.get("Знание корейского")
        extra_langs = entry.get("Доп языки")
        # Если общего поля нет, попробуем разобрать "Знание языков"
        general = entry.get("Знание языков")
        langs_list: list[str] = []
        if isinstance(general, str):
            langs_list = [s.strip() for s in general.replace(";", ",").split(",") if s.strip()]
        elif isinstance(general, (list, tuple)):
            langs_list = [str(s).strip() for s in general if str(s).strip()]

        if know_korean is None and langs_list:
            # ищем корейский среди общих
            for lang in langs_list:
                if "коре" in lang.lower():
                    know_korean = lang
            # дополнительные — все остальные кроме корейского
            others = [l for l in langs_list if not ("коре" in l.lower())]
            if extra_langs is None and others:
                extra_langs = ", ".join(others)

        return know_korean, extra_langs

    know_korean, extra_langs = extract_languages()
    add_field("Знание корейского", know_korean)
    add_field("Доп языки", extra_langs)

    # 7. Здоровье
    add_field("Здоровье", entry.get("Здоровье"))

    # 8. Фобия
    add_field("Фобия", entry.get("Фобия"))

    # 9. Хобби
    add_field("Хобби", entry.get("Хобби"))

    # 10. Интересный факт из прошлого (разные варианты ключей)
    fact = get_from_any(["Интересный факт из прошлого", "Интересный факт", "Факт из прошлого"])
    add_field("Интересный факт из прошлого", fact)

    # 11. Характер
    add_field("Характер", entry.get("Характер"))

    # 12. Допинфа (поддержка вариаций)
    extra_info = None
    for k in entry.keys():
        lk = k.lower()
        if "доп" in lk and "инф" in lk:
            extra_info = entry.get(k)
            break
    add_field("Допинфа", extra_info)

    # 13. Образ
    add_field("Образ", entry.get("Образ"))

    # 14. Персональный навык (оставляем как список для спец-рендера)
    skills = entry.get("Персональный навык")
    add_field("Персональный навык", skills)

    # 15-16. Карточки: Условия/Действия
    cards = entry.get("Карточки") if isinstance(entry.get("Карточки"), dict) else {}
    if cards:
        if "Условия" in cards:
            add_field("Условия", cards.get("Условия"))
        # Поддержка и старого ключа "События", и нового "Действия"
        if "Действия" in cards:
            add_field("Действия", cards.get("Действия"))

    return fields


def generate_code():
    while True:
        code = str(random.randint(100, 999))
        if code not in games:
            return code

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        # Безопасное получение данных формы с значениями по умолчанию
        player_name = request.form.get('player_name', '').strip()
        count_str = request.form.get('count', '').strip()
        
        # Валидация имени игрока
        if not player_name:
            return render_template('create.html', error="Имя игрока обязательно"), 400
            
        # Валидация количества игроков
        try:
            count = int(count_str)
        except ValueError:
            return render_template('create.html', error="Введите корректное число игроков"), 400
            
        if count < 2 or count > 10:
            return render_template('create.html', error="Количество игроков должно быть от 2 до 10"), 400

        # Получаем данные из Google Sheets и генерируем профили игроков в памяти
        users_data, cards_data = fetch_source_data()
        bunkers = fetch_bunkers()
        events = fetch_events()
        # Если в бункере задан пол (колонка D), применяем его для всех и пересчитываем рост/вес внутри генерации
        forced_gender = None
        # Мы ещё не сохранили игру, поэтому используем выбранный bunker напрямую
        chosen_bunker = random.choice(bunkers) if bunkers else None
        if chosen_bunker:
            dval = chosen_bunker.get('D') if isinstance(chosen_bunker, dict) else getattr(chosen_bunker, 'D', None)
            if isinstance(dval, str) and dval.strip():
                forced_gender = dval.strip().lower()

        generated_entries = generate.create_random_dicts(users_data, cards_data, count, forced_gender=forced_gender)

        resources_list, producers_list = fetch_resources()
        # Генерируем от 1 до 4 случайных ресурсов
        resources = []
        if resources_list:
            num_resources = random.randint(1, min(4, len(resources_list)))
            resources = random.sample(resources_list, num_resources)
        
        # Генерируем от 1 до 4 случайных продюсеров
        producers = []
        if producers_list:
            num_producers = random.randint(1, min(4, len(producers_list)))
            producers = random.sample(producers_list, num_producers)

        # Генерация игры
        code = generate_code()

        players = []
        for i, entry in enumerate(generated_entries):
            fields = build_fields_from_entry(entry)
            players.append({
                'name': player_name if i == 0 else None,
                'fields': fields
            })

        games[code] = {
            'players': players,
            'master': player_name,
            'count': count,
            'bunker': chosen_bunker,
            'random_event': (random.choice(events) if events else None),
            'event_revealed': False,
            'resources': resources,
            'producers': producers
        }

        session['game_code'] = code
        session['player_name'] = player_name

        return redirect(url_for('game'))

    # GET запрос - просто отображаем форму
    return render_template('create.html')

@app.route('/join', methods=['GET', 'POST'])
def join():
    # Авто-ре-join по device_id из сессии
    if request.method == 'GET':
        device_id = session.get('device_id')
        code = session.get('game_code')
        player_name = session.get('player_name')
        if device_id and code in games and player_name:
            return redirect(url_for('game'))

    if request.method == 'POST':
        code = request.form.get('game_code').strip()
        player_name = request.form.get('player_name').strip()

        if not code or len(code) != 3 or not code.isdigit():
            return "Неверный код игры", 400

        if code not in games:
            return "Игра с таким кодом не найдена", 404

        if not player_name:
            return "Имя обязательно", 400

        game = games[code]
        if any(p['name'] == player_name for p in game['players'] if p['name']):
            return "Имя уже занято в этой игре", 400

        free_spot = None
        for i, p in enumerate(game['players']):
            if p['name'] is None:
                free_spot = i
                break
        if free_spot is None:
            return "Все места заняты", 400

        game['players'][free_spot]['name'] = player_name

        session['game_code'] = code
        session['player_name'] = player_name
        # Примитивный device_id: сохраняем уникальный ID в сессию, чтобы по нему восстанавливать
        if not session.get('device_id'):
            session['device_id'] = str(uuid.uuid4())

        return redirect(url_for('game'))

    return render_template('join.html')

@app.route('/game')
def game():
    code = session.get('game_code')
    player_name = session.get('player_name')

    if not code or not player_name or code not in games:
        return redirect(url_for('index'))

    game = games[code]
    players = game['players']

    try:
        current_player_index = next(i for i, p in enumerate(players) if p['name'] == player_name)
    except StopIteration:
        return "Игрок не найден в игре", 400

    selected_player_index = request.args.get('selected', default=current_player_index, type=int)
    if selected_player_index < 0 or selected_player_index >= len(players):
        selected_player_index = current_player_index

    selected_player = players[selected_player_index]
    is_current_player = (current_player_index == selected_player_index)
    is_master = (player_name == game.get('master'))

    # Обработка раскрытия полей и общего события
    reveal_all = request.args.get('reveal_all')
    if reveal_all and is_master:
        for p in players:
            for f in p['fields']:
                f['revealed'] = True
        game['event_revealed'] = True
        return redirect(url_for('game', selected=selected_player_index, keep_info=1))

    reveal_field = request.args.get('reveal_field')
    if reveal_field and is_current_player:
        if reveal_field == '__random_event__':
            game['event_revealed'] = True
            return redirect(url_for('game', selected=selected_player_index, keep_info=1))
        else:
            for field in selected_player['fields']:
                if field['name'] == reveal_field:
                    field['revealed'] = True
                    break
            return redirect(url_for('game', selected=selected_player_index))
    resources = game.get('resources')
    producers = game.get('producers')
    # Первый вход: разворачиваем инфо-панель на мобильных
    session_key = f"info_opened_{code}_{player_name}"
    open_info = False
    if not session.get(session_key):
        session[session_key] = True
        open_info = True
    # Сохраняем раскрытие при ?keep_info=1
    try:
        keep_info = int(request.args.get('keep_info', 0))
    except Exception:
        keep_info = 0
    if keep_info:
        open_info = True
    
    survivors = len(players) // 2

    all_revealed = True
    for field in selected_player['fields']:
        if not field['revealed']:
            all_revealed = False
            break

    return render_template('game.html',
                         code=code,
                         players=players,
                         selected=selected_player_index,
                         current_player_index=current_player_index,
                         current_player_name=player_name,  # Добавлено
                         selected_player=selected_player,
                         is_current_player=is_current_player,
                         is_master=is_master,
                         master=game['master'],
                         resources=resources,
                         producers=producers,
                         bunker=game.get('bunker'),
                         random_event=game.get('random_event'),
                         event_revealed=game.get('event_revealed'),
                         open_info=open_info,
                         survivors=survivors, 
                         all_revealed=all_revealed,
                         enumerate=enumerate)

@app.route('/reveal_word', methods=['POST'])
def reveal_word():
    code = session.get('game_code')
    player_name = session.get('player_name')

    if not code or not player_name or code not in games:
        return redirect(url_for('index'))

    game = games[code]
    players = game['players']

    try:
        player_index = next(i for i, p in enumerate(players) if p['name'] == player_name)
    except StopIteration:
        return "Игрок не найден в игре", 400

    players[player_index]['revealed'] = True

    return redirect(url_for('game', selected=player_index))

@app.route('/exit')
def exit_game():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')