'''
Чтобы сгенерировать токен и ключ перейди сюда: https://trello.com/app-key
по ссылке находится ключ (ВАНЯ) и дальше жми "сгенерируйте токен вручную" 
чтобы получить ТОКЕН. вставь эти значения в токен и кей
'''

import json
import pandas as pd
from requests import request
import datetime as dt
import os

class Board:
    ''' Names: Asklepius, Scaner, TEST'''
    def __init__(self, name):
        self.token = 'token'                    #<========== token ======================
        self.key = 'key'                        #<=========== key =======================
        boards = {
            'Scaner':       'nKcVU64e',
            'Asklepius':    'np24rG0z',
            'TEST':         '6IYvOZMy'
        }
        self.board = boards[name]
        url = f'https://api.trello.com/1/board/{self.board}?key={self.key}&token={self.token}&cards=open&lists=open&member=true&member_fields=all'

        r = request(method='GET', url=url)
        None if r.status_code == 200 else print(r.status_code)
        self.data = json.loads(r.text)

        self.init_members()
        self.init_cards()
        self.init_lists()
        self.add_cards_to_lists()
        self.lists_labels = [lst.name for lst in self.lists]
        
    def init_members(self):
        url = f'https://api.trello.com/1/board/{self.board}/memberships?key={self.key}&token={self.token}&member_fields=all'
        r = request(method='GET', url=url)
        j = json.loads(r.text)
        ids = [user['idMember'] for user in j]
        users = {}
        for id in ids:
            url = f'https://api.trello.com/1/members/{id}'
            r = request(method='GET', url=url)
            data = json.loads(r.text)
            name = data['fullName']
            users[id] = name
        self.members = users

    def init_lists(self):
        self.lists = [List(lst) for lst in self.data['lists']]

    def init_cards(self):
        self.cards = [Card(card) for card in self.data['cards']]
        for card in self.cards:
            members_id = card['idMembers']
            card.data['responsibles'] = [self.members[i] for i in members_id]
            card.responsibles = card.data['responsibles']
    
    def add_cards_to_lists(self):
        for lst in self.lists:
            for card in self.cards:
                if card['idList'] == lst['id']:
                    lst.add_card(card)
    
    def get_cards_of(self, list_key, *attributes):
        for i in self.lists:
            if i.name == list_key:
                return i.cards
       
class List:
    def __init__(self, d):
        self.data = d
        self.cards = []
        self.name = self.data['name']

    def __getitem__(self, key): return self.data[key]
    def add_card(self, card): self.cards.append(card)

class Card:
    def __init__(self,d):
        self.data = d
        self.name = self.data['name']
        self.url = self.data['shortUrl']
        self.responsibles = []

    def __getitem__(self, key): return self.data[key]
    def __str__(self): return self.data['name']


class ReportMaker:
    
    def __init__(self, board, list_of_incompleted, lists_of_completed):
        self.board = board
        dnow = dt.datetime.today()
        delta = dt.timedelta(days=7)
        dago = dnow - delta
        self.period = f'{dago.day}.{dago.month}.{dago.year}-{dnow.day}.{dnow.month}.{dnow.year}'


        self.list_of_incompleted = list_of_incompleted
        self.lists_of_completed = lists_of_completed
        self.incomplete_cards = []
        self.complete_cards = []

        for lst in self.board.lists:

            if lst.name in self.list_of_incompleted:
                for card in lst.cards:
                    card_text = f'{card.name} {card.url} {card.responsibles}'
                    self.incomplete_cards.append(card_text)

            if lst.name in self.lists_of_completed:
                for card in lst.cards:
                    card_text = f'{card.name} {card.url} {card.responsibles} '
                    self.complete_cards.append(card_text)

        status = {
            'incomplete': self.incomplete_cards,
            'complete': self.complete_cards
        }
        self.make_json(status, self.period)

        statuses = os.listdir('statuses')
        fn1, fn2 = statuses[-1], statuses[-2]
        fn1 = f'statuses/{fn1}'
        fn2 = f'statuses/{fn2}'
        self.diff = self.difference(fn1, fn2)
        self.make_txt()

    def difference(self, fn1, fn2):
        with open(fn2, 'r', encoding='utf-8') as file:
            f2 = json.load(file)
        with open(fn1, 'r', encoding='utf-8') as file:
            f1 = json.load(file)
        diff = {
            'Added': set(f1['incomplete']) - set(f2['incomplete']),
            'Completed': set(f1['complete']) - set(f2['complete'])
            }
        return diff

    def make_txt(self):
        report = f'Отчёт по карточкам за период {self.period}:\n\n'
        report += 'Добавленные на следующую неделю задачи:\n\n'

        for card in self.diff['Added']:
            report += card + '\n'

        report += '\n\nВыполненные за неделю задачи:\n\n'
        
        for card in self.diff['Completed']:
            report += card + '\n'

        with open(f'reports/{self.period}.txt', 'w', encoding='utf-8') as file:
            file.write(report)

    def make_json(self, report, period):
        with open(f'statuses/{period}.json', 'w', encoding='utf-8') as file:
            json.dump(report, file)

if __name__ == '__main__':
    board = Board('Scaner')
    rpmkr = ReportMaker(
        board=board,
        list_of_incompleted=['ICE BOX', 'EMERGENCY', 'IN PROGRESS', 'В ОФИСЕ', 'TESTING'],
        lists_of_completed=['COMPLETE', 'ARCHIVE'])
