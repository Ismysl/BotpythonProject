from main import bot, dp, con
from aiogram import types
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, \
 InputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from config import admin_id
from docxtpl import DocxTemplate
from aiogram.dispatcher.filters.state import State, StatesGroup
import json, string
from urllib.parse import urljoin
import pymorphy2

import pandas as pd
import nltk
import nupy as np
import re
from nltk.stem import wordnet # to perform Lemmitization
from sklearn.feature_extraction.text import CountVectorizer # to perform bow
from sklearn.feature_extraction.text import TfidfVectorizer # to perform tfidf
from nltk import pos_tag # for parts of speech
from sklearn.metrics import pairwise_distances # to perfrom cosine similarity
from nltk import word_tokenize # to create tokens
from nltk.corpus import stopwords # for stop words


global mes
global flag
global doc_id
doc_data ={}
user_data = {}

spisok_num = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
spisok_buk = ['ё', 'й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ъ', 'ф', 'ы', 'в', 'а', 'п', 'р', 'о',
              'о', 'л', 'д', 'ж', 'э', 'я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю',
              'b', 'd', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'z']
spisok_simvl = ['!', '@', '#', '$', ';', '^', ':', ',', '-', '(', ')', '*', '?']

MAIN_DOC_URL = "C:/Users/imysl/OneDrive/BotpythonProject/"


# проерка только на наличие цифр
def chek_number(slovo):
    for i in str(slovo):
        if i not in spisok_num:
            if i != '.':
                return False


# проверка только на наличие букв
def chek_bukv(slovo):
    for i in str(slovo).lower():
        if (i != ' ') and (i != '-'):
            if i not in spisok_buk:
                return False


# проверка ФИО человека
def chek_fio(fio):
    sobstv = fio.split()
    if 4 > len(sobstv) > 1:
        if chek_bukv(fio) == False:
            return "В поле ФИО Собственника присутсвуют посторонние символы!"
    else:
        return "В поле ФИО Собственника укажите ФИО!"
    return 'Все верно'


# проверка корректности ввода даты
def chek_data(znach_data):
    if len(znach_data) == 10:  # проверка длинны введенной даты
        vrem = znach_data.split('.')
        if len(vrem) == 3:  # проверка формата ввода
            if (len(vrem[0]) != 4) or (len(vrem[1]) != 2) or (len(vrem[2]) != 2):
                return "Неверный формат, введите по формату ГГГГ.ММ.ДД"
            else:
                message = chek_number(znach_data)
                if message == False:
                    return 'В поле дата присутсвуют посторонние символы'
                if int(vrem[0]) > 2023:
                    return 'Год указан неверно!'
                if '00' == vrem[1]:
                    return 'Введите месяц больше 0!'
                if '00' == vrem[2]:
                    return 'Введите число больше 0!'
                if 0 > int(vrem[1]) or int(vrem[1]) > 12:  # проверка корректности введенного месяца
                    return "Неверно введен месяц, введите по формату ГГГГ.ММ.ДД"
                else:  # проверка числа дней в месяце
                    mes = int(vrem[1])
                    day = int(vrem[2])
                    spisok_day_mes = [31, 0, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                    if mes == 2:
                        if int(vrem[0]) // 4 == 0:
                            if 0 < day > 29:
                                return "Количество дней не допустимое в месяце!"
                        else:
                            if 0 < day > 28:
                                return "Количество дней не допустимое в месяце!"
                    else:
                        if 0 < day > spisok_day_mes[mes - 1]:
                            return "Количество дней не допустимое в месяце!"
            if chek_number(znach_data) == False:
                return "В введенной дате имеются буквы!"
        else:
            return "Введите дату через точку! (ГГГГ.ММ.ДД)"
    else:
        return "Неверное число символов в дате!"
    return 'Все верно'


class User:
    def __init__(self, first_name):
        self.first_name = first_name
        self.last_name = ''
        self.date_birth = ''
        self.role_user = 'User'


class Docx:
    def __init__(self, number_doc):
        self.number_doc = number_doc
        self.date_doc = ''
        self.name_comp_cl = ''
        self.fio_client = ''
        self.subdivision = ''
        self.post = ''
        self.name_comp_emp = ''
        self.fio_empl = ''
        self.number_h = ''
        self.content = ''
        self.note = ''
        self.descript = ''
        self.implementat_method = ''
        self.timing_and_mark = ''
        self.start_time = ''
        self.end_time = ''

# создание состояний
class Forms(StatesGroup):
    name = State() # Задаем состояние
    surname = State()
    date_birth = State()

    give_a_role = State()
    del_user = State()

    st_tip_doc = State()
    st_number_doc = State()
    st_date_doc = State()
    st_name_comp_cl = State()
    st_fio_client = State()
    st_subdivision = State()
    st_post = State()
    st_name_comp_emp = State()
    st_fio_empl = State()
    st_number_h = State()
    st_content = State()
    st_note = State()
    st_descript = State()
    st_implementat_method = State()
    st_timing_and_mark = State()
    st_start_time = State()
    st_end_time = State()

# выполнение запросов на select данных
def sql_zapros(zapros):
    cur = con.cursor()
    cur.execute(zapros) # курсор выполняет запрос
    otv = cur.fetchall() # сохранем информацию из запроса к БД в переменную otv
    cur.close()
    return otv

# выполнение запросов на внесение, изменение и удаление
def sql_zapros_insert(zapros):
    cur = con.cursor()
    cur.execute(zapros) # курсор выполняет запрос
    con.commit() # сохранем информацию из запроса к БД в переменную otv
    cur.close()
    return 0

# запрос на select Users
def sql_zapros_role():
    zapros = "select id_usbot, role_user from Users;"
    sp_roles = sql_zapros(zapros)
    return sp_roles

# запрос на заполнение данных из ЛУРВ и ЛТ в бд
def sql_zapros_pechat(docs, flag):

    zapros1 = "INSERT INTO Documents (number_doc, date_doc) " \
              "VALUES (%s, '%s')"
    val = (doc_id, docs.date_doc)
    sql_zapros_insert(zapros1 % val)

    zapros2 = "INSERT INTO Company (name_comp) " \
              "VALUES ('%s')"
    val = docs.name_comp_cl
    sql_zapros_insert(zapros2 % val)

    if flag:
        zapros2_1 = "INSERT INTO Company (name_comp) " \
                  "VALUES ('%s')"
        val = docs.name_comp_emp
        sql_zapros_insert(zapros2_1 % val)

    zapros_v1 = "SELECT id_comp FROM Company WHERE name_comp = '%s'"
    val = docs.name_comp_cl
    otv1 = sql_zapros(zapros_v1 % val)

    otv1_sl = otv1[0]
    id_compani = otv1_sl['id_comp']

    zapros3 = "INSERT INTO Clients (id_comp, fio_client, subdivision, post) VALUES (%s, '%s', '%s', '%s')"

    val = (int(id_compani), docs.fio_client, docs.subdivision, docs.post)
    sql_zapros_insert(zapros3 % val)

    if flag:
        zapros_v2 = "SELECT id_comp FROM Company WHERE name_comp = '%s'"
        val = docs.name_comp_emp
        otv2 = sql_zapros(zapros_v2 % val)

        otv2_sl = otv2[0]
        id_compani_empl = otv2_sl['id_comp']

        zapros4 = "INSERT INTO  Employee (id_comp, fio_empl) VALUES (%s, '%s')"
        val = (int(id_compani_empl), docs.fio_empl)
        sql_zapros_insert(zapros4 % val)

    zapros_v3 = "SELECT id_doc FROM Documents WHERE number_doc = %s"
    val = doc_id
    otv3 = sql_zapros(zapros_v3 % val)

    otv3_sl = otv3[0]
    id_docs = otv3_sl['id_doc']

    zapros_v4 = "SELECT id_client FROM Clients WHERE fio_client = '%s'"
    val = docs.fio_client
    otv4 = sql_zapros(zapros_v4 % val)

    otv4_sl = otv4[0]
    id_clients = otv4_sl['id_client']

    if flag:
        zapros_v5 = "SELECT id_empl FROM Employee WHERE fio_empl = '%s'"
        val = docs.fio_empl
        otv5 = sql_zapros(zapros_v5 % val)

        otv5_sl = otv5[0]
        id_empls = otv5_sl['id_empl']
    else:
        zapros_v6 = "SELECT id_empl FROM Employee WHERE fio_empl != ''"
        otv6 = sql_zapros(zapros_v6)

        otv6_sl = otv6[0]
        id_empls = otv6_sl['id_empl']

        docs.content = ''
        docs.note = ''
        docs.start_time = '00:00'
        docs.end_time= '00:00'

    zapros5 = "INSERT INTO Tasks (id_doc, id_client, id_empl, content, note, descript, implementat_method, timing_and_mark, start_time, end_time, number_h) " \
              "VALUES (%s, %s, %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s)"
    val = (int(id_docs), int(id_clients), int(id_empls), docs.content, docs.note, docs.descript, docs.implementat_method, docs.timing_and_mark, docs.start_time, docs.end_time,
           docs.number_h)
    sql_zapros_insert(zapros5 % val)

# стартовая команда Печать
@dp.message_handler(lambda message: message.text == "Печать")
async def start_pechat(message: types.Message):
    sp_role = sql_zapros_role()

    for i in range(len(sp_role)):
        sp_role_sl = sp_role[i]
        if str(message.from_user.id) == sp_role_sl.get('id_usbot'):
            if (sp_role_sl.get('role_user') == 'Admin') or (sp_role_sl.get('role_user') == 'Employee'):
                btn1 = KeyboardButton(text="На Главную")
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="Жду твоего сообщения").row(btn1)
                await bot.send_message(message.chat.id, "Укажите вид документа, который Вы хотите заполнить:\n"
                                                        "(ЛУРВ или ЛТ)", reply_markup=keyboard)
                await Forms.st_tip_doc.set() # Устанавливаем состояние

