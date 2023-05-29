import os
import json
from dotenv import load_dotenv
import time


class Utils():
    def __init__(self) -> None:
        self.load_cfg()

    def load_cfg(self):
        self.env = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(self.env):
            load_dotenv(self.env)
        else:
            print(
                f'Файл настроек \'{self.env.split(".")[1]}\' отствует!')

    def send_message(self, open_socket, message):
        json_message = json.dumps(message)
        response = json_message.encode(os.getenv('ENCODING'))
        open_socket.send(response)

    def get_message(self, open_socket):
        response = open_socket.recv(int(os.getenv('MAX_PACKAGE_LENGTH')))
        if isinstance(response, bytes):
            json_response = response.decode(os.getenv('ENCODING'))
            response_dict = json.loads(json_response)
            if isinstance(response_dict, dict):
                return response_dict
            raise ValueError
        raise ValueError

    def parse_message(self, message):
        if os.getenv('ACTION') in message \
                and message[os.getenv('ACTION')] == os.getenv('PRESENCE') \
                and os.getenv('TIME') in message \
                and os.getenv('USER') in message \
                and message[os.getenv('USER')][os.getenv('ACCOUNT_NAME')] == 'Guest':
            return {os.getenv('RESPONSE'): 200}
        return {
            os.getenv('RESPONSE'): 400,
            os.getenv('ERROR'): 'Bad Request'
        }

    def create_presence_message(self, account_name):
        message = {
            os.getenv('ACTION'): os.getenv('PRESENCE'),
            os.getenv('TIME'): time.time(),
            os.getenv('USER'): {
                os.getenv('ACCOUNT_NAME'): account_name
            }
        }
        return message

    def parse_response(self, message):
        if os.getenv('RESPONSE') in message:
            if message[os.getenv('RESPONSE')] == 200:
                return '200 : OK'
            return f'400 : {message[os.getenv("ERROR")]}'
        raise ValueError
        