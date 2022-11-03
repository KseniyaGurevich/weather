import subprocess
import sys
from datetime import datetime
import requests
import sqlite3
from statistics import mean
import pandas as pd
import openpyxl
from geopy.geocoders import Nominatim
import logging
from exceptions import TownDoesNotExist, Error


def geolocation(town):
    """Определяет координты введённого города"""
    geolocator = Nominatim(user_agent="ksun")
    return geolocator.geocode(town)


def weather_in_the_city(location):
    """Записывает данные погоды в файл excel"""
    parameters = {
        'lat': location.latitude,
        'lon': location.longitude,
        'lang': 'ru_RU',
    }

    request_headers = {
        'X-Yandex-API-Key': 'a8d64539-21bd-4f80-9691-766773951581'
    }
    url = 'https://api.weather.yandex.ru/v2/informers/'
    response = requests.get(url, headers=request_headers, params=parameters)
    weather = response.json()['forecast']['parts']
    res = {}
    for i in weather:
        try:
            res['part_name'].append(i['part_name'])
            res['Temperature']. append(i['temp_avg'])
            res['Pressure'].append(i['pressure_mm'])
            res['humidity'].append(i['humidity'])
            res['condition'].append(i['condition'])
        except KeyError:
            res['part_name'] = [i['part_name']]
            res['Temperature'] = [i['temp_avg']]
            res['Pressure'] = [i['pressure_mm']]
            res['humidity'] = [i['humidity']]
            res['condition'] = [i['condition']]

    date = response.json()['forecast']['date']
    df = pd.DataFrame(res)
    df.to_excel('./weather.xlsx', sheet_name=date)
    wb = openpyxl.load_workbook('weather.xlsx')
    ws = wb.active
    day_temp_avg = mean(res['Temperature'])
    ws.append(['Среднее значение', '', day_temp_avg, '', '', ''])

    if max(res['Pressure']) - min(res['Pressure']) >= 5:
        if res[0] > res[-1]:
            ws.append(['Ожидается резкое падение атмосферного давления'])
        elif res[0] < res[-1]:
            ws.append(['Ожидается резкое увеличение атмосферного давления'])
    else:
        ws.append(['Давление практически неизменно'])
    wb.save('weather.xlsx')
    logging.info("Данные записаны в файл")


def sql(location):
    """Записывает данные в базу данных sqlite"""
    con = sqlite3.connect('db.sqlite')
    cur = con.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS weather(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date text,
        enter_town text,
        result);
    ''')
    try:
        sqlite_with_parametrs = '''INSERT INTO
                                   weather(date, enter_town, result)
                                   VALUES (?, ?, ?);'''
        data_tuple = (datetime.now(), str(location), 'Greate!')
        cur.execute(sqlite_with_parametrs, data_tuple)
        con.commit()
        con.close()
        logging.info('Данные в sqlite успешно записаны!')
    except ValueError as error:
        logging.error(f'Ошибка при записи данных в sqlite: {error}')


def sql_error():
    """Записывает ошибку в базу данных"""
    con = sqlite3.connect('db.sqlite')
    cur = con.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS weather(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date text,
        enter_town text,
        result
    );
    ''')
    sqlite_with_parametrs = '''INSERT INTO weather(date, enter_town, result)
                                       VALUES (?, ?, ?);'''
    data_tuple = (datetime.now(), None, 'Error')
    cur.execute(sqlite_with_parametrs, data_tuple)
    con.commit()
    con.close()
    logging.info('Ошибка в sqlite записана')


def main():
    """Основная логика работы."""
    logging.basicConfig(
        level=logging.DEBUG,
        format=('%(asctime)s - '
                '%(levelname)s - '
                '%(message)s - '
                '%(name)s - '
                '%(filename)s - '
                '%(funcName)s - '
                '%(lineno)s'),
        handlers=[
            logging.FileHandler('weather.log', 'a', encoding='utf8'),
            logging.StreamHandler(sys.stdout),
        ],
    )
    try:
        town = input('Введите населённый пункт: ')
        location = geolocation(town)
        if location is None:
            logging.error("Такого города не существует")
            sql_error()
            raise TownDoesNotExist
        else:
            logging.info("Координаты населённого пункта успешно определены")

        weather_in_the_city(location)
        sql(location)
        subprocess.call('weather.xlsx', shell=True)
    except Error:
        sql_error()


if __name__ == '__main__':
    main()