# указание вида документа(ЛУРВ и ЛТ)
@dp.message_handler(state=Forms.st_tip_doc)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    global flag
    async with state.proxy() as proxy:# Устанавливаем состояние ожидания
        if message.text == 'ЛТ':
            flag = False
        else:
            flag = True

    if message.text == "На Главную":
        await state.finish()  # Выключаем состояние
        await main_menu(message)
    elif (message.text == 'ЛУРВ') or (message.text == 'ЛТ'):
        await bot.send_message(message.chat.id, text="Введите номер документа")
        await Forms.st_number_doc.set()
    else:
        await message.answer("Вид документа может быть: ЛУРВ или ЛТ")
        await Forms.st_tip_doc.set()
        await message.delete()

# указание номера документа
@dp.message_handler(state=Forms.st_number_doc) # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    global doc_id
    async with state.proxy() as proxy: # Устанавливаем состояние ожидания
        try:
            doc_id = message.text
            doc_data[doc_id] = Docx(message.text)

        except:
            bot.send_message(message.chat.id, "Ошибка")
    if message.text == "На Главную":
        await state.finish()  # Выключаем состояние
        await main_menu(message)
    else:
        await bot.send_message(message.chat.id, text="Введите дату\n"
                                                     "(в формате ГГГГ.ММ.ДД)")
        await Forms.st_date_doc.set()

# указание даты документа
@dp.message_handler(state=Forms.st_date_doc) # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy: # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.date_doc = message.text
            znach_data = docs.date_doc

        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        elif chek_data(znach_data) != 'Все верно':
            await message.answer(f"{chek_data(znach_data)}")
            await Forms.st_date_doc.set()
            await message.delete()
        else:
            await bot.send_message(message.chat.id, text="Введите название компании (заказчика)")
            await Forms.st_name_comp_cl.set()

# указание названия компании (заказчика)
@dp.message_handler(state=Forms.st_name_comp_cl)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.name_comp_cl = message.text

        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        else:
            await bot.send_message(message.chat.id, text="Введите ФИО (заказчика)")
            await Forms.st_fio_client.set()

# указание ФИО (заказчика)
@dp.message_handler(state=Forms.st_fio_client)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.fio_client = message.text
            fio = docs.fio_client
        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        elif chek_fio(fio) != 'Все верно':
            await message.answer("ФИО указано некорректно")
            await Forms.st_fio_client.set()
            await message.delete()
        elif len(fio) > 50:
            await message.answer("Кол-во символов в ФИО заказчика не должно быть больше 50")
            await message.delete()
            await Forms.st_fio_client.set()
        else:
            if flag:
                await bot.send_message(message.chat.id, text="Введите название Организация (исполнителя)")
                await Forms.st_name_comp_emp.set()
            else:
                await bot.send_message(message.chat.id, text="Введите подразделение (заказчика)")
                await Forms.st_subdivision.set()

# указание подразделения (заказчика)
@dp.message_handler(state=Forms.st_subdivision)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.subdivision = message.text

        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        elif len(docs.subdivision) > 30:
            await message.answer("Кол-во символов в подразделении заказчика не должно быть больше 30")
            await message.delete()
            await Forms.st_subdivision.set()
        else:
            await bot.send_message(message.chat.id, text="Введите должность (заказчика)")
            await Forms.st_post.set()

# указание должности (заказчика)
@dp.message_handler(state=Forms.st_post)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.post = message.text

        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        elif len(docs.post) > 30:
            await message.answer("Кол-во символов в должности заказчика не должно быть больше 30")
            await message.delete()
            await Forms.st_post.set()
        else:
            await bot.send_message(message.chat.id, text="Введите кол-во часов")
            await Forms.st_number_h.set()

# указание названия Организация (исполнителя)
@dp.message_handler(state=Forms.st_name_comp_emp)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.name_comp_emp = message.text

        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        else:
            await bot.send_message(message.chat.id, text="Введите ФИО (исполнителя)")
            await Forms.st_fio_empl.set()

# указание ФИО (исполнителя)
@dp.message_handler(state=Forms.st_fio_empl)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.fio_empl = message.text
            fio = docs.fio_empl
        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        elif chek_fio(fio) != 'Все верно':
            await message.answer("ФИО указано некорректно")
            await Forms.st_fio_empl.set()
            await message.delete()
        elif len(fio) > 50:
            await message.answer("Кол-во символов в ФИО исполнителя не должно быть больше 50")
            await message.delete()
            await Forms.st_fio_empl.set()
        else:
            await bot.send_message(message.chat.id, text="Введите кол-во часов")
            await Forms.st_number_h.set()

# указание кол-во часов
@dp.message_handler(state=Forms.st_number_h)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.number_h = message.text

        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        elif chek_number(docs.number_h) == False:
            await message.answer("Укажите арабскими цифрами")
            await message.delete()
            await Forms.st_number_h.set()
        else:
            if flag:
                await bot.send_message(message.chat.id, text="Опишите содержание работ")
                await Forms.st_content.set()
            else:
                await bot.send_message(message.chat.id, text="Описание задачи")
                await Forms.st_descript.set()

# указание содержания работ
@dp.message_handler(state=Forms.st_content)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.content = message.text

        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        elif len(docs.content) > 100:
            await message.answer("Кол-во символов в описании не должно быть больше 100")
            await message.delete()
            await Forms.st_content.set()
        else:
            await bot.send_message(message.chat.id, text="Примечание")
            await Forms.st_note.set()

# указание примечания
@dp.message_handler(state=Forms.st_note)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.note = message.text

        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        elif len(docs.note) > 100:
            await message.answer("Кол-во символов в примечании не должно быть больше 100")
            await message.delete()
            await Forms.st_note.set()
        else:
            await bot.send_message(message.chat.id, text="Время начала работ\n"
                                                         "(в формате 00:00)")
            await Forms.st_start_time.set()

# указание описания задачи
@dp.message_handler(state=Forms.st_descript)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.descript = message.text
        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        else:
            await bot.send_message(message.chat.id, text="Способ реализации")
            await Forms.st_implementat_method.set()

