import logging as log
import os
import datetime as dt
from os.path import expandvars

path = os.path.dirname(os.path.abspath(__file__))


# def init_log_file():
#     if os.path.exists(path + '/logs/' + str(dt.date.today()) +
#                       'app.log'):
#         log.error('Файл логирования инициирован')
#         return path + '/logs/' + str(dt.date.today()) + 'app.log'
#     else:
#         with open(path + '/logs/' + str(dt.date.today()) + 'app.log', 'w'):
#             log.error('Файл логирования инициирован')
#         return path + '/logs/' + str(dt.date.today()) + 'app.log'


# TODO Не забыть добавить path в filename при деплое на прод
log.basicConfig(filename=str(dt.date.today()) + 'app.log', filemode='w', level=log.INFO,
                format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
