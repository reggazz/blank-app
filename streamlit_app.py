import pytz
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
import time as t
from datetime import datetime
from flatlib import const
from flatlib.geopos import GeoPos
from timezonefinder import TimezoneFinder
import io
import matplotlib
matplotlib.use("Agg")  # <-- добавь в самом начале, до импорта pyplot
import matplotlib.pyplot as plt
import numpy as np
import os

from yandexcloud import SDK
import requests
import os

def get_timezone(lat, lon):
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        raise ValueError("Не удалось определить часовой пояс для координат")
    return pytz.timezone(tz_name)

def swa(
    date=None, hour=None, minutes=None, Latitude=None, Longitude=None,
    dateNow=None, hourNow=None, minutesNow=None, LatitudeNow=None, LongitudeNow=None,
    draw_aspects_mode="all",# "transit-natal", "natal", "transit", "all", "none"
    zodiakType="Альтернативный",
    moonMonth=False,
    colorScheme="rainbow"
    ):

    # Start timing
    start_time = t.time()

    # === Определение среды ===
    dpi = None
    figsize = None
    if dpi is None or figsize is None:
        if "DEEPNOTE_PROJECT_ID" in os.environ:
            # Deepnote
            dpi = 110
            figsize = (7, 7)
        else:
            # Предположительно Render или продакшн
            dpi = 300
            figsize = (7, 7)

    transit_data_provided = all([
        dateNow is not None, hourNow is not None, minutesNow is not None, LatitudeNow is not None, LongitudeNow is not None
    ])
    natal_data_provided = all([
        date is not None, hour is not None, minutes is not None, Latitude is not None, Longitude is not None
    ])

    # List of planets to calculate positions for
    planets = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]
    planet_positions = {}
    
    info_text = ""
    info_text_2 = ""
    aspects_text = ""

    if natal_data_provided:
        # mode = "transit-natal" # только текущие планеты
        # draw_aspects_mode="all" # "transit-natal", "natal", "transit", "all", "none"
        # print ("natal_data_provided")
        
        # Данные рождения
        input_date = date.strftime('%Y/%m/%d')  # Date of interest
        hour = int(hour)  # Hour of interest
        minutes = int(minutes)  # Minutes of interest
        time = f"{hour:02}:{minutes:02}"  # Format time as HH:MM

        # timeNow = f"{hourNow:02}:{minutesNow:02}"  # Format time as HH:MM

        # Calculate GMT offset dynamically
        # local_tz = pytz.timezone('Europe/Moscow')  # Replace with the appropriate timezone
        local_tz = get_timezone(Latitude, Longitude)
        local_time = datetime.strptime(f"{input_date} {time}", "%Y/%m/%d %H:%M")
        local_time = local_tz.localize(local_time)
        gmt_offset_seconds = local_time.utcoffset().total_seconds()
        gmt_offset_hours = int(gmt_offset_seconds // 3600)
        gmt_offset = f"{gmt_offset_hours:+03}:00"

        # Location coordinates
        latitude, longitude = float(Latitude), float(Longitude)

        # Create a Flatlib Datetime and GeoPos object
        dt = Datetime(input_date, time, gmt_offset)
        pos = GeoPos(latitude, longitude)

        # Create a chart
        chart = Chart(dt, pos)

        # Get the ascendant
        ascendant = chart.get('Asc')
        ascendant_sign = ascendant.sign
        ascendant_degree = ascendant.lon
        zodiac_type = "Tropical"  # Flatlib uses the tropical zodiac by default
        # Определяем дом, в котором находится натальный асцендент
        ascendant_house_index = int(ascendant_degree // 30)  # Индекс дома (0-11)

        # Calculate degree within the sign
        sign_degrees = ascendant_degree % 30

        for planet in planets:
            try:
                obj = chart.get(planet)
                planet_positions[planet] = {
                    'sign': obj.sign,
                    'degree': obj.lon,
                    'sign_degree': obj.lon % 30
                }
            except KeyError:
                planet_positions[planet] = 'Data not available'

        planet_positions
        
        info_text = f"Время рождения: {input_date} Time: {time}  GMT Offset: {gmt_offset} Latitude: {Latitude} Longitude: {Longitude}"

        # End timing
        end_time = t.time()
        execution_time = end_time - start_time
    else:
        mode = "current" # только текущие планеты
    
    if transit_data_provided:
        # print ("transit_data_provided")
        # # Input data
        input_date2 = dateNow.strftime('%Y/%m/%d')  # Date of interest
        hourNow = int(hourNow)  # Hour of interest
        minutesNow = int(minutesNow)  # Minutes of interest
        timeNow = f"{hourNow:02}:{minutesNow:02}"  # Format time as HH:MM

        # Calculate GMT offset dynamically
        # local_tz = pytz.timezone('Europe/Moscow')  # Replace with the appropriate timezone
        local_tz = get_timezone(LatitudeNow, LongitudeNow)
        local_time = datetime.strptime(f"{input_date2} {timeNow}", "%Y/%m/%d %H:%M")
        local_time = local_tz.localize(local_time)
        gmt_offset_seconds = local_time.utcoffset().total_seconds()
        gmt_offset_hours = int(gmt_offset_seconds // 3600)
        current_gmt_offset = f"{gmt_offset_hours:+03}:00"

        # Location coordinates
        latitudeNow, longitudeNow = float(LatitudeNow), float(LongitudeNow)

        # Create a Flatlib Datetime and GeoPos object
        pos = GeoPos(LatitudeNow, longitudeNow)
        # Создаем объект Flatlib для текущей даты и времени
        current_dt = Datetime(input_date2, timeNow, current_gmt_offset)
        current_chart = Chart(current_dt, pos)

        # Рассчитываем положения планет для текущей даты и времени
        current_planet_positions = {}
        for planet in planets:
            try:
                obj = current_chart.get(planet)
                current_planet_positions[planet] = {
                    'sign': obj.sign,
                    'degree': obj.lon,
                    'sign_degree': obj.lon % 30
                }
            except KeyError:
                current_planet_positions[planet] = 'Data not available'
        info_text_2 = f"Время расчета: {input_date2}, Time: {timeNow}, GMT Offset: {current_gmt_offset}, Latitude: {LatitudeNow}, Longitude: {LongitudeNow}"   

    # Если включен тип зодиака 1, добавляем аянамшу к углам
    ayanamsha = 0  # Значение по умолчанию
    if zodiakType == "Сидерический": # Сидерический
        ayanamsha = 24.0  # Примерное значение аянамши, заменить на точное при необходимости
        ayanamsha_rad = np.deg2rad(ayanamsha)
    else: # Тропический
        ayanamsha_rad = 0

    # Если включен режим "лунный месяц", поворачиваем график так, чтобы Солнце было на юге
    if moonMonth:
        sun_position = current_planet_positions.get('Sun', {}).get('degree', 0)  # Положение Солнца в градусах
        rotation_offset = np.deg2rad(270) - np.deg2rad(sun_position)  # Поворачиваем так, чтобы Солнце оказалось внизу
        if (zodiakType == "Сидерический"): # Сидерический
            rotation_offset = np.deg2rad(270) - np.deg2rad(sun_position) + ayanamsha_rad # Поворачиваем так, чтобы Солнце оказалось внизу
    else:
        rotation_offset = ayanamsha_rad  # Поворачиваем график так, чтобы весеннее равноденствие было на западе

    # Создаем круг, разделенный на 12 частей
    fig, ax = plt.subplots(figsize=(figsize), subplot_kw={'projection': 'polar'})  # Увеличиваем размер круга
    ax.set_theta_zero_location('W')  # Устанавливаем начальную точку отсчета (восток)
    ax.set_theta_direction(-1)  # Устанавливаем направление против часовой стрелки
    # ax.set_ylim(0, 1.15)  # Устанавливает радиус от 0 до 0.1
    ax.set_aspect('equal')  # Устанавливает равные пропорции осей

    
    # Определяем иконки и названия знаков зодиака
    zodiac_icons = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']
    zodiac_signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    if colorScheme == "rainbow":
        zodiac_colors = [
        'red', 'brown', 'cyan', 'blue', 'red', 'brown', 
        'cyan', 'blue', 'red', 'brown', 'cyan', 'blue'
        ]
    else:
        zodiac_colors = [
        'black', 'black', 'black', 'black', 'black', 'black', 
        'black', 'black', 'black', 'black', 'black', 'black'
        ]
    # Если включен альтернативный зодиак, сдвигаем иконки на один знак вперед
    if zodiakType == "Альтернативный":
        zodiac_icons = zodiac_icons[1:] + zodiac_icons[:1]  # Сдвиг иконок
        zodiac_colors = zodiac_colors[1:] + zodiac_colors[:1]  # Сдвиг цветов

    planet_icons = {'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂', 'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇'}
    planet_colors = {'Sun': 'gold', 'Moon': 'darkgray', 'Mercury': 'gray', 'Venus': 'green', 'Mars': 'red', 'Jupiter': 'orange', 'Saturn': 'black', 'Uranus': 'cyan', 'Neptune': 'blue', 'Pluto': 'brown'}

    # Настраиваем начальный угол для знаков зодиака
    angles = np.linspace(0, 2 * np.pi, 13) + rotation_offset  # Углы для разделения на 12 частей
    
    if natal_data_provided:
        # Добавляем номера домов, начиная с дома асцендента
        for i in range(12):
            house_number = (i - ascendant_house_index) % 12 + 1  # Номер дома с учетом асцендента
            house_angle = (angles[i] + angles[i+1]) / 2  # Средний угол для номера дома
            ax.text(house_angle, 0.5, str(house_number), ha='center', va='center', fontsize=8, color='gray', alpha=0.5)  # Полупрозрачные номера домов


    # Определяем цвета для различных регионов
    if colorScheme == "rainbow":
        # colors = ['Indigo', 'Magenta', 'Pink', 'Red', 'OrangeRed', 'Yellow', 'YellowGreen', 'Green', 'Aqua', 'Cyan', 'SkyBlue', 'Blue']
        colors = [
        (128, 0, 255),     # Indigo (270°)
        (255, 0, 255),     # Magenta (300°)
        (255, 0, 128),     # Pink (330°)
        (255, 0, 0),       # Red (0°)
        (255, 128, 0),     # OrangeRed (30°)
        (255, 255, 0),     # Yellow (60°)
        (128, 255, 0),     # YellowGreen (90°)
        (0, 255, 0),       # Green (120°)
        (0, 255, 128),     # Aqua (150°)
        (0, 255, 255),     # Cyan (180°)
        (0, 128, 255),     # SkyBlue (210°)
        (0, 0, 255),       # Blue (240°)
        ]
        colors = [(r/255, g/255, b/255) for r, g, b in colors]
    else:
        colors = ['blue', 'blue', 'blue', 'red', 'red', 'red', 'brown', 'brown', 'brown', 'lightblue', 'lightblue', 'lightblue']

    if zodiakType == "Сидерический":
        # colors = ['gray', 'gray', 'gray', 'gray', 'gray', 'gray', 'gray', 'gray', 'gray', 'gray', 'gray', 'gray']
        colors = colors[-1:] + colors[:-1]  # Сдвиг цветов
    if zodiakType == "Тропический":
        colors = colors[-1:] + colors[:-1]  # Сдвиг цветов

    orientOffset = 0
    if moonMonth == 1:
        orientOffset = rotation_offset
    import matplotlib.transforms as transforms
    from matplotlib.patches import RegularPolygon
    # Создаем треугольник с вершиной вниз — повернутый на 180 градусов
    # if zodiakType == "Сидерический":
    #     rotation_offset = rotation_offset - 30
    triangle_down = RegularPolygon(
        (0.5, 0.5),
        numVertices=3,
        radius=0.10,
        orientation=np.pi - orientOffset,  # 180 градусов в радианах
        color='cyan',
        alpha=0.2,
        transform=ax.transAxes
    )
    ax.add_patch(triangle_down)    
    # Добавляем треугольник
    triangle = RegularPolygon(
    (0.5, 0.5),
    numVertices=3,
    radius=0.10,
    orientation=0 - orientOffset,
    color='red',
    alpha=0.2,
    transform=ax.transAxes
    )
    ax.add_patch(triangle)

    # Рисуем 12 секций с полукруглыми формами
    for i in range(12):
        theta = np.linspace(angles[i], angles[i+1], 100)  # Углы для текущей секции
        r_inner = np.zeros_like(theta)  # Внутренний радиус (нулевой)
        r_outer = np.ones_like(theta)  # Внешний радиус (единичный)
        ax.fill_between(theta, r_inner, r_outer, color=colors[i], alpha=0.080)  # Прозрачный фон для секции
        ax.text((angles[i] + angles[i+1]) / 2, 0.7, zodiac_icons[i], ha='center', va='center', fontsize=20, color=zodiac_colors[i], alpha=1.00)  # Перемещаем иконки ближе к центру

    # Добавляем по 30 делений для каждого знака
    for i in range(12):
        for j in range(30):
            minor_angle = angles[i] + (j * (angles[i+1] - angles[i]) / 30)  # Угол для каждого деления
            ax.plot([minor_angle, minor_angle], [0.95, 1], color='gray', lw=0.5)  # Линии делений с уменьшенной длиной

    if natal_data_provided:
        # Добавляем асцендент на график
        ascendant_angle = np.deg2rad(ascendant_degree) + rotation_offset  # Угол асцендента в радианах
        ax.text(ascendant_angle, 1.15, "Asc", ha='center', va='center', fontsize=10, color='purple')  # Подпись асцендента
        ax.plot(ascendant_angle, 0.95, 'o', color='purple', markersize=3)  # Уменьшенная точка для асцендента

    if transit_data_provided:
        # Добавляем иконки планет для текущей даты и времени
        for planet, data in current_planet_positions.items():
            if isinstance(data, dict):  # Проверяем, что данные доступны
                if zodiakType == "Тропический" or zodiakType == "Альтернативный":
                    planet_angle = np.deg2rad(data['degree']) + rotation_offset
                elif zodiakType == "Сидерический" and moonMonth == 1:
                    planet_angle = np.deg2rad(data['degree']) + rotation_offset - ayanamsha_rad
                else:
                    planet_angle = np.deg2rad(data['degree'])
                planet_radius = 1.07  # Радиус для иконки планеты ближе к кругу
                fontsize = 20 if planet == 'Moon' else 15
                ax.text(planet_angle, planet_radius, planet_icons.get(planet, '?'), ha='center', va='center', fontsize=fontsize, color=planet_colors.get(planet, 'black'))  # Иконка планеты с цветом
                ax.plot(planet_angle, 1, 'o', color=planet_colors.get(planet, 'black'), markersize=3)  # Точка планеты на краю круга

    if natal_data_provided:
        # Добавляем иконки натальных планет на график
        for planet, data in planet_positions.items():
            if isinstance(data, dict):  # Проверяем, что данные доступны
                if zodiakType == "Тропический" or zodiakType == "Альтернативный":
                    planet_angle = np.deg2rad(data['degree']) + rotation_offset
                elif zodiakType == "Сидерический" and moonMonth == 1:
                    planet_angle = np.deg2rad(data['degree']) + rotation_offset - ayanamsha_rad
                else:
                    planet_angle = np.deg2rad(data['degree'])
                planet_radius = 0.89  # Радиус для иконки планеты ближе к краю круга
                fontsize = 20 if planet == 'Moon' else 15
                ax.text(planet_angle, planet_radius, planet_icons.get(planet, '?'), ha='center', va='center', fontsize=fontsize, color=planet_colors.get(planet, 'black'))  # Иконка планеты с цветом
                ax.plot(planet_angle, 0.95, 'o', color=planet_colors.get(planet, 'black'), markersize=3)  # Точка планеты ближе к краю круга

    # Добавляем точки солнцестояний и равноденствий
    solstice_equinox_angles = {
        'Весеннее равноденствие': (0, 'blue'),  # Овен (0°)
        'Летнее солнцестояние': (90, 'red'),  # Рак (90°)
        'Осеннее равноденствие': (180, 'brown'),  # Весы (180°)
        'Зимнее солнцестояние': (270, 'lightblue')  # Козерог (270°)
    }

    for event, (angle, color) in solstice_equinox_angles.items():
        event_angle = np.deg2rad(angle)    # Угол события в радианах с учетом поворота
        if (zodiakType == "Тропический" or zodiakType == "Альтернативный"): event_angle = event_angle + rotation_offset
        if (zodiakType == "Сидерический" and moonMonth == 1): event_angle = event_angle + rotation_offset - ayanamsha_rad
        # if ((zodiakType == "Тропический" or zodiakType == "Альтернативный") and moonMonth == 1): event_angle = event_angle + rotation_offset
        ax.plot([event_angle, event_angle], [0, 1.15], color=color, lw=0.4)  # Линия от центра круга до квадрата
        ax.scatter(event_angle, 1.15, color=color, s=100, marker='s', label=event)  # Квадратная иконка события

    if draw_aspects_mode!="none":
        orb = 2  # Орбис в градусах
        # Добавляем мажорные аспекты между текущими и натальными планетами
        MAJOR_ASPECTS = {
            'Conjunction': 0,
            'Opposition': 180,
            'Trine': 120,
            'Square': 90,
            'Sextile': 60
        }

    def draw_aspects(ax, planet_positions1, planet_positions2, rotation_offset, zodiakType, moonMonth, ayanamsha, orb, radius1, radius2):
        aspects_info = []
        seen_aspects = set()  # чтобы исключить повтор в тексте

        for planet1, data1 in planet_positions1.items():
            if isinstance(data1, dict):
                angle1 = data1['degree']
                for planet2, data2 in planet_positions2.items():
                    if planet1 != planet2 and isinstance(data2, dict):
                        angle2 = data2['degree']

                        for aspect, aspect_angle in MAJOR_ASPECTS.items():
                            angle_diff = abs((angle2 - angle1) % 360)
                            angle_diff = min(angle_diff, 360 - angle_diff)

                            if abs(angle_diff - aspect_angle) <= orb:
                                # Вычисляем углы в радианах
                                if zodiakType in ["Тропический", "Альтернативный"]:
                                    angle1_rad = np.deg2rad(angle1) + rotation_offset
                                    angle2_rad = np.deg2rad(angle2) + rotation_offset
                                elif zodiakType == "Сидерический" and moonMonth == 1:
                                    angle1_rad = np.deg2rad(angle1 - ayanamsha) + rotation_offset
                                    angle2_rad = np.deg2rad(angle2 - ayanamsha) + rotation_offset
                                else:
                                    angle1_rad = np.deg2rad(angle1)
                                    angle2_rad = np.deg2rad(angle2)

                                # Цвет линии в зависимости от аспекта
                                if aspect == 'Conjunction':
                                    color = 'yellow'
                                elif aspect in ['Trine', 'Sextile']:
                                    color = 'green'
                                elif aspect in ['Opposition', 'Square']:
                                    color = 'red'
                                else:
                                    color = 'gray'

                                # Рисуем линию всегда
                                ax.plot([angle1_rad, angle2_rad], [radius1, radius2], color=color, lw=1.4)

                                # Ключ для уникальности (планеты в алфавитном порядке)
                                pair_key = (tuple(sorted([planet1, planet2])), aspect, round(angle_diff, 2))
                                if pair_key not in seen_aspects:
                                    seen_aspects.add(pair_key)
                                    aspects_info.append(f"{planet1} {aspect} {planet2} (разница: {angle_diff:.2f}°)")

        return "\n".join(aspects_info)

    aspects_text2 = ""
    aspects_text3 = ""

    # Аспекты от текущих к натальным
    if (draw_aspects_mode == "all" or draw_aspects_mode == "transit-natal") and natal_data_provided and transit_data_provided:
        aspects_text=draw_aspects(ax, planet_positions, current_planet_positions, rotation_offset, zodiakType, moonMonth, ayanamsha, orb, 0.95, 1)
        aspects_text="Аспекты транзитных планет к натальным: " +  aspects_text
    # Аспекты между текущими планетами
    if (draw_aspects_mode == "transit" or draw_aspects_mode == "all") and transit_data_provided:
        aspects_text2=draw_aspects(ax, current_planet_positions, current_planet_positions, rotation_offset, zodiakType, moonMonth, ayanamsha, orb, 1, 1)
        aspects_text2 = "Аспекты между транзитными планет: " + aspects_text2
    # Аспекты между натальными планетами
    if (draw_aspects_mode == "natal") and natal_data_provided:
        aspects_text3=draw_aspects(ax, planet_positions, planet_positions, rotation_offset, zodiakType, moonMonth, ayanamsha, orb, 0.95, 0.95)
        aspects_text3 = "Аспекты между натальными планетами: " + aspects_text3
    # Добавляем крест, если включен режим "лунный месяц"
    if moonMonth:
        ax.plot([0, 0], [0, 1], color='gray', lw=0.5, linestyle='--')  # Вертикальная линия
        ax.plot([np.pi / 2, np.pi / 2], [0, 1], color='gray', lw=0.5, linestyle='--')  # Горизонтальная линия (вправо)
        ax.plot([np.pi, np.pi], [0, 1], color='gray', lw=0.5, linestyle='--')  # Вертикальная линия (вниз)
        ax.plot([3 * np.pi / 2, 3 * np.pi / 2], [0, 1], color='gray', lw=0.5, linestyle='--')  # Горизонтальная линия (влево)

    if natal_data_provided:
        # Добавляем стрелку от центра до точки Луны, если включен режим "moonMonth"
        if moonMonth:
            moon_data = current_planet_positions.get('Moon', {})
            if isinstance(moon_data, dict):
                moon_angle = np.deg2rad(moon_data['degree']) + rotation_offset - ayanamsha_rad
                ax.annotate(
                    '', 
                    xy=(moon_angle, 1),  # Конечная точка стрелки (на краю круга)
                    xytext=(0, 0),  # Начальная точка стрелки (центр круга)
                    arrowprops=dict(facecolor='gray', arrowstyle='->', lw=1.5)
                )

    # Убираем сетку, метки и круг
    ax.grid(False)  # Убираем сетку
    ax.set_yticklabels([])  # Убираем метки радиуса
    ax.set_xticklabels([])  # Убираем метки углов
    ax.spines['polar'].set_visible(False)  # Убираем круговую рамку

    # Перемещаем легенду направо за круг
    # plt.legend(loc='upper left',bbox_to_anchor=(0.00, 0.1),frameon=False, fontsize=7, title="События")#bbox_to_anchor=(0.0, 0.0), 
    
    if (info_text != "") or (info_text_2 != ""):
        ax.text(0.05, 1.05, f"{info_text}\n{info_text_2}", transform=ax.transAxes, fontsize=7, va='top', ha='left')

    # # Output results
    # print(f"Время рождения: {input_date}, Time: {time}, GMT Offset: {gmt_offset}, Latitude: {Latitude}, Longitude: {Longitude}")
    # print(f"Время расчета: {input_date2}, Time: {timeNow}, GMT Offset: {current_gmt_offset}, Latitude: {LatitudeNow}, Longitude: {LongitudeNow}")
    # print(f"Асцендент: {ascendant_sign}, Degree: {ascendant_degree} ({sign_degrees:.2f}° in {ascendant_sign}), Zodiac Type: {zodiac_type}")
    
    if natal_data_provided and not transit_data_provided:
        moon = chart.get(const.MOON)
        sun = chart.get(const.SUN)
    if transit_data_provided :
        moon = current_chart.get(const.MOON)
        sun = current_chart.get(const.SUN)
    # Лунный день
    moon_phase_angle = (moon.lon - sun.lon) % 360
    lunar_day = int(moon_phase_angle / 12) + 1
    # Время до полнолуния/новолуния
    if moon_phase_angle < 180:
        phase = "новолуния"
        time_to_phase = (180 - moon_phase_angle) / 12  # в днях
    else:
        phase = "полнолуния"
        time_to_phase = (360 - moon_phase_angle) / 12  # в днях
    # Знак Луны
    moon_sign = moon.sign
    if zodiakType == "Альтернативный":
        # Сдвиг знака на один вперед
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        moon_sign_index = (signs.index(moon_sign) + 1) % 12
        moon_sign = signs[moon_sign_index]
    # Формируем текстовую информацию
    infoMoon = (
        # f"Лунный день: {lunar_day}\n"
        # f"Время до {phase}: {time_to_phase:.2f} дней\n"
        f"Луна в знаке: {moon_sign}")
    if natal_data_provided and not transit_data_provided:
        infoMoon = (
        # f"Лунный день: {lunar_day}\n"
        # f"Время до {phase}: {time_to_phase:.2f} дней\n"
        f"Натальная луна в знаке: {moon_sign}")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=dpi)
    plt.close(fig)

    buf.seek(0)
    
    if "DEEPNOTE_PROJECT_ID" in os.environ:# если в deep note
        from IPython.display import display, Image
        display(Image(data=buf.getvalue()))

    # return buf, yandexGPT("дай характеристику транзита с точки зрения древней астрологии в которой телец - это точка весеннего равноденствия." + infoMoon)
    callbackQuery = ""
    if (draw_aspects_mode == "all"): 
        callbackQuery = "Дай характеристику аспекта транзитной планеты к натальной:\n " + aspects_text + "\nА также дай характеристику аспекта между транзитными планетами:\n " + aspects_text2
    if (draw_aspects_mode == "transit"): 
        callbackQuery = "Дай характеристику аспекта между транзитными планетами:\n " + aspects_text2
    if (draw_aspects_mode == "natal"): 
        callbackQuery = "Дай характеристику аспекта натальных планет:\n " + aspects_text3
    if (draw_aspects_mode == "transit-natal"): 
        callbackQuery = "Дай характеристику аспекта транзитной планеты к натальной:\n " +  aspects_text

    # print (callbackQuery + " и описание лунного дня: " + infoMoon)

    return buf, yandexGPT(callbackQuery + " и описание лунного дня: " + infoMoon)

def yandexGPT(inputText):
    oauth_token = os.getenv("OAUTH_TOKEN")
    IAM_TOKEN = get_iam_token(oauth_token)
    if not IAM_TOKEN:
        return None

    FOLDER_ID = 'b1gi25autl18rk6ja7nl'

    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'application/json'
    }

    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",  # или yandexgpt если доступен
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": 1000
        },
        "messages": [
            {
            "role": "system", 
            "text": "Ты профессиональный астролог с 15-летним опытом. Отвечай, используя астрологические термины, аспекты и влияния планет. В своих ответах учитывай положения планет, знаки зодиака и их влияние на ситуацию. Пиши профессионально, но понятно для клиента. Избегай сложных технических терминов без объяснения."
            },
            {"role": "user", "text": inputText}
        ]
    }

    response = requests.post(
        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        headers=headers,
        json=data
    )
    if response.status_code != 200:
        print("Ошибка от API LLM:", response.text)
        return None
    response_json = response.json()
    if "result" not in response_json:
        print("В ответе нет ключа 'result':", response_json)
        return None

    text = response_json["result"]["alternatives"][0]["message"]["text"]
    # print(text)
    return text