# указание способа реализации
@dp.message_handler(state=Forms.st_implementat_method)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.implementat_method = message.text

        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        elif len(docs.implementat_method) > 100:
            await message.answer("Кол-во символов в способе реализации не должно быть больше 100")
            await message.delete()
            await Forms.st_implementat_method.set()
        else:
            await bot.send_message(message.chat.id, text="Сроки и оценка трудозатрат")
            await Forms.st_timing_and_mark.set()

# указание сроков и оценки трудозатрат и завершение заполнения ЛТ
@dp.message_handler(state=Forms.st_timing_and_mark)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.timing_and_mark = message.text

            sql_zapros_pechat(docs, flag)

            whats_new_url = urljoin(MAIN_DOC_URL, "ЛТ_БЛАНК.docx")
            whats_new_url_n = urljoin(MAIN_DOC_URL, f"ЛТ_заполненые/ЛТ_{doc_id}.docx")

            doc = DocxTemplate(whats_new_url)
            context = {'date': docs.date_doc, 'client': docs.name_comp_cl, 'client_fio': docs.fio_client,
                       'subdivision': docs.subdivision, 'post': docs.post, 'number_h': docs.number_h,
                       'descript': docs.descript, 'implementat_method': docs.implementat_method,
                       'timing_and_mark': docs.timing_and_mark}
            doc.render(context)
            doc.save(whats_new_url_n)

            f1 = open(whats_new_url_n, "rb")
            await bot.send_message(message.chat.id,
                                   text="Поздравляю! Данные сохранены. Вы можете скачать заполненый документ")
            await bot.send_document(message.chat.id, f1)

        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        else:
            await state.finish()  # Выключаем состояние

# указание время начала работ
@dp.message_handler(state=Forms.st_start_time)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            docs = doc_data[doc_id]
            docs.start_time = message.text
            sp_start = docs.start_time.split(":")

        except:
            await bot.send_message(message.chat.id, "Ошибка")

        if message.text == "На Главную":
            await state.finish()  # Выключаем состояние
            await main_menu(message)
        elif (chek_number(sp_start[0]) == False) or (chek_number(sp_start[1]) == False):
            await message.delete()
            await Forms.st_start_time.set()
        elif (int(sp_start[0]) > 23) or (int(sp_start[1]) > 59):
            await message.delete()
            await Forms.st_start_time.set()
        else:
            await bot.send_message(message.chat.id, text="Время окончания работ\n"
                                                         "(в формате 00:00)")
            await Forms.st_end_time.set()

# указание время окончания работ и завершение заполнения ЛУРВ
@dp.message_handler(state=Forms.st_end_time)  # Принимаем состояние
async def pechat(message: types.Message, state: FSMContext):
    global flag
    async with state.proxy() as proxy:# Устанавливаем состояние ожидания
        sp_end = message.text.split(":")

        if (chek_number(sp_end[0]) == False) or (chek_number(sp_end[1]) == False):
            await message.delete()
            await Forms.st_end_time.set()
        elif (int(sp_end[0]) > 23) or (int(sp_end[1]) > 59):
            await message.delete()
            await Forms.st_end_time.set()
        else:
            try:

                docs = doc_data[doc_id]
                docs.end_time = message.text

                sql_zapros_pechat(docs, flag)

                whats_new_url = urljoin(MAIN_DOC_URL, "ЛУРВ_БЛАНК.docx")
                whats_new_url_n = urljoin(MAIN_DOC_URL, f"ЛУРВ_заполненые/ЛУРВ_{doc_id}.docx")

                doc = DocxTemplate(whats_new_url)
                context = {'date': docs.date_doc, 'client': docs.name_comp_cl, 'client_fio': docs.fio_client,
                           'post': docs.post,
                           'name_comp': docs.name_comp_emp, 'fio_empl': docs.fio_empl, 'number_h': docs.number_h,
                           'content': docs.content, 'note': docs.note, 'start_time': docs.start_time,
                           'end_time': docs.end_time}
                doc.render(context)
                doc.save(whats_new_url_n)

                f1 = open(whats_new_url_n, "rb")

                await bot.send_message(message.chat.id,
                                       text="Поздравляю! Данные сохранены. Вы можете скачать заполненый документ")
                await bot.send_document(message.chat.id, f1)
            except:
                await bot.send_message(message.chat.id, "Ошибка")

            if message.text == "На Главную":
                await state.finish()  # Выключаем состояние
                await main_menu(message)
            else:
                await state.finish()  # Выключаем состояние


async def send_to_admin(dp):
    await bot.send_message(chat_id=admin_id, text='Бот запущен')

# Быстрая команда /start, запуск регистрации
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    test = 0
    zapros = "select id_usbot, role_user from Users;"
    sp_role = sql_zapros(zapros)
    for i in range(len(sp_role)):
        sp_role_sl = sp_role[i]
        if str(message.chat.id) == sp_role_sl.get('id_usbot'):
            test = 1
            zapros = "select first_name from Users where id_usbot = '%s';"
            val = str(message.chat.id)
            name = sql_zapros(zapros % val)
            await bot.send_message(message.chat.id, f"Мне кажется, {name[0].get('first_name')}, мы с Вами уже знакомы...")
            break

    if test == 0:
        await bot.send_message(message.chat.id, "Привет! Я бот Пат!\n"
                                                " Давайте знакомиться!\n"
                                                " Как Вас зовут?")
        await bot.send_message(message.chat.id, "Введите имя")
        await Forms.name.set() # Устанавливаем состояние

# указание имени пользователя
@dp.message_handler(state=Forms.name)  # Принимаем состояние
async def start(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        try:
            user_id = message.from_user.id
            user_data[user_id] = User(message.text)
            slovo = message.text
        except:
            bot.send_message(message.chat.id, "Ошибка")
    if chek_bukv(slovo) == False:
        await message.answer("В имени должны быть только буквы!")
        await message.delete()
        await Forms.name.set()
    elif len(slovo) > 30:
        await message.answer("Кол-во символов в имени не должно быть больше 30")
        await message.delete()
        await Forms.name.set()
    else:
        await bot.send_message(message.chat.id, text="Введите фамилию")
        await Forms.surname.set()

# указание фамилии пользователя
@dp.message_handler(state=Forms.surname) # Принимаем состояние
async def start(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy: # Устанавливаем состояние ожидания
        try:
            user_id = message.from_user.id
            user = user_data[user_id]
            user.last_name = message.text
            slovo = user.last_name
        except:
            bot.send_message(message.chat.id, "Ошибка")

    if chek_bukv(slovo) == False:
        await message.answer("В фамилии должны быть только буквы!")
        await message.delete()
        await Forms.surname.set()
    elif len(slovo) > 30:
        await message.answer("Кол-во символов в фамилии не должно быть больше 30")
        await message.delete()
        await Forms.surname.set()
    else:
        await bot.send_message(message.chat.id, text="Введите дату рождения\n"
                                                     "(в формате ГГГГ.ММ.ДД)")
        await Forms.date_birth.set()

# указание даты рождения пользователя
@dp.message_handler(state=Forms.date_birth) # Принимаем состояние
async def start(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy: # Устанавливаем состояние ожидания
        znach_data = message.text
        if chek_data(znach_data) != 'Все верно':
            await message.answer(f"{chek_data(znach_data)}")
            await Forms.date_birth.set()
            await message.delete()
        else:
            user_id = message.from_user.id
            user = user_data[user_id]
            user.date_birth = znach_data

            zapros = "INSERT INTO Users (first_name, last_name, birth_data, id_usbot, role_user) " \
                     "VALUES ('%s', '%s', '%s', '%s', '%s')"
            val = (user.first_name, user.last_name, user.date_birth, user_id, user.role_user)

            sql_zapros_insert(zapros%val)

            await bot.send_message(message.chat.id,
                                   text=f"Поздравляю, {user.first_name}! Вы успешно зарегистрировались!\n"
                                        f" Чтобы перейти в Главное меню введите команду /go или /help")

            await state.finish()  # Выключаем состояние

# запуск быстрой команды /go и /help, открытие Главного меню
@dp.message_handler(commands=['go', 'help'])
@dp.message_handler(lambda message: message.text == "На Главную")
async def main_menu(message: Message):
    btn1 = KeyboardButton(text="Обучение")
    btn2 = KeyboardButton(text="Регламент")
    btn3 = KeyboardButton(text="Ссылки")
    btn4 = KeyboardButton(text="Печать")
    btn5 = KeyboardButton(text="Управление пользователями")

    sp_role = sql_zapros_role()

    for i in range(len(sp_role)):
        sp_role_sl = sp_role[i]
        if str(message.from_user.id) == sp_role_sl.get('id_usbot'):
            if sp_role_sl.get('role_user') == 'Admin':
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="Задай свой вопрос").row(
                    btn1, btn2, btn3
                ).add(btn4, btn5)
                await message.answer("Привет, я бот Пат, задай мне вопрос или выбери пункт Меню",
                                     reply_markup=keyboard)

            elif sp_role_sl.get('role_user') == 'Employee':
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="Задай свой вопрос").row(
                    btn1, btn2, btn3
                ).add(btn4)
                await message.answer("Привет, я бот Пат, задай мне вопрос или выбери пункт Меню",
                                     reply_markup=keyboard)

            elif sp_role_sl.get('role_user') == 'User':
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="Задай свой вопрос").row(
                    btn1)
                await message.answer("Привет, я бот Пат, задай мне вопрос или выбери пункт Меню",
                                     reply_markup=keyboard)

