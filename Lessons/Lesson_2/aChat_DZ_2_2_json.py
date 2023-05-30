"""
Задание на закрепление знаний по модулю json. Есть файл orders в формате JSON с
информацией о заказах. Написать скрипт, автоматизирующий его заполнение данными. 
Для этого:
 a. Создать функцию write_order_to_json(), в которую передается 5 параметров — товар
    (item), количество (quantity), цена (price), покупатель (buyer), дата (date). Функция
    должна предусматривать запись данных в виде словаря в файл orders.json. При
    записи данных указать величину отступа в 4 пробельных символа;
 b. Проверить работу программы через вызов функции write_order_to_json() с передачей
    в нее значений каждого параметра.
"""

import json


def write_order_to_json(item, quantity, price, buyer, date):
    filename = "orders.json"
    with open(filename, 'r', encoding='utf-8') as f_r:
        data = json.load(f_r)

    data['orders'].append({ 'item': item, 
                        'quantity': quantity,
                           'price': price, 
                           'buyer': buyer, 
                            'date': date
                           })

    with open(filename, "w", encoding="utf-8") as f_w:
        json.dump(data, f_w, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    write_order_to_json('Intel Core i5 - 12400F', '1', '14830', 
                'Иванов', '01.05.2023')
    write_order_to_json('NVIDIA GeForce RTX 3060 Palit Dual 12Gb', 
                '1', '33950', 'Петров', '02.05.2023')
    write_order_to_json('MSI PRO H610M-E ', '1', '6790', 'Сидоров',
                '03.05.2023')