def get_iam_token(oauth_token):
    response = requests.post(
        'https://iam.api.cloud.yandex.net/iam/v1/tokens',
        json={'yandexPassportOauthToken': oauth_token}
    )
    if response.status_code == 200:
        return response.json()['iamToken']
    else:
        print('Ошибка получения IAM токена:', response.text)
        return None

from datetime import datetime
import pytz  # если get_timezone возвращает tzinfo

tz = get_timezone(57, 41)
now = datetime.now(tz)

inputs2 = {
    "dateNow": dateNow,          # обязательно передан
    "hourNow": hourNow,
    "minutesNow": minutesNow,
    "LatitudeNow": LatitudeNow,
    "LongitudeNow": LongitudeNow,
}

dateNow = inputs2.get("dateNow") or now.date()
hourNow = inputs2.get("hourNow") or now.hour
minutesNow = inputs2.get("minutesNow") or now.minute
LatitudeNow = inputs2.get("LatitudeNow") or 0
LongitudeNow = inputs2.get("LongitudeNow") or 0

params = {
    # "date": date,
    # "hour": hour,
    # "minutes": minutes,
    # "Latitude": Latitude,
    # "Longitude": Longitude, 
    "dateNow": now.date(),
    "hourNow": now.hour,
    "minutesNow": now.minute,
    "LatitudeNow": 57,
    "LongitudeNow": 41,
    "draw_aspects_mode": "all",# all natal transit transit-natal
    "zodiakType": "Альтернативный", # "Сидерический""Альтернативный""Тропический"
    "moonMonth": False, # True False
    "colorScheme": "rainbow",#rainbow gray 
}
swa(**params)
# yandexGPT(swa(**params)[1])

