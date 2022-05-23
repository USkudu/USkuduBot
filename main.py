import sqlite3
import calendar
import datetime
import os
import re
import config

HELP_MESSAGE = f'''Инструкция бота {config.USERNAME_BOT}\n\n
Ключевые слова - это слова которые должны обязательно состоять в вашем запросе, неважно как сформулирован вопрос, \
хватает написать ключевые слова (порядок неважен) для получения ответа на запрос.\n
Для получения ответов на следующие вопросы необходимо отметить бота {config.USERNAME_BOT}:\n
    Пример: {config.USERNAME_BOT} сегодня пары 
    Для того чтобы узнать: 
        1. Расписание пар на сегодня, ключевые слова:  «пары сегодня»\n
        2. Расписание пар на завтра, ключевые слова:  «пары завтра»\n
        3. Расписание на текущую неделю, ключевое слово:  «расписание»\n
        4. Расписания на недели, ключевое слово:  «расписания»\n
        5. Расписание на определенную неделю, ключевое слово:  «"цифра недели" расписание»\n
        6. Где проходит пара на данный момент времени, ключевые слова:  «где пара»\n
        7. Результаты аттестаций, ключевые слова:  «аттестации | (1|2|3) аттестация»\n
        8. Номер недели, ключевые слова «номер недели»\n
        9. Зачет или экзамен по предмету, ключевые слова «"название предмета"»\n
        10. Список всех предметов, ключевое слово «предметы»\n
        12. Расписание сессии, ключевые слова «сессия | экзамены»\n\n
    Что бы назначить дежурного необходимо выполнить следующие команды:\n
        1. Дежурный на сегодня: Команда /duty\n
        2. В случае если дежурный отсутствует: Команда /next\n
        !!! Необходимо зафиксировать дежурство: Команда /success\n\n
        
        
Как использовать Википедию:\n
    Для обращения к википедии необходимо написать ключевое слово, а затем поисковое.\n
    Ключевое слово «вики | wiki».
    Примеры:
        вики питон
        вики python
        wiki python
        wiki питон'''

START_MESSAGE = '''На что горазд USkudu?

🌈 USkudu знает какие сегодня/завтра пары;
🌈 USkudu может назвать номер текущей недели;
🌈 USkudu знает результаты аттестаций;
🌈 USkudu может отправить расписание;
🌈 USkudu знает по какой дисциплине зачет, а по какой экзамен;
🌈 USkudu знает названия всех предметов;
🌈 USkudu знает когда экзамены;
🌈 USkudu знает кто дежурный;
🌈 USkudu знает где сейчас пара;
🌈 USkudu знает википедию.'''


