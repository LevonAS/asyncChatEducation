# launcher под Ubunte Server Mate
import os, subprocess, time

PROCESS = []

while True:
    ACTION = input('Выберите действие: q - выход, '
                   's - запустить сервер и клиенты, x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        # PROCESS.append(subprocess.Popen('mate-terminal -- python server_run.py',
        #                                 shell=True))
        # for i in range(3):
        #     PROCESS.append(subprocess.Popen('mate-terminal -- python client_run.py',
        #                                     shell=True))
        # Запускаем клиентов:
        for i in range(4):
            PROCESS.append(subprocess.Popen(f'mate-terminal -- python client_run.py -n usertest{i + 1}',  shell=True))
        # PROCESS.append(subprocess.Popen(f'mate-terminal -- python ./client/client.py -n usertest1',  shell=True))
        # print("PROCESS List", PROCESS)
    elif ACTION == 'x':
        while PROCESS:
            VICTIM = PROCESS.pop()
            # print("VICTIM: ", VICTIM)
            VICTIM.kill()
            # VICTIM.terminate() 
