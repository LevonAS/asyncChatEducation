"""
Задание на закрепление знаний по модулю CSV. Написать скрипт, осуществляющий выборку
определенных данных из файлов info_2_1.txt, info_2_2.txt, info_2_3.txt и формирующий новый
«отчетный» файл в формате CSV.
Для этого:
 a. Создать функцию get_data(), в которой в цикле осуществляется перебор файлов с
    данными, их открытие и считывание данных. В этой функции из считанных данных
    необходимо с помощью регулярных выражений извлечь значения параметров
    «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы». Значения
    каждого параметра поместить в соответствующий список. Должно получиться четыре
    списка — например, os_prod_list, os_name_list, os_code_list, os_type_list. В этой же
    функции создать главный список для хранения данных отчета — например, main_data
    — и поместить в него названия столбцов отчета в виде списка: «Изготовитель
    системы», «Название ОС», «Код продукта», «Тип системы». Значения для этих
    столбцов также оформить в виде списка и поместить в файл main_data (также для
    каждого файла);
 b. Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл. В этой
    функции реализовать получение данных через вызов функции get_data(), а также
    сохранение подготовленных данных в соответствующий CSV-файл;
 c. Проверить работу программы через вызов функции write_to_csv().
"""

import csv, re, os, chardet


def get_data():
    os_prod_list, os_name_list, os_code_list, os_type_list = [], [], [], []
    main_data = [['', 'Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']]
    files_in_dir = os.listdir(os.path.dirname(os.path.abspath(__file__)))


    for i in range(1, 4):
        filename = f'info_{i}.txt'
        if (filename in files_in_dir):
            with open('info_2.txt', 'rb') as f:
                encoding_f = chardet.detect(f.readline())["encoding"]
            with open(filename,  'r', encoding=encoding_f) as f:
                for line in f:
                    parse = re.match(r'^([А-яA-z() ]*): *([A-zА-я 0-9\/,:;()+.-]*)', line)

                    # заполняем промежуточные списки
                    if parse is not None and parse[1] in main_data[0]:
                        if   parse[1] == main_data[0][1]:
                            os_prod_list.append(parse[2])
                        elif parse[1] == main_data[0][2]:
                            os_name_list.append(parse[2])
                        elif parse[1] == main_data[0][3]:
                            os_code_list.append(parse[2])
                        elif parse[1] == main_data[0][4]:
                            os_type_list.append(parse[2])
                        else:
                            None
    
    # заполняем главный список
    j = 1
    for i in range(0, 3):
        main_data.append([j, os_prod_list[i], os_name_list[i], os_code_list[i], os_type_list[i]])
        j += 1

    return main_data


def write_to_csv(csv_file):
    data = get_data()
    # формирование результирующего файла
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        for line in data:
            writer.writerow(line)
    
    # проверка результата выводом результирующего файла в консоль
    with open(csv_file, 'r', encoding='utf-8') as file:
        print(file.read())


if __name__ == '__main__':
    write_to_csv('report_file.csv')


## "","Изготовитель системы","Название ОС","Код продукта","Тип системы"
## 1,"LENOVO","Microsoft Windows 7 Профессиональная ","00971-OEM-1982661-00231","x64-based PC"
## 2,"ACER","Microsoft Windows 10 Professional","00971-OEM-1982661-00231","x64-based PC"
## 3,"DELL","Microsoft Windows 8.1 Professional","00971-OEM-1982661-00231","x86-based PC"
