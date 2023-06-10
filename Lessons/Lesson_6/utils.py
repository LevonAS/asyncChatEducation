import os, time, json
from log.decor_log import log


@log
def send_message(open_socket, message):
    json_message = json.dumps(message)
    response = json_message.encode(os.getenv('ENCODING'))
    open_socket.send(response)

@log
def get_message(open_socket):
    response = open_socket.recv(int(os.getenv('MAX_PACKAGE_LENGTH')))
    if isinstance(response, bytes):
        json_response = response.decode(os.getenv('ENCODING'))
        response_dict = json.loads(json_response)
        if isinstance(response_dict, dict):
            return response_dict
        raise ValueError
    raise ValueError

@log
def parse_message(message):
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

@log
def create_presence_message(account_name):
    message = {
        os.getenv('ACTION'): os.getenv('PRESENCE'),
        os.getenv('TIME'): time.time(),
        os.getenv('USER'): {
            os.getenv('ACCOUNT_NAME'): account_name
        }
    }
    return message

@log
def parse_response(message):
    if os.getenv('RESPONSE') in message:
        if message[os.getenv('RESPONSE')] == 200:
            return '200 : OK'
        return f'400 : {message[os.getenv("ERROR")]}'
    raise ValueError
        