# Импортируем библиотеку telebot для работы с Telegram API
import telebot
# Импортируем модуль types для создания клавиатур и кнопок
from telebot import types


bot = telebot.TeleBot

# База данных материалов: название -> {расход на м2, количество в упаковке}
materials_db = {
    "штукатурка": {"расход": 8.5, "упаковка": 30},
    "краска": {"расход": 0.12, "упаковка": 10},
    "плитка": {"расход": 1.02, "упаковка": 24},
    "кирпич": {"расход": 51, "упаковка": 480},
    "доска": {"расход": 0.12, "упаковка": 10},
}

# Цены на материалы в разных регионах
region_prices = {
    "Москва": {"штукатурка": 500, "краска": 1200, "плитка": 800, "кирпич": 16.40, "доска": 280},
    "Санкт-Петербург": {"штукатурка": 450, "краска": 1100, "плитка": 750, "кирпич": 23, "доска": 240},
    "другой": {"штукатурка": 400, "краска": 1000, "плитка": 700, "кирпич": 20, "доска": 108}
}

# Словарь для хранения данных каждого пользователя (ID пользователя -> его данные)
user_data = {}


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    # Получаем ID пользователя из сообщения
    user_id = message.chat.id
    # Инициализируем данные пользователя, регион по умолчанию - 'другой'
    user_data[user_id] = {'region': 'другой'}

    # Создаем обычную клавиатуру (не Inline) с кнопками
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # resize_keyboard - подгоняет размер
    # Добавляем кнопки
    markup.add("Рассчитать", "Регион")
    # Отправляем приветственное сообщение с клавиатурой
    bot.send_message(user_id, "Привет! Я строительный калькулятор\nВыберите действие:", reply_markup=markup)


# Обработчик текстовых сообщений - вызывается когда пользователь нажал "Регион"
@bot.message_handler(func=lambda message: message.text == "Регион")
def set_region(message):
    # Создаем  клавиатуру c кнопками внутри сообщения
    markup = types.InlineKeyboardMarkup()
    # Перебираем все регионы из словаря region
    for region in region_prices.keys():
        # Для каждого региона создаем кнопку
        markup.add(types.InlineKeyboardButton(region.title(), callback_data=f"region_{region}"))
    # Отправляем сообщение с выбором региона
    bot.send_message(message.chat.id, "Выберите регион:", reply_markup=markup)


# Обработчик нажатия кнопки "Рассчитать"
@bot.message_handler(func=lambda message: message.text == "Рассчитать")
def start_calculation(message):
    user_id = message.chat.id
    # Если пользователя нет в базе, создаем для него запись с регионом по умолчанию
    if user_id not in user_data:
        user_data[user_id] = {'region': 'другой'}

    # Создаем клавиатуру для выбора материала
    markup = types.InlineKeyboardMarkup()
    # Перебираем все доступные материалы
    for material in materials_db.keys():
        # Добавляем кнопку с названием материала
        markup.add(types.InlineKeyboardButton(material.title(), callback_data=f"material_{material}"))
    # Отправляем сообщение с выбором материала
    bot.send_message(message.chat.id, "Выберите материал:", reply_markup=markup)


# Обработчик всех запросов
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    # Получаем ID пользователя из сообщения
    user_id = call.message.chat.id

    # Проверяем, что нажата кнопка выбора региона
    if call.data.startswith('region_'):
        # Извлекаем название региона
        region = call.data.replace('region_', '')
        # Если пользователя нет в базе, создаем запись
        if user_id not in user_data:
            user_data[user_id] = {}
        # Сохраняем выбранный регион
        user_data[user_id]['region'] = region
        # Подтверждаем выбор региона
        bot.send_message(user_id, f"Регион: {region.title()}")
        # Удаляем сообщение с кнопками выбора региона
        bot.delete_message(user_id, call.message.message_id)

    # Проверяем, что нажата кнопка выбора материала
    elif call.data.startswith('material_'):
        # Извлекаем название материала
        material = call.data.replace('material_', '')
        # Сохраняем выбранный материал
        user_data[user_id]['material'] = material
        # Удаляем сообщение с кнопками выбора материала
        bot.delete_message(user_id, call.message.message_id)
        # Запрашиваем размеры комнаты и регистрируем следующий шаг 
        msg = bot.send_message(user_id, "Введите длину и ширину комнаты (м):")
        bot.register_next_step_handler(msg, calculate)


# Функция расчета количества материала и стоимости
def calculate(message):
    try:
        user_id = message.chat.id
        # Получаем данные пользователя
        user = user_data[user_id]
        # Разделяем введенную строку на два числа (длина и ширина)
        length, width = map(float, message.text.split())
        # Получаем выбранный материал
        material = user['material']
        # Получаем регион (если нет - 'другой')
        region = user.get('region', 'другой')

        # Рассчитываем площадь стен (периметр * высоту 2.7м)
        area = 2 * (length + width) * 2.7
        # Получаем информацию о материале из базы
        mat_info = materials_db[material]
        # Получаем цену для выбранного региона и материала
        price = region_prices[region][material]

        # Рассчитываем общее количество материала
        total_material = area * mat_info["расход"]
        # Рассчитываем количество упаковок (округляем вверх)
        packages = int(total_material / mat_info["упаковка"]) + 1
        # Рассчитываем общую стоимость
        cost = packages * price

        # Формируем результат
        result = (f"Материал: {material.title()}\n"
                  f"Площадь стен: {area:.1f} м²\n"
                  f"Упаковок: {packages} шт\n"
                  f"Стоимость: {cost} Рублей\n"
                  f"Регион: {region.title()}\n\n"
                  f"Цены могут не совпадать с вашим регионом!")

        # Отправляем результат пользователю
        bot.send_message(user_id, result)

    # Обрабатываем ошибки (неправильный ввод)
    except:
        bot.send_message(user_id, "Ошибка. Введите два числа через пробел")
        # Если данные есть, повторно запрашиваем ввод
        if user_id in user_data and 'material' in user_data[user_id]:
            msg = bot.send_message(user_id, "Введите длину и ширину:")
            bot.register_next_step_handler(msg, calculate)


# Точка входа в программу
if __name__ == "__main__":
    # Запускаем бота в режиме постоянного опроса сервера Telegram
    # none_stop=True - продолжать работу даже при ошибках
    bot.polling(none_stop=True)