# форма управления пользователями
@dp.message_handler(lambda message: message.text == "Управление пользователями")
async def msg_education(message: types.Message):

    btn1 = KeyboardButton(text="Управление ролями")
    btn2 = KeyboardButton(text="Удаление пользователей")
    btn3 = KeyboardButton(text="На Главную")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="Задай свой вопрос").row(
        btn1, btn2
    ).add(btn3)
    await message.answer("Если навести твердый порядок жёсткой рукой, то ...", reply_markup=keyboard)

# форма управления ролями
@dp.message_handler(lambda message: message.text == "Управление ролями")
async def msg_role(message: types.Message):
    sp_role = sql_zapros_role()

    for i in range(len(sp_role)):
        sp_role_sl = sp_role[i]
        if str(message.from_user.id) == sp_role_sl.get('id_usbot'):
            if sp_role_sl.get('role_user') == 'Admin':
                zapros = "select first_name, last_name, id_usbot from Users;"
                content = sql_zapros(zapros)
                spisok = []
                for j in range(len(content)):
                    content_sl = content[j]
                    spisok.append(content_sl.get('first_name'))
                    spisok.append(content_sl.get('last_name'))
                    spisok.append(content_sl.get('id_usbot'))
                    spisok.append('\n')

                await bot.send_message(chat_id=message.chat.id, text='<b>Как выдать роль?</b>\n\n'
                                                                     '1) Найдите id Пользователя в списке\n'
                                                                     '2) Отправьте его боту\n')
                await bot.send_message(chat_id=message.chat.id, text=' '.join(map(str, spisok)))
            else:
                await message.answer("У Вас не хватает прав...")
    await Forms.give_a_role.set()

# форма добавления и удаления ролей
@dp.message_handler(state=Forms.give_a_role) # Принимаем состояние
async def msg_role(message: types.Message, state: FSMContext):
    global mes
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        ikb = InlineKeyboardMarkup(row_width=2)
        ib1 = InlineKeyboardButton(text='Добавить', callback_data="Добавить роль")
        ib2 = InlineKeyboardButton(text='Удалить', callback_data="Удалить роль")
        ikb.add(ib1, ib2)

        mes = message.text

        await bot.send_message(chat_id=message.chat.id, text='3) Выберите "Добавить роль" или "Удалить роль"', reply_markup=ikb)
        await state.finish()

# форма удаления пользователей
@dp.message_handler(lambda message: message.text == "Удаление пользователей")
async def msg_del(message: types.Message):
    sp_role = sql_zapros_role()

    for i in range(len(sp_role)):
        sp_role_sl = sp_role[i]
        if str(message.from_user.id) == sp_role_sl.get('id_usbot'):
            if sp_role_sl.get('role_user') == 'Admin':
                zapros = "select first_name, last_name, id_usbot from Users;"
                content = sql_zapros(zapros)
                spisok = []
                for i in range(len(content)):
                    content_sl = content[i]
                    spisok.append(content_sl.get('first_name'))
                    spisok.append(content_sl.get('last_name'))
                    spisok.append(content_sl.get('id_usbot'))
                    spisok.append('\n')

                await bot.send_message(chat_id=message.chat.id, text='<b>Как удалить пользователя?</b>\n\n'
                                                                     '1) Найдите id Пользователя в списке\n'
                                                                     '2) Отправьте его боту\n')
                await bot.send_message(chat_id=message.chat.id, text=' '.join(map(str, spisok)))
            else:
                await message.answer("У Вас не хватает прав...")
    await Forms.del_user.set()

# кнопка удаления пользователя
@dp.message_handler(state=Forms.del_user)  # Принимаем состояние
async def msg_del(message: types.Message, state: FSMContext):
    global mes
    async with state.proxy() as proxy:  # Устанавливаем состояние ожидания
        ikb = InlineKeyboardMarkup(row_width=2)
        ib1 = InlineKeyboardButton(text='Удалить', callback_data="Удалить пользователя")
        ikb.add(ib1)

        mes = message.text

        await bot.send_message(chat_id=message.chat.id, text='3) Нажмите "Удалить"',
                               reply_markup=ikb)
        await state.finish()

# форма обучение
@dp.message_handler(lambda message: message.text == "Обучение")
async def msg_education(message: types.Message):

    btn1 = KeyboardButton(text="Курсы")
    btn2 = KeyboardButton(text="Билеты")
    btn3 = KeyboardButton(text="Документация")
    btn4 = KeyboardButton(text="На Главную")

    sp_role = sql_zapros_role()

    for i in range(len(sp_role)):
        sp_role_sl = sp_role[i]
        if str(message.from_user.id) == sp_role_sl.get('id_usbot'):
            if (sp_role_sl.get('role_user') == 'Admin') or (sp_role_sl.get('role_user') == 'Employee'):
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="Задай свой вопрос").row(
                    btn1, btn2).add(btn3).add(btn4)
                await message.reply("Пора ботать!", reply_markup=keyboard)

            elif sp_role_sl.get('role_user') == 'User':
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="Задай свой вопрос").row(
                    btn1, btn2).add(btn4)
                await message.reply("Пора ботать!", reply_markup=keyboard)

# форма билеты
@dp.message_handler(lambda message: message.text == "Билеты")
async def msg_tickets(message: types.Message):

    btn1 = KeyboardButton(text="Билеты БП ПРОФ")
    btn2 = KeyboardButton(text="Билеты БП СПЕЦ-КОНС")
    btn3 = KeyboardButton(text="Билеты БП СПЕЦ")
    btn4 = KeyboardButton(text="На Главную")

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="Задай свой вопрос").row(
        btn1, btn2, btn3
    ).add(btn4)
    await message.answer("Билеты 1С Бухгалтерия предприятия", reply_markup=keyboard)

# отправка билетов БП ПРОФ
@dp.message_handler(lambda message: message.text == "Билеты БП ПРОФ")
async def msg_tickets(message: types.Message):
    try:
        whats_new_url = urljoin(MAIN_DOC_URL, "Билеты_ПРОФ_БП.zip")
        f1 = open(whats_new_url, "rb")
        await message.answer("Билеты 1С БП ПРОФ")
        await bot.send_document(message.chat.id, f1)
    except FileNotFoundError:
        await message.answer("Файл не найден")

# отправка билетов БП СПЕЦ-КОНС
@dp.message_handler(lambda message: message.text == "Билеты БП СПЕЦ-КОНС")
async def msg_tickets(message: types.Message):
    try:
        whats_new_url = urljoin(MAIN_DOC_URL, "Билеты_СПЕЦ-КОНС_БП.zip")
        f2 = open(whats_new_url, "rb")
        await message.answer("Билеты 1С БП СПЕЦ-КОНС")
        await bot.send_document(message.chat.id, f2)
    except FileNotFoundError:
        await message.answer("Файл не найден")