class TelegramBot:
    def __init__(self):
        self.sqlite_connection = sqlite3.connect('db.sqlite3', check_same_thread=False)
        self.cursor = self.sqlite_connection.cursor()
        self.num_week = self.cursor.execute('SELECT number FROM week').fetchone()[0]
        self.name_week = {1: 'first_', 2: 'second_', 3: 'third_', 4: 'fourth_'}
        self.tz = datetime.timezone(datetime.timedelta(hours=3), name='МСК')
        self.duty_today = ''
        self.students = self.cursor.execute('SELECT name, counter FROM students').fetchall()
        self.set_subjects = {i[0].lower().strip() for i in self.cursor.execute(
            f'''SELECT subjects.name FROM subjects''').fetchall()}

    def today(self):
        """the method that answers the question "what are the pairs today" """
        t = str(datetime.datetime.now(tz=self.tz))[:10]
        t = datetime.datetime.strptime(t, "%Y-%m-%d")
        day_week = calendar.day_name[t.today().weekday()].lower()
        name_table = self.name_week[self.num_week] + day_week
        if day_week == 'sunday':
            return 'Сегодня выходной!'
        data = self.cursor.execute(
            f'''SELECT subjects.name, type, name_teacher, number_auditorium, name_subgroup  
            FROM {name_table} 
            LEFT JOIN subjects ON {name_table}.id_subjects = subjects.id
            LEFT JOIN teachers ON {name_table}.id_teachers = teachers.id
            LEFT JOIN audiences ON {name_table}.id_audiences = audiences.id
            LEFT JOIN type_pair ON {name_table}.id_type_pair = type_pair.id
            LEFT JOIN subgroup ON {name_table}.id_subgroup = subgroup.id''').fetchall()

        answer = ''
        for ind, value in enumerate(data, 1):
            if value[0] is None:
                answer += f'{ind}) ------ \n'
            elif None in value:
                if value[-1] is None and value.count(None) == 1:
                    if '|' not in value[2]:
                        answer += f'{ind}) {" ".join(list(value[:-1]))}\n\n'
                    else:
                        try:
                            name_teacher, number_aud = value[2].split('|'), value[3].split('|')
                            answer += f'''{ind}) {value[0]} {value[1]} \n1я подгруппа {name_teacher[0]} {number_aud[0]}
                            \n2я подгруппа {name_teacher[1]} {number_aud[1]}\n\n'''
                        except:
                            answer += 'Ошибка при заполнении БД\n\n'
                elif value.count(None) == 2:
                    answer += f'{ind}) {" ".join([i for i in value if i is not None])}\n\n'
                else:
                    answer += f'{ind}) {" ".join(["Ошибка при заполнении БД" if i is None else i for i in value])}\n\n'

            else:
                answer += f'{ind}) {" ".join(list(value))}\n\n'
        return answer

    def tomorrow(self):
        """the method that answers the question "what are the pairs tomorrow" """
        days = {'monday': 'tuesday',
                'tuesday': 'wednesday',
                'wednesday': 'thursday',
                'thursday': 'friday',
                'friday': 'saturday',
                'saturday': 'Завтра выходной!',
                'sunday': 'monday'}
        t = str(datetime.datetime.now(tz=self.tz))[:10]
        t = datetime.datetime.strptime(t, "%Y-%m-%d")
        day_week = calendar.day_name[t.today().weekday()].lower()
        if day_week == 'saturday':
            return days[day_week]
        if day_week == 'sunday':
            self.update()
        name_table = self.name_week[self.num_week] + days[day_week]
        data = self.cursor.execute(
            f'''SELECT subjects.name, type, name_teacher, number_auditorium, name_subgroup  
                    FROM {name_table} 
                    LEFT JOIN subjects ON {name_table}.id_subjects = subjects.id
                    LEFT JOIN teachers ON {name_table}.id_teachers = teachers.id
                    LEFT JOIN audiences ON {name_table}.id_audiences = audiences.id
                    LEFT JOIN type_pair ON {name_table}.id_type_pair = type_pair.id
                    LEFT JOIN subgroup ON {name_table}.id_subgroup = subgroup.id''').fetchall()
        answer = ''
        for ind, value in enumerate(data, 1):
            if value[0] is None:
                answer += f'{ind}) ------ \n'
            elif None in value:
                if value[-1] is None and value.count(None) == 1:
                    if '|' not in value[2]:
                        answer += f'{ind}) {" ".join(list(value[:-1]))}\n\n'
                    else:
                        try:
                            name_teacher, number_aud = value[2].split('|'), value[3].split('|')
                            answer += f'{ind}) {value[0]} {value[1]}\n 1я подгруппа {name_teacher[0]} {number_aud[0]}\n 2я подгруппа {name_teacher[1]} {number_aud[1]}\n\n'
                        except:
                            answer += 'Ошибка при заполнении БД\n\n'
                elif value.count(None) == 2:
                    answer += f'{ind}) {" ".join([i for i in value if i is not None])}\n\n'
                else:
                    answer += f'{ind}) {" ".join(["Ошибка при заполнении БД" if i is None else i for i in value])}\n\n'

            else:
                answer += f'{ind}) {" ".join(list(value))}\n\n'
        return answer

    def schedule(self, bot, chat_id, message):
        """the method that answers the question "what is the schedule" """
        l = sorted(os.listdir('media/schedules'))
        num = re.search('[\d]', message)
        if 'расписания' == message:
            for name_file in l:
                with open(os.path.join('media/schedules', name_file), 'rb') as image:
                    bot.send_photo(chat_id, image)
        elif 'расписание' == message:
            for name_file in l:
                if str(self.num_week) in name_file:
                    with open(os.path.join('media/schedules', name_file), 'rb') as image:
                        bot.send_photo(chat_id, image)
                        break
        elif num is not None and 'расписание' in message and 0 < int(num.group()) < 5:
            for name_file in l:
                if str(num.group()) in name_file:
                    with open(os.path.join('media/schedules', name_file), 'rb') as image:
                        bot.send_photo(chat_id, image)
                        break
        else:
            bot.send_message(chat_id, 'Введены некорректные данные!')

    def number_week(self):
        """the method that answers the question "number of the week" """
        data = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}
        return f'{data[self.num_week]}  неделя.'

    def attestations(self, bot, chat_id, message):
        """the method answering the question "attestation" """
        l = sorted(os.listdir('media/attestations'))
        num = re.search('[\d]', message)
        if 'аттестации' in message:
            for name_file in l:
                with open(os.path.join('media/attestations', name_file), 'rb') as image:
                    bot.send_photo(chat_id, image)
        elif num is not None:
            num = num.group()
            for name_file in l:
                if num in name_file:
                    with open(os.path.join('media/attestations', name_file), 'rb') as image:
                        bot.send_photo(chat_id, image)
                        break
            else:
                bot.send_message(chat_id, 'Введены некорректные данные или аттестация отсутствует!')
        else:
            bot.send_message(chat_id, 'Введены некорректные данные или аттестации отсутствуют!')

    def audience_couple(self):
        """the method that answers the question "where is the pair" """
        now_hour = datetime.datetime.now(tz=self.tz).hour
        now_minute = datetime.datetime.now(tz=self.tz).minute
        now_num, num = {1: 'Первая', 2: 'Вторая', 3: 'Третья', 4: 'Четвертая'}, 0
        if now_hour in [8, 9, 10, 11, 12, 13, 14, 15]:
            if now_hour == 8 and now_minute < 20:
                return 'Пара еще не началась!'
            elif now_hour in [8, 9]:
                num = 1
            elif (now_hour == 10 and now_minute > 9) or (now_hour == 11 and now_minute < 40):
                num = 2
            elif (now_hour == 12 and now_minute > 19) or (now_hour == 13 and now_minute < 50):
                num = 3
            elif (now_hour == 14 and now_minute >= 0) or (now_hour == 15 and now_minute < 30):
                num = 4
            if not num:
                return 'Перемена!'
            t = str(datetime.datetime.now(tz=self.tz))[:10]
            t = datetime.datetime.strptime(t, "%Y-%m-%d")
            day_week = calendar.day_name[t.today().weekday()].lower()
            name_table = self.name_week[self.num_week] + day_week
            data = self.cursor.execute(
                f'''SELECT {name_table}.id, subjects.name, type, name_teacher, number_auditorium, name_subgroup  
                FROM {name_table} 
                LEFT JOIN subjects ON {name_table}.id_subjects = subjects.id
                LEFT JOIN teachers ON {name_table}.id_teachers = teachers.id
                LEFT JOIN audiences ON {name_table}.id_audiences = audiences.id
                LEFT JOIN type_pair ON {name_table}.id_type_pair = type_pair.id
                LEFT JOIN subgroup ON {name_table}.id_subgroup = subgroup.id
                WHERE {name_table}.id = {num}''').fetchone()

            if None is not data:
                return f'{num}) ' + ' '.join([i for i in data[1:] if isinstance(i, str)])

            return f'{now_num[num]} пара отсутствует!'

        return 'На данный момент нет пары!'

    def exams(self):
        """the method that answers the question "when are the exams" """
        data = self.cursor.execute(
            f'''SELECT subjects.name, name_teacher, time
                            FROM exams
                            LEFT JOIN subjects ON exams.id_subjects = subjects.id
                            LEFT JOIN teachers ON exams.id_teachers = teachers.id''').fetchall()
        return '\n\n'.join([f'Предмет: {i[0]}\nПреподаватель: {i[1]}\nВремя: {i[2]}' for i in data])

    def test_or_exams(self, name_subj):
        """the method that answers the question "on a certain subject test or exam" """
        data = self.cursor.execute(
            f'''SELECT subjects.name, category_pairs.category
                                    FROM subjects 
                                    LEFT JOIN category_pairs ON subjects.category_id = category_pairs.id''').fetchall()
        for s in data:
            if name_subj == s[0].lower().strip():
                return ' - '.join(s)

    def update(self):

        t = str(datetime.datetime.now(tz=self.tz))[:10]
        t = datetime.datetime.strptime(t, "%Y-%m-%d")
        date_today = t.today().date()
        data = self.cursor.execute('SELECT number, date FROM week').fetchone()
        n, d = data[0], data[1]
        if str(date_today) != str(d):
            self.cursor.execute(f'UPDATE week SET number = {n + 1 if n < 4 else 1}, date = "{date_today}"')
            self.sqlite_connection.commit()
            self.num_week = self.cursor.execute('SELECT number FROM week').fetchone()[0]

    def subjects(self):

        answer = ''
        data = self.cursor.execute(
            f'''SELECT subjects.name, category_pairs.category
                            FROM subjects 
                            LEFT JOIN category_pairs ON subjects.category_id = category_pairs.id
                            ORDER BY category_id''').fetchall()

        for s, c in data:
            answer += f'{s} - {c}\n'

        return answer

    def duty(self):
        std = self.cursor.execute('SELECT name, counter FROM students').fetchall()
        if self.duty_today != '':
            return self.duty_today
        data = min(std, key=lambda x: x[1])
        self.duty_today = data[0]
        return f'Сегодня дежурный: {self.duty_today}'

    def next(self):

        if self.duty_today != '':
            for student in range(len(self.students)):
                if self.students[student][0] == self.duty_today and student + 1 != len(self.students):
                    self.duty_today = self.students[student+1][0]
                    return f'Следующий дежурный: {self.duty_today}'
                elif self.students[student][0] == self.duty_today and student + 1 == len(self.students):
                    self.students = self.students[0][0]
                    return f'Следующий дежурный: {self.duty_today}'

        return 'Необходимо сначала выбрать дежурного! /duty'

    def success(self):

        if self.duty_today != '':
            print(self.duty_today)
            self.cursor.execute(f'''UPDATE students
                                    SET counter = counter + 1
                                    WHERE name = "{self.duty_today}"''')
            self.sqlite_connection.commit()
            self.duty_today = ''
            return 'Дежурство зафиксировано!'

        return 'Необходимо сначала выбрать дежурного! /duty'