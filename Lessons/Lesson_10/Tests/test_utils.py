import unittest, os, json, sys
from dotenv import load_dotenv

project_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_directory)

from utils import send_message, get_message


class TestSocket:
    '''
    Тестовый класс для тестирования отправки и получения,
    при создании требует словарь, который будет прогонятся
    через тестовую функцию
    '''

    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.receved_message = None

    def send(self, message_to_send):
        """
        Тестовая функция отправки, корретно  кодирует сообщение,
        так-же сохраняет что должно было отправлено в сокет.
        message_to_send - то, что отправляем в сокет
        :param message_to_send:
        :return:
        """
        json_test_message = json.dumps(self.test_dict)
        # кодирует сообщение
        self.encoded_message = json_test_message.encode('utf-8')
        # сохраняем что должно было отправлено в сокет
        self.receved_message = message_to_send

    def recv(self, max_len):
        """
        Получаем данные из сокета
        :param max_len:
        :return:
        """
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode('utf-8')


class TestUtils(unittest.TestCase):
    load_dotenv()
    test_dict_send = {
        'action': 'presence',
        'time': 111111.111111,
        'user': {
            'account_name': 'test_test'
        }
    }
    test_dict_recv_ok = {'response': 200}
    test_dict_recv_err = {
        'response': 400,
        'error': 'Bad Request'
    }

    def setUp(self):
        pass

    def tearDown(self):
        pass
  
    def test_send_message(self):
        """
        Тестируем корректность работы фукции отправки,
        создадим тестовый сокет и проверяю корректность отправки словаря
        :return:
        """
        # экземпляр тестового словаря, хранит собственно тестовый словарь
        test_socket = TestSocket(self.test_dict_send)
        # вызов тестируемой функции, результаты будут сохранены в тестовом сокете
        send_message(test_socket, self.test_dict_send)
        # проверка корретности кодирования словаря.
        # сравниваем результат довренного кодирования и результат от тестируемой функции
        self.assertEqual(test_socket.encoded_message,
                         test_socket.receved_message)
        # дополнительно, проверим генерацию исключения, при не словаре на входе.
        with self.assertRaises(Exception):
            send_message(test_socket, test_socket)
        print("Тест функции отправки сообщения пройден")

    def test_get_message(self):
        """
        Тест функции приёма сообщения
        :return:
        """
        test_sock_ok = TestSocket(self.test_dict_recv_ok)
        test_sock_err = TestSocket(self.test_dict_recv_err)
        # тест корректной расшифровки корректного словаря
        self.assertEqual(get_message(test_sock_ok), self.test_dict_recv_ok)
        # тест корректной расшифровки ошибочного словаря
        self.assertEqual(get_message(test_sock_err), self.test_dict_recv_err)
        print("Тест функции приёма сообщения пройден")

    def test_read_env(self):
        """
        Тестируем корректность чтения файла настроек .env
        :return:
        """
        self.assertEqual(os.getenv('DEFAULT_IP_ADDRESS'), '127.0.0.1',
                         'Параметры из файла .env не прочитаны')
        self.assertEqual(os.getenv('DEFAULT_PORT'), '7777',
                         'Параметры из файла .env не прочитаны')           
        self.assertEqual(os.getenv('ENCODING'), 'utf-8',
                         'Параметры из файла .env не прочитаны')
        print("Тест корректности чтения файла настроек .env пройден")
        

if __name__ == "__main__":
    unittest.main()