# отправка билетов БП СПЕЦ
@dp.message_handler(lambda message: message.text == "Билеты БП СПЕЦ")
async def msg_tickets(message: types.Message):
    try:
        whats_new_url = urljoin(MAIN_DOC_URL, "Билеты_СПЕЦ_БП.zip")
        f3 = open(whats_new_url, "rb")
        await message.answer("Билеты 1С БП СПЕЦ")
        await bot.send_document(message.chat.id, f3)
    except FileNotFoundError:
        await message.answer("Файл не найден")

# форма ссылки
@dp.message_handler(lambda message: message.text == "Ссылки")
async def msg_links(message: types.Message):
    sp_role = sql_zapros_role()

    for i in range(len(sp_role)):
        sp_role_sl = sp_role[i]
        if str(message.from_user.id) == sp_role_sl.get('id_usbot'):
            if (sp_role_sl.get('role_user') == 'Admin') or (sp_role_sl.get('role_user') == 'Employee'):
                btn1 = KeyboardButton(text="Ссылка К7")
                btn2 = KeyboardButton(text="Ссылка ДО")
                btn3 = KeyboardButton(text="Ссылка Поpтaл")
                btn4 = KeyboardButton(text="Ссылка ИТС")
                btn5 = KeyboardButton(text="На Главную")
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="Задай свой вопрос").row(
                    btn1, btn2, btn3, btn4
                ).add(btn5)
                await message.answer("Куда отправимся?", reply_markup=keyboard)

# отправка ссылки К7
@dp.message_handler(lambda message: message.text == "Ссылка К7")
async def msg_links(message: types.Message):
    text = '[К7](https://zup.1cbit.ru/UP/ru/)'
    await bot.send_message(message.chat.id, text, parse_mode='MarkdownV2')
    await message.delete()

# отправка ссылки ДО
@dp.message_handler(lambda message: message.text == "Ссылка ДО")
async def msg_links(message: types.Message):
    text = '[ДО](https://do.bit-cowork.ru/ProjectManagement/ru/)'
    await bot.send_message(message.chat.id, text, parse_mode='MarkdownV2')
    await message.delete()

# отправка ссылки Портал
@dp.message_handler(lambda message: message.text == "Ссылка Поpтaл")
async def msg_links(message: types.Message):
    text = '[Портал](https://newportal.1cbit.ru)'
    await bot.send_message(message.chat.id, text, parse_mode='MarkdownV2')
    await message.delete()

# отправка ссылки ИТС
@dp.message_handler(lambda message: message.text == "Ссылка ИТС")
async def msg_links(message: types.Message):
    text = '[ИТС](https://its.1c.ru/)'
    await bot.send_message(message.chat.id, text, parse_mode='MarkdownV2')
    await message.delete()

# форма Курсы
@dp.message_handler(lambda message: message.text == "Курсы")
async def msg_curs(message: types.Message):
    btn1 = KeyboardButton(text="Бухучет")
    btn2 = KeyboardButton(text="Администрирование")
    btn3 = KeyboardButton(text="Бухгалтерия")
    btn4 = KeyboardButton(text="Курс ЗУП")
    btn5 = KeyboardButton(text="Курс УТ")
    btn6 = KeyboardButton(text="Программирование")
    btn7 = KeyboardButton(text="На Главную")

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="Задай свой вопрос").row(
        btn1).row(btn2, btn3).row(btn4, btn5).add(btn6).add(btn7)
    await message.answer("Выбираем что поучить!", reply_markup=keyboard)

# форма Документация
@dp.message_handler(lambda message: message.text == "Документация")
async def msg_curs(message: types.Message):
    sp_role = sql_zapros_role()

    for i in range(len(sp_role)):
        sp_role_sl = sp_role[i]
        if str(message.from_user.id) == sp_role_sl.get('id_usbot'):
            if (sp_role_sl.get('role_user') == 'Admin') or (sp_role_sl.get('role_user') == 'Employee'):
                btn1 = KeyboardButton(text="Проектные технологии")
                btn2 = KeyboardButton(text="Матер. при выходе на работу")
                btn3 = KeyboardButton(text="На Главную")

                keyboard = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="Задай свой вопрос").row(
                    btn1, btn2).add(btn3)
                await message.answer("Вот бы почитать...", reply_markup=keyboard)

# отправка материалов по Бухучет
@dp.message_handler(lambda message: message.text == "Бухучет")
async def msg_buhuchet(message: types.Message):
    #whats_new_url = urljoin(MAIN_DOC_URL, "Обучение 1-й бит/1. Бухучет.zip"
    #f1 = open(
    #    whats_new_url,
    #    "rb")
    #await bot.send_document(message.chat.id, f1)
    await message.answer("Ой, здесь пока ничего нет...")
    #await bot.send_document(message.chat.id, f1)

# отправка материалов по Администрирование
@dp.message_handler(lambda message: message.text == "Администрирование")
async def msg_adm(message: types.Message):
    try:
        whats_new_url = urljoin(MAIN_DOC_URL, "Обучение 1-й бит/2. Администрирование.zip")
        f2 = open(
            whats_new_url,
            "rb")
        await bot.send_document(message.chat.id, f2)
    except FileNotFoundError:
        await message.answer("Файл не найден")

# отправка материалов по Бухгалтерия
@dp.message_handler(lambda message: message.text == "Бухгалтерия")
async def msg_buhgal(message: types.Message):
    try:
        whats_new_url = urljoin(MAIN_DOC_URL, "Обучение 1-й бит/3. Бухгалтерия.zip")
        f3 = open(
            whats_new_url,
            "rb")
        await bot.send_document(message.chat.id, f3)
    except FileNotFoundError:
        await message.answer("Файл не найден")

# отправка материалов по Курс ЗУП
@dp.message_handler(lambda message: message.text == "Курс ЗУП")
async def msg_zup(message: types.Message):
    try:
        whats_new_url = urljoin(MAIN_DOC_URL, "Обучение 1-й бит/4. ЗУП.zip")
        f4 = open(
            whats_new_url,
            "rb")
        await bot.send_document(message.chat.id, f4)
    except FileNotFoundError:
        await message.answer("Файл не найден")

# отправка материалов по Курс УТ
@dp.message_handler(lambda message: message.text == "Курс УТ")
async def msg_ut(message: types.Message):
    try:
        whats_new_url = urljoin(MAIN_DOC_URL, "Обучение 1-й бит/5. УТ.zip")
        f5 = open(
            whats_new_url,
            "rb")
        await bot.send_document(message.chat.id, f5)
    except FileNotFoundError:
        await message.answer("Файл не найден")

# отправка материалов по Программирование
@dp.message_handler(lambda message: message.text == "Программирование")
async def msg_programm(message: types.Message):
    try:
        whats_new_url = urljoin(MAIN_DOC_URL, "Обучение 1-й бит/6. Программирование.zip")
        f6 = open(
            whats_new_url,
            "rb")
        await bot.send_document(message.chat.id, f6)
    except FileNotFoundError:
        await message.answer("Файл не найден")

# отправка материалов по Проектные технологии
@dp.message_handler(lambda message: message.text == "Проектные технологии")
async def msg_proect(message: types.Message):
    try:
        whats_new_url = urljoin(MAIN_DOC_URL, "Обучение 1-й бит/7. Проектные технологии.zip")
        f7 = open(
            whats_new_url,
            "rb")
        await bot.send_document(message.chat.id, f7)
    except FileNotFoundError:
        await message.answer("Файл не найден")

# отправка материалов по Матер. при выходе на работу
@dp.message_handler(lambda message: message.text == "Матер. при выходе на работу")
async def msg_mat(message: types.Message):
    try:
        whats_new_url = urljoin(MAIN_DOC_URL, "Обучение 1-й бит/8. Ознакомиться с матер. при выходе на работу.zip")
        f8 = open(
            whats_new_url,
            "rb")
        await bot.send_document(message.chat.id, f8)
    except FileNotFoundError:
        await message.answer("Файл не найден")

