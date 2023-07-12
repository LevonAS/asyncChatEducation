import sys, os, unittest

project_directory = os.getcwd()
sys.path.append(project_directory)

from server import server


class TestServer(unittest.TestCase):

    def test_start_server(self):
        """
        Тестируем корректность запуска серверной части
        :return:
        """
        self.assertRaises(NameError, server)
       


if __name__ == '__main__':
    unittest.main()

