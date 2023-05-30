

"""
Задание 1.
Каждое из слов «разработка», «сокет», «декоратор» представить в строковом формате
и проверить тип и содержание соответствующих переменных. 
Затем с помощью онлайн-конвертера преобразовать строковые представление
в формат Unicode и также проверить тип и содержимое переменных.
"""

print('------------------------------Задача №1------------------------------')
str_1 = "разработка"
print(type(str_1), str_1)
## <class 'str'> разработка
str_1_utf16 = "\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430"
print(type(str_1_utf16), str_1_utf16)
## <class 'str'> разработка

str_2 = "сокет"
print(type(str_2), str_2)
## <class 'str'> сокет
str_2_utf16 = "\u0441\u043e\u043a\u0435\u0442"
print(type(str_2_utf16), str_2_utf16)
## <class 'str'> сокет

str_3 = "декоратор"
print(type(str_3), str_3)
## <class 'str'> декоратор
str_3_utf16 = "\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440"
print(type(str_3_utf16), str_3_utf16)
## <class 'str'> декоратор


"""
Задание 2.
Каждое из слов «class», «function», «method» записать в байтовом типе 
без преобразования в последовательность кодов (не используя методы encode и decode) 
и определить тип, содержимое и длину соответствующих переменных.
"""

print('------------------------------Задача №2------------------------------')

words = [b'class', b'function', b'method']

for el in words:
    print(f'<Байт-слово "{el}" имеет тип {type(el)}  и  длину {len(el)}.')

## <Байт-слово "b'class'" имеет тип <class 'bytes'>  и  длину 5.
## <Байт-слово "b'function'" имеет тип <class 'bytes'>  и  длину 8.
## <Байт-слово "b'method'" имеет тип <class 'bytes'>  и  длину 6.


"""
Задание 3.
Определить, какие из слов «attribute», «класс», «функция», «type» 
невозможно записать в байтовом типе.
"""

print('------------------------------Задача №3------------------------------')

words = ['attribute', 'класс', 'функция', 'type']

for el in words:
    try:
        print(f'Слово "{el}" представляестя в виде байтовой строки "{bytes(el, "ascii")}"')
    except UnicodeEncodeError:
        print(f'Слово "{el}" невозможно записать в виде байтовой строки, т.к содержит символы не из ASCII')

## Слово "attribute" представляестя в виде байтовой строки "b'attribute'"
## Слово "класс" невозможно записать в виде байтовой строки, т.к содержит символы не из ASCII
## Слово "функция" невозможно записать в виде байтовой строки, т.к содержит символы не из ASCII
## Слово "type" представляестя в виде байтовой строки "b'type'"


"""
Задание 4.
Преобразовать слова «разработка», «администрирование», «protocol», «standard» 
из строкового представления в байтовое и выполнить обратное преобразование 
(используя методы encode и decode).
"""

print('------------------------------Задача №4------------------------------')

words = ['разработка', 'администрирование', 'protocol', 'standard']

for el in words:
    print(f'Слово "{el}" преобразуется в байтовый вид (utf8):\n \
        "{el.encode("utf8")}", \n обратное преобразование: "{el.encode("utf8").decode()}".')

## Слово "разработка" преобразуется в байтовый вид (utf8):
##          "b'\xd1\x80\xd0\xb0\xd0\xb7\xd1\x80\xd0\xb0\xd0\xb1\xd0\xbe\xd1\x82\xd0\xba\xd0\xb0'", 
##  обратное преобразование: "разработка".
## Слово "администрирование" преобразуется в байтовый вид (utf8):
##          "b'\xd0\xb0\xd0\xb4\xd0\xbc\xd0\xb8\xd0\xbd\xd0\xb8\xd1\x81\xd1\x82\xd1\x80\xd0\xb8\xd1\x80\xd0\xbe\xd0\xb2\xd0\xb0\xd0\xbd\xd0\xb8\xd0\xb5'", 
##  обратное преобразование: "администрирование".
## Слово "protocol" преобразуется в байтовый вид (utf8):
##          "b'protocol'", 
##  обратное преобразование: "protocol".
## Слово "standard" преобразуется в байтовый вид (utf8):
##          "b'standard'", 
##  обратное преобразование: "standard". 


"""
Задание 5.
Выполнить пинг веб-ресурсов yandex.ru, youtube.com и 
преобразовать результаты из байтовового в строковый тип на кириллице.
"""

print('------------------------------Задача №5------------------------------')
import subprocess


ping_yandex = subprocess.Popen(("ping", "yandex.ru"), stdout=subprocess.PIPE)
ping_youtube = subprocess.Popen(("ping", "youtube.com"), stdout=subprocess.PIPE)
i = 0

for el in ping_yandex.stdout:
    if i <= 4 :
        i += 1
        print(el.decode("cp866"))
    else:
        i = 0
        break

for el in ping_youtube.stdout:
    if i <= 4 :
        i += 1
        print(el.decode("cp866"))
    else:
        i = 0
        break

## PING yandex.ru (5.255.255.77) 56(84) bytes of data.
## 64 bytes from yandex.ru (5.255.255.77): icmp_seq=1 ttl=128 time=9.82 ms
## 64 bytes from yandex.ru (5.255.255.77): icmp_seq=2 ttl=128 time=9.96 ms
## 64 bytes from yandex.ru (5.255.255.77): icmp_seq=3 ttl=128 time=9.62 ms
## 64 bytes from yandex.ru (5.255.255.77): icmp_seq=4 ttl=128 time=9.77 ms

## PING youtube.com (64.233.163.136) 56(84) bytes of data.
## 64 bytes from lj-in-f136.1e100.net (64.233.163.136): icmp_seq=1 ttl=128 time=18.0 ms
## 64 bytes from lj-in-f136.1e100.net (64.233.163.136): icmp_seq=2 ttl=128 time=18.3 ms
## 64 bytes from lj-in-f136.1e100.net (64.233.163.136): icmp_seq=3 ttl=128 time=17.8 ms
## 64 bytes from lj-in-f136.1e100.net (64.233.163.136): icmp_seq=4 ttl=128 time=18.4 ms


"""
Задание 6.
Создать текстовый файл test_file.txt, заполнить его тремя строками: 
    «сетевое программирование», «сокет», «декоратор». 
Проверить кодировку файла по умолчанию. 
Принудительно открыть файл в формате Unicode и вывести его содержимое.
"""

print('------------------------------Задача №6------------------------------')
# Создание файла, в Линуксе
f = open('test_file_dz1.txt', 'w')
f.writelines(['сетевое программирование\n', 'сокет\n', 'декоратор\n'])
f.close()
print(f'Файл test_file_dz1.txt создан')

# Проверка кодировки файла
with open('test_file_dz1.txt',) as f:  
    print(f'Кодировка файла "{f.encoding}".')
    
# Открытие файла в определённой кодировке (UTF-8)
with open('test_file_dz1.txt', "r", encoding="UTF-8") as f:
    file_contents = f.read()
print(f'Содержимое файла:  \n{file_contents}')

## Файл test_file_dz1.txt создан
## Кодировка файла "UTF-8".
## Содержимое файла:  
## сетевое программирование
## сокет
## декоратор