# форма Регламент
@dp.message_handler(lambda message: message.text == "Регламент")
async def msg_reg(message: types.Message):
    sp_role = sql_zapros_role()

    for i in range(len(sp_role)):
        sp_role_sl = sp_role[i]
        if str(message.from_user.id) == sp_role_sl.get('id_usbot'):
            if (sp_role_sl.get('role_user') == 'Admin') or (sp_role_sl.get('role_user') == 'Employee'):
                btn1 = KeyboardButton(text="Содержание")
                btn2 = KeyboardButton(text="Глоссарий")
                btn3 = KeyboardButton(text="Скачать регламент")
                btn4 = KeyboardButton(text="На Главную")

                keyboard = ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="Задай свой вопрос").row(
                    btn1, btn2
                ).add(btn3).add(btn4)

                ikb_r = InlineKeyboardMarkup(row_width=1)
                ibr1 = InlineKeyboardButton(text="Глава 1. Начало работы", callback_data="1")
                ibr2 = InlineKeyboardButton(text="Глава 2. Работа с менеджерами и клиентами", callback_data="2")
                ibr3 = InlineKeyboardButton(text="Глава 3. Внутренний документооборот", callback_data="3")
                ibr4 = InlineKeyboardButton(text="Глава 4. Зарплата и К7", callback_data="4")
                ibr5 = InlineKeyboardButton(text="Полезная информация", callback_data="5")
                ikb_r.add(ibr1, ibr2, ibr3, ibr4, ibr5)

                await message.answer('Вы можете посмотреть полное содержание, перейдя по кнопке "Содержание"',reply_markup=keyboard)
                await message.answer("Выбираем главу!", reply_markup=ikb_r)
            else:
                await message.answer("У Вас не хватает прав...")

# открытие содержания регламента
@dp.message_handler(lambda message: message.text == "Содержание")
async def msg_content(message: types.Message):
    zapros = "select text_reg from Regulations where name_chapter = 'Содержание';"
    content = sql_zapros(zapros)
    content_sl = content[0]
    await bot.send_message(chat_id=message.chat.id, text=content_sl.get('text_reg'))

# открытие глоссария регламента
@dp.message_handler(lambda message: message.text == "Глоссарий")
async def msg_glossary(message: types.Message):
    zapros = "select text_reg from Regulations where name_chapter = 'Глоссарий';"
    content = sql_zapros(zapros)
    content_sl = content[0]
    await bot.send_message(chat_id=message.chat.id, text=content_sl.get('text_reg'))

# скачать регламент
@dp.message_handler(lambda message: message.text == "Скачать регламент")
async def msg_download_reg(message: types.Message):
    try:
        whats_new_url = urljoin(MAIN_DOC_URL, "Регламент.docx")
        f1 = open(
            whats_new_url,
            "rb")
        await bot.send_document(message.chat.id, f1)
    except FileNotFoundError:
        await message.answer("Файл не найден")

