import telebot
from telebot import types

bot = telebot.TeleBot

materials_db = {
    "штукатурка": {"расход": 8.5, "упаковка": 30},
    "краска": {"расход": 0.12, "упаковка": 10},
    "плитка": {"расход": 1.02, "упаковка": 24},
    "кирпич": {"расход": 51, "упаковка": 480},
    "доска": {"расход": 0.12, "упаковка": 10},
}

region_prices = {
    "Москва": {"штукатурка": 500, "краска": 1200, "плитка": 800, "кирпич": 16.40, "доска": 280},
    "Санкт-Петербург": {"штукатурка": 450, "краска": 1100, "плитка": 750, "кирпич": 23, "доска": 240},
    "другой": {"штукатурка": 400, "краска": 1000, "плитка": 700, "кирпич": 20, "доска": 108}
}

user_data = {}


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_data[user_id] = {'region': 'другой'}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Рассчитать", "Регион")
    bot.send_message(user_id, "Привет! Я строительный калькулятор\nВыберите действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Регион")
def set_region(message):
    markup = types.InlineKeyboardMarkup()
    for region in region_prices.keys():
        markup.add(types.InlineKeyboardButton(region.title(), callback_data=f"region_{region}"))
    bot.send_message(message.chat.id, "Выберите регион:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Рассчитать")
def start_calculation(message):
    user_id = message.chat.id
    if user_id not in user_data:
        user_data[user_id] = {'region': 'другой'}

    markup = types.InlineKeyboardMarkup()
    for material in materials_db.keys():
        markup.add(types.InlineKeyboardButton(material.title(), callback_data=f"material_{material}"))
    bot.send_message(message.chat.id, "Выберите материал:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.message.chat.id

    if call.data.startswith('region_'):
        region = call.data.replace('region_', '')
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['region'] = region
        bot.send_message(user_id, f"Регион: {region.title()}")
        bot.delete_message(user_id, call.message.message_id)

    elif call.data.startswith('material_'):
        material = call.data.replace('material_', '')
        user_data[user_id]['material'] = material
        bot.delete_message(user_id, call.message.message_id)
        msg = bot.send_message(user_id, "Введите длину и ширину комнаты (м):")
        bot.register_next_step_handler(msg, calculate)


def calculate(message):
    try:
        user_id = message.chat.id
        user = user_data[user_id]
        length, width = map(float, message.text.split())
        material = user['material']
        region = user.get('region', 'другой')

        area = 2 * (length + width) * 2.7
        mat_info = materials_db[material]
        price = region_prices[region][material]

        total_material = area * mat_info["расход"]
        packages = int(total_material / mat_info["упаковка"]) + 1
        cost = packages * price

        result = (f"Материал: {material.title()}\n"
                  f"Площадь стен: {area:.1f} м²\n"
                  f"Упаковок: {packages} шт\n"
                  f"Стоимость: {cost} Рублей\n"
                  f"Регион: {region.title()}\n\n"
                  f"Цены могут не совпадать с вашим регионом!")

        bot.send_message(user_id, result)

    except:
        bot.send_message(user_id, "Ошибка. Введите два числа через пробел")
        if user_id in user_data and 'material' in user_data[user_id]:
            msg = bot.send_message(user_id, "Введите длину и ширину:")
            bot.register_next_step_handler(msg, calculate)


if __name__ == "__main__":
    bot.polling(none_stop=True)
