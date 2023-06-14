import os, subprocess, time

PROCESS = []

while True:
    ACTION = input('Выберите действие: q - выход, '
                   's - запустить сервер и клиенты, x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        PROCESS.append(subprocess.Popen('mate-terminal -- python server.py',
                                        shell=True))
        for i in range(4):
            PROCESS.append(subprocess.Popen('mate-terminal -- python client.py',
                                            shell=True))
        # print("PROCESS", PROCESS)
    elif ACTION == 'x':
        while PROCESS:
            VICTIM = PROCESS.pop()
            VICTIM.kill()