# инлайн кнопки регламента
@dp.callback_query_handler()
async def pechat_callback(callback: types.CallbackQuery):
    global mes
    if callback.data == '1':
        ikb_1 = InlineKeyboardMarkup(row_width=1)
        ibr1 = InlineKeyboardButton(text='1 Начало работы', url="https://know.bit-cowork.ru/kb-post/1-nachalo-raboty/")
        ibr2 = InlineKeyboardButton(text='1.1 Портал "Первый Бит"', url="https://know.bit-cowork.ru/kb-post/1-1-portal-pervyj-bit/")
        ibr0 = InlineKeyboardButton(text="Выбрать Главу", callback_data="0")
        ikb_1.add(ibr1, ibr2, ibr0)
        await bot.send_message(chat_id=callback.from_user.id, text="Глава 1. Начало работы", reply_markup=ikb_1)
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)

    elif callback.data == '2':
        ikb_2 = InlineKeyboardMarkup(row_width=1)
        ibr1 = InlineKeyboardButton(text='2.1 Пришла информация... Наши действия.', url="https://know.bit-cowork.ru/kb-post/2-1-prishla-informatsiya-o-tom-chto-u-klienta-est-v-chyom-to-interes-nashi-dejstviya-v-zavisimosti-ot-togo-otkuda-prishla-informatsiya-o-interese-klienta/")
        ibr2 = InlineKeyboardButton(text='2.2 Подготовка к общению с клиентом', url="https://know.bit-cowork.ru/kb-post/2-2-podgotovka-k-obshheniyu-s-klientom/")
        ibr3 = InlineKeyboardButton(text='2.3. Первая встреча с клиентом', url="https://know.bit-cowork.ru/kb-post/2-3-pervaya-vstrecha-s-klientom/")
        ibr4 = InlineKeyboardButton(text='2.4. Действия после встречи', url="https://know.bit-cowork.ru/kb-post/2-4-dejstviya-posle-vstrechi/")
        ibr0 = InlineKeyboardButton(text="Выбрать Главу", callback_data="0")
        ikb_2.add(ibr1, ibr2, ibr3, ibr4, ibr0)
        await bot.send_message(chat_id=callback.from_user.id, text="Глава 2. Работа с менеджерами и клиентами",
                               reply_markup=ikb_2)
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)

    elif callback.data == '3':
        ikb_3 = InlineKeyboardMarkup(row_width=1)
        ibr1 = InlineKeyboardButton(text="3.1 Начальная страница", url="https://know.bit-cowork.ru/kb-post/3-1-nachalnaya-stranitsa/")
        ibr2 = InlineKeyboardButton(text="3.2 Описание виджетов", url="https://know.bit-cowork.ru/kb-post/3-2-opisanie-vidzhetov/")
        ibr3 = InlineKeyboardButton(text="3.3 Работа с внутренним докуметооборотом", url="https://know.bit-cowork.ru/kb-post/3-3-rabota-s-vnutrennim-dokumentooborotom-fiksatsiya-trudozatrat/")
        ibr0 = InlineKeyboardButton(text="Выбрать Главу", callback_data="0")
        ikb_3.add(ibr1, ibr2, ibr3, ibr0)
        await bot.send_message(chat_id=callback.from_user.id, text="Глава 3. Внутренний документооборот",
                               reply_markup=ikb_3)
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)

    elif callback.data == '4':
        ikb_4 = InlineKeyboardMarkup(row_width=1)
        ibr1 = InlineKeyboardButton(text="4 Зарплата и К7", url="https://know.bit-cowork.ru/kb-post/glava-4-zarplata-i-k7/")
        ibr2 = InlineKeyboardButton(text="4.1 Расчет ЗП. Категории", url="https://know.bit-cowork.ru/kb-post/4-1-raschet-zarabotnoj-platy-kategorii/")
        ibr3 = InlineKeyboardButton(text="4.2 Просмотр ЗП в К7 и в ДО", url="https://know.bit-cowork.ru/kb-post/4-2-prosmotr-zarabotnoj-platy-v-k7-i-v-nashem-do/")
        ibr0 = InlineKeyboardButton(text="Выбрать Главу", callback_data="0")
        ikb_4.add(ibr1, ibr2, ibr3, ibr0)
        await bot.send_message(chat_id=callback.from_user.id, text="Глава 4. Зарплата и К7", reply_markup=ikb_4)
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)

    elif callback.data == '5':
        ikb_5 = InlineKeyboardMarkup(row_width=1)
        ibr1 = InlineKeyboardButton("Откуда брать информацию о продуктах 1С?", url="https://know.bit-cowork.ru/kb-post/otkuda-brat-informatsiyu-o-produktah-1s/")
        ibr2 = InlineKeyboardButton(text="Правила переписки по почте", url="https://know.bit-cowork.ru/kb-post/pravila-perepiski-po-pochte/")
        ibr3 = InlineKeyboardButton(text="Головной акт и подчиненный акт", url="https://know.bit-cowork.ru/kb-post/golovnoj-akt-i-podchinennyj-akt/")
        ibr0 = InlineKeyboardButton(text="Выбрать Главу", callback_data="0")
        ikb_5.add(ibr1, ibr2, ibr3, ibr0)
        await bot.send_message(chat_id=callback.from_user.id, text="Выбираем дальше!", reply_markup=ikb_5)
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)

    elif callback.data == '0':
        ikb_r = InlineKeyboardMarkup(row_width=1)
        ibr1 = InlineKeyboardButton(text="Глава 1. Начало работы", callback_data="1")
        ibr2 = InlineKeyboardButton(text="Глава 2. Работа с менеджерами и клиентами", callback_data="2")
        ibr3 = InlineKeyboardButton(text="Глава 3. Внутренний документооборот", callback_data="3")
        ibr4 = InlineKeyboardButton(text="Глава 4. Зарплата и К7", callback_data="4")
        ibr5 = InlineKeyboardButton(text="Полезная информация", callback_data="5")
        ikb_r.add(ibr1, ibr2, ibr3, ibr4, ibr5)
        await bot.send_message(chat_id=callback.from_user.id, text="Выбираем главу!", reply_markup=ikb_r)
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)

    else:
        flag = False
        # инлайн кнопки добавления и удаления ролей
        if callback.data == 'Добавить роль':
            try:
                zapros = "select id_usbot, role_user from Users;"
                sp_role = sql_zapros(zapros)
                for i in range(len(sp_role)):
                    sp_role_sl = sp_role[i]
                    if str(mes) == str(callback.from_user.id) or (str(mes) == '1063818709'):
                        flag = True
                        await callback.answer('Вы не можете изменить роль этому пользователю')
                        break
                    elif str(mes) == sp_role_sl.get('id_usbot'):
                        flag = True
                        if sp_role_sl.get('role_user') == 'Admin':
                            await callback.answer('Это Админ. Нельзя выдать роль')
                            break
                        elif sp_role_sl.get('role_user') == 'Employee':
                            zapros1 = "UPDATE Users SET role_user = 'Admin' WHERE id_usbot = '%s'"
                            val = str(mes)
                            sql_zapros_insert(zapros1 % val)
                            await callback.answer('Выдана роль Админ')
                            await bot.send_message(chat_id=mes, text ='Вам выдана роль Админ')
                            break
                        elif sp_role_sl.get('role_user') == 'User':
                            zapros2 = "UPDATE Users SET role_user = 'Employee' WHERE id_usbot = '%s'"
                            val = str(mes)
                            sql_zapros_insert(zapros2 % val)
                            await callback.answer('Выдана роль Сотрудник')
                            await bot.send_message(chat_id=mes, text='Вам выдана роль Сотрудник')
                            break


                if flag == False:
                    await callback.answer('Неверный id')

            except:
                await callback.answer('Введите сначала id сотрудника')

        elif callback.data == 'Удалить роль':
            try:
                zapros = "select id_usbot, role_user from Users;"
                sp_role = sql_zapros(zapros)

                for i in range(len(sp_role)):
                    sp_role_sl = sp_role[i]
                    if str(mes) == str(callback.from_user.id) or (str(mes) == '1063818709'):
                        flag = True
                        await callback.answer('Вы не можете изменить роль этому пользователю')
                        break
                    elif str(mes) == sp_role_sl.get('id_usbot'):
                        flag = True
                        if sp_role_sl.get('role_user') == 'Admin':
                            zapros3 = "UPDATE Users SET role_user = 'Employee' WHERE id_usbot = '%s'"
                            val = str(mes)
                            sql_zapros_insert(zapros3 % val)
                            await callback.answer('Удалена роль Админ')
                            await bot.send_message(chat_id=mes, text='К сожалению, Вы больше не Админ...')
                            break
                        elif sp_role_sl.get('role_user') == 'Employee':
                            zapros4 = "UPDATE Users SET role_user = 'User' WHERE id_usbot = '%s'"
                            val = str(mes)
                            sql_zapros_insert(zapros4 % val)
                            await callback.answer('Удалена роль Сотрудник')
                            await bot.send_message(chat_id=mes, text='К сожалению, Вы больше не Сотрудник...')
                            break
                        elif sp_role_sl.get('role_user') == 'User':
                            await callback.answer('Это Пользователь. Нельзя удалить роль')
                            break

                if flag == False:
                    await callback.answer('Неверный id')


            except:
                await callback.answer('Введите сначала id сотрудника')
        # инлайн кнопка удаления пользователя
        elif callback.data == 'Удалить пользователя':
                ikb = InlineKeyboardMarkup(row_width=2)
                ib1 = InlineKeyboardButton(text='Да, удалить', callback_data="Да, удалить")
                ib2 = InlineKeyboardButton(text='Нет', callback_data="Нет")
                ikb.add(ib1, ib2)
                await callback.answer('Подтвердите действие')
                await bot.send_message(chat_id=callback.from_user.id, text='Удалить пользователя?',
                                       reply_markup=ikb)
        # инлайн кнопки подтверждения удаления пользователя
        elif callback.data == 'Да, удалить':
            try:
                zapros = "select id_usbot, role_user from Users;"
                sp_role = sql_zapros(zapros)

                for i in range(len(sp_role)):
                    sp_role_sl = sp_role[i]
                    if str(mes) == str(callback.from_user.id) or (str(mes) == '1063818709'):
                        flag = True
                        await callback.answer('Вы не можете удалить этого пользователя')
                        break
                    elif str(mes) == sp_role_sl.get('id_usbot'):
                        zapros = "delete from Users where id_usbot = '%s'"
                        val = str(mes)
                        sql_zapros_insert(zapros % val)
                        flag = True
                        await callback.answer('Пользователь удален')

                if flag == False:
                    await callback.answer('Неверный id')

            except:
                await callback.answer('Введите сначала id сотрудника')

        elif callback.data == 'Нет':
            await callback.answer('Правильно! Пусть еще поработает;)')


