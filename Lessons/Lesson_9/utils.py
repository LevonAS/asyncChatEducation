import os, time, json
from log.decor_log import log


class Utils():
    def __init__(self):
        pass

    @log
    def send_message(self, open_socket, message):
        json_message = json.dumps(message)
        response = json_message.encode(os.getenv('ENCODING'))
        open_socket.send(response)
        # print("UUU_SM_1", "[message:]", message, "\n[response:]", response, "\n[open_socket:]", open_socket, "\n")

    @log
    def get_message(self, client):
        """
        Утилита приёма и декодирования сообщения принимает байты выдаёт словарь,
        если приняточто-то другое отдаёт ошибку значения
        :param client:
        :return:
        """
        response = client.recv(int(os.getenv('MAX_PACKAGE_LENGTH')))
        # print("UUU_GM_1", response, "||||")
        if isinstance(response, bytes):
            json_response = response.decode(os.getenv('ENCODING'))
            response_dict = json.loads(json_response)
            if isinstance(response_dict, dict):
                # print("UUU_GM_2", response_dict, "||||")
                return response_dict
            raise ValueError
        raise ValueError
        