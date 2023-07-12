import unittest, os, sys
from dotenv import load_dotenv


project_directory = os.getcwd()
sys.path.append(project_directory)

from utils import parse_response


class TestClient(unittest.TestCase):
    load_dotenv()

    def test_200_ans(self):
        """Тест корректтного разбора ответа 200"""
        self.assertEqual(parse_response({'response': 200}), '200 : OK',
                         'Тест корректтного разбора ответа 200 не пройден')
    print("Тест корректтного разбора ответа 200")

    def test_400_ans(self):
        """Тест корректного разбора 400"""
        self.assertEqual(parse_response({'response': 400, 'error': 'Bad Request'}), '400 : Bad Request',
                         'Тест корректного разбора 400 не пройден')
    print("Тест корректного разбора 400 пройден")

    def test_no_response(self):
        """Тест исключения без поля RESPONSE"""
        self.assertRaises(ValueError, parse_response, {
                          'error': 'Bad Request'})
    print("Тест исключения без поля RESPONSE пройден")


if __name__ == '__main__':
    unittest.main()