# функция обработки сообщений отправленных боту
@dp.message_handler(lambda message: True, content_types=['text'])
async def msg(message: Message):
    global mes
    if ({i.lower().translate(str.maketrans('','', string.punctuation)) for i in message.text.split(' ')}\
        .intersection(set(json.load(open('cenz.json')))) != set()):
        await message.answer('Давайте будем культурнее!')
        await message.delete()
    elif message.text == 'Привет':
        await message.answer('Привет!')
    elif message.text == 'Как тебя зовут?':
        await message.answer('Меня зовут Пат')
    elif message.text == 'Как у тебя дела?':
        await message.answer('Хорошо, спасибо')
    else:
        mes = str(message.text)
        sp_role = sql_zapros_role()
        # обработка текста и поиск по регламенту
        for i in range(len(sp_role)):
            sp_role_sl = sp_role[i]
            if str(message.from_user.id) == sp_role_sl.get('id_usbot'):
                if (sp_role_sl.get('role_user') == 'Admin') or (sp_role_sl.get('role_user') == 'Employee'):

                    text = str(message.text).lower()
                    mesg = re.sub(r'[^ а-я]', '', text)
                    stop_words = stopwords.words('russian')
                    var_mes_st = word_tokenize(mesg)
                    var_mes = []
                    morph = pymorphy2.MorphAnalyzer()
                    for word in var_mes_st:
                        if word not in stop_words:
                            var_mes.append(morph.parse(word)[0].normal_form)

                    zapros_NK = "SELECT id_key, key_word FROM NKeys"
                    sp_sl_keys = sql_zapros(zapros_NK)

                    zapros_C_k = "SELECT id_ck, id_chapter, id_key FROM Chapter_key"
                    sp_sl_ck = sql_zapros(zapros_C_k)

                    zapros_Ch = "SELECT id_chapter, name_chapter FROM Chapter"
                    sp_sl_chap = sql_zapros(zapros_Ch)


                    for i in range(len(var_mes)):
                        id_k = 0
                        id_tema = 0
                        tema = ''

                        for j in range(len(sp_sl_keys)):
                            if var_mes[i] == sp_sl_keys[j].get('key_word'):
                                id_k = sp_sl_keys[j].get('id_key')

                        for y in range(len(sp_sl_ck)):
                            if id_k == sp_sl_ck[y].get('id_key'):
                                id_tema = sp_sl_ck[y].get('id_chapter')

                        for q in range(len(sp_sl_chap)):
                            if id_tema == sp_sl_chap[q].get('id_chapter'):
                                tema = sp_sl_chap[q].get('name_chapter')

                        if tema == 'Глава 1':
                            ikbn_1 = InlineKeyboardMarkup(row_width=1)
                            ibr1 = InlineKeyboardButton(text='1 Начало работы',
                                                        url="https://know.bit-cowork.ru/kb-post/1-nachalo-raboty/")
                            ibr2 = InlineKeyboardButton(text='1.1 Портал "Первый Бит"',
                                                        url="https://know.bit-cowork.ru/kb-post/1-1-portal-pervyj-bit/")
                            ikbn_1.add(ibr1, ibr2)
                            await bot.send_message(chat_id=message.from_user.id, text="Нашла \"{0}\" вот здесь:".format(var_mes[i]), reply_markup=ikbn_1)

                        elif tema == 'Глава 2.1':
                            ikbn_2 = InlineKeyboardMarkup(row_width=1)
                            ibr1 = InlineKeyboardButton(text='2.1 Пришла информация... Наши действия.',
                                                        url="https://know.bit-cowork.ru/kb-post/2-1-prishla-informatsiya-o-tom-chto-u-klienta-est-v-chyom-to-interes-nashi-dejstviya-v-zavisimosti-ot-togo-otkuda-prishla-informatsiya-o-interese-klienta/")
                            ikbn_2.add(ibr1)
                            await bot.send_message(chat_id=message.from_user.id, text="Нашла \"{0}\" вот здесь:".format(var_mes[i]),
                                                   reply_markup=ikbn_2)

                        elif tema == 'Глава 2.2':
                            ikbn_2_2 = InlineKeyboardMarkup(row_width=1)
                            ibr1 = InlineKeyboardButton(text='2.2 Подготовка к общению с клиентом', url="https://know.bit-cowork.ru/kb-post/2-2-podgotovka-k-obshheniyu-s-klientom/")
                            ikbn_2_2.add(ibr1)
                            await bot.send_message(chat_id=message.from_user.id, text="Нашла \"{0}\" вот здесь:".format(var_mes[i]),
                                                   reply_markup=ikbn_2_2)

                        elif tema == 'Глава 2.3':
                            ikbn_2_3 = InlineKeyboardMarkup(row_width=1)
                            ibr1 = InlineKeyboardButton(text='2.3. Первая встреча с клиентом', url="https://know.bit-cowork.ru/kb-post/2-3-pervaya-vstrecha-s-klientom/")
                            ikbn_2_3.add(ibr1)
                            await bot.send_message(chat_id=message.from_user.id, text="Нашла \"{0}\" вот здесь:".format(var_mes[i]),
                                                   reply_markup=ikbn_2_3)

                        elif tema == 'Глава 3.1':
                            ikbn_3_1 = InlineKeyboardMarkup(row_width=1)
                            ibr1 = InlineKeyboardButton(text="3.1 Начальная страница", url="https://know.bit-cowork.ru/kb-post/3-1-nachalnaya-stranitsa/")
                            ikbn_3_1.add(ibr1)
                            await bot.send_message(chat_id=message.from_user.id, text="Нашла \"{0}\" вот здесь:".format(var_mes[i]),
                                                   reply_markup=ikbn_3_1)

                        elif tema == 'Глава 3.2':
                            ikbn_3_2 = InlineKeyboardMarkup(row_width=1)
                            ibr1 = InlineKeyboardButton(text="3.2 Описание виджетов", url="https://know.bit-cowork.ru/kb-post/3-2-opisanie-vidzhetov/")
                            ikbn_3_2.add(ibr1)
                            await bot.send_message(chat_id=message.from_user.id, text="Нашла \"{0}\" вот здесь:".format(var_mes[i]),
                                                   reply_markup=ikbn_3_2)

                        elif tema == 'Глава 3.3':
                            ikbn_3_3 = InlineKeyboardMarkup(row_width=1)
                            ibr1 = InlineKeyboardButton(text="3.3 Работа с внутренним докуметооборотом", url="https://know.bit-cowork.ru/kb-post/3-3-rabota-s-vnutrennim-dokumentooborotom-fiksatsiya-trudozatrat/")
                            ikbn_3_3.add(ibr1)
                            await bot.send_message(chat_id=message.from_user.id, text="Нашла \"{0}\" вот здесь:".format(var_mes[i]),
                                                   reply_markup=ikbn_3_3)

                        elif tema == 'Глава 4':
                            ikbn_4 = InlineKeyboardMarkup(row_width=1)
                            ibr1 = InlineKeyboardButton(text="4 Зарплата и К7",
                                                        url="https://know.bit-cowork.ru/kb-post/glava-4-zarplata-i-k7/")
                            ibr2 = InlineKeyboardButton(text="4.1 Расчет ЗП. Категории",
                                                        url="https://know.bit-cowork.ru/kb-post/4-1-raschet-zarabotnoj-platy-kategorii/")
                            ibr3 = InlineKeyboardButton(text="4.2 Просмотр ЗП в К7 и в ДО",
                                                        url="https://know.bit-cowork.ru/kb-post/4-2-prosmotr-zarabotnoj-platy-v-k7-i-v-nashem-do/")
                            ikbn_4.add(ibr1, ibr2, ibr3)
                            await bot.send_message(chat_id=message.from_user.id, text="Нашла \"{0}\" вот здесь:".format(var_mes[i]), reply_markup=ikbn_4)

                        elif tema == 'Глава 5':
                            ikbn_5 = InlineKeyboardMarkup(row_width=1)
                            ibr1 = InlineKeyboardButton("Откуда брать информацию о продуктах 1С?",
                                                        url="https://know.bit-cowork.ru/kb-post/otkuda-brat-informatsiyu-o-produktah-1s/")
                            ibr2 = InlineKeyboardButton(text="Правила переписки по почте",
                                                        url="https://know.bit-cowork.ru/kb-post/pravila-perepiski-po-pochte/")
                            ibr3 = InlineKeyboardButton(text="Головной акт и подчиненный акт",
                                                        url="https://know.bit-cowork.ru/kb-post/golovnoj-akt-i-podchinennyj-akt/")
                            ikbn_5.add(ibr1, ibr2, ibr3)
                            await bot.send_message(chat_id=message.from_user.id, text="Нашла \"{0}\" вот здесь:".format(var_mes[i]), reply_markup=ikbn_5)

                        elif tema == 'Выезд на заявку':
                            try:
                                whats_new_url = urljoin(MAIN_DOC_URL,
                                                        "Обучение 1-й бит/Выезд на заявку.docx")
                                f1 = open(
                                    whats_new_url,
                                    "rb")
                                await bot.send_message(chat_id=message.from_user.id,
                                                       text="Нашла \"{0}\" вот здесь:".format(var_mes[i]))
                                await bot.send_document(message.chat.id, f1)
                            except FileNotFoundError:
                                await message.answer("Файл не найден")

                        elif tema == 'Положение об испытательном сроке':
                            try:
                                whats_new_url = urljoin(MAIN_DOC_URL,
                                                        "Обучение 1-й бит/2017 Положение об испытательном сроке.docx")
                                f2 = open(
                                    whats_new_url,
                                    "rb")
                                await bot.send_message(chat_id=message.from_user.id,
                                                       text="Нашла \"{0}\" вот здесь:".format(var_mes[i]))
                                await bot.send_document(message.chat.id, f2)
                            except FileNotFoundError:
                                await message.answer("Файл не найден")

                        else:
                            mes = str(message.text)
                            await message.answer('Я пока не знаю что такое \"{0}\"...'.format(var_mes[i]))

# ответ на стикер
@dp.message_handler(content_types="sticker")
async def echo_sticker(message: types.Message):
    await message.reply_sticker(message.sticker.file_id)

# ответ на фото
@dp.message_handler(content_types="photo")
async def echo_photo(message: types.Message):
    await message.reply_photo(message.photo[-1].file_id, 'Красиво!')


