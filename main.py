from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QTextEdit, QLabel, QComboBox, QLineEdit
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import sys
import csv

YES = 2
PROBABLY = 1
DONTKNOW = 0
PROBABLYNOT = -1
NO = -2


class UI_poke20(QMainWindow):
    def __init__(self):
        super(UI_poke20, self).__init__()
        uic.loadUi("pokemonguess20.ui", self)
        widget_dict = {'yesBUTT': ['clicked', QPushButton],
                       'probablyBUTT': ['clicked', QPushButton],
                       'dontknowBUTT': ['clicked', QPushButton],
                       'probablynotBUTT': ['clicked', QPushButton],
                       'noBUTT': ['clicked', QPushButton],
                       'questionTB': [None, QTextEdit],
                       'restartBUTT': ['clicked', QPushButton],
                       'questionsleftTB': [None, QLineEdit]}

        for widget, _list in widget_dict.items():
            verb, wtype = _list
            self.__dict__[widget] = self.findChild(wtype, widget)
            if verb != None:
                self.__dict__[widget].clicked.connect(getattr(self, verb + '_' + widget))
        self.q_already_queued = False
        self.show()
        self.new_game()

    def clicked_yesBUTT(self):
        if type(self.cur_question).__name__ == 'q_is_name':
            self.questionTB.setText(
                'I win!')
            return None
        self.answer_question(YES)

    def clicked_probablyBUTT(self):
        self.answer_question(PROBABLY)

    def clicked_dontknowBUTT(self):
        # TODO add counter and push 'unknown' if reached 10 unknown
        self.unknown_ct += 1  # this is  gonna introduce a hard to create bug
        self.answer_question(DONTKNOW)
        if int(self.unknown_ct) == 10:
            result = any('q_is_name' == type(self.cur_question).__name__ for question in self.questions)
            if not result: self.questions.append(q_is_name(self.top_series))
            self.cur_question = self.questions[-1]
            self.cur_question.cur_arg = 'unown'
            self.questionTB.setText(self.cur_question.getText())

    def clicked_probablynotBUTT(self):
        self.answer_question(PROBABLYNOT)

    def clicked_noBUTT(self):
        self.answer_question(NO)

    def clicked_restartBUTT(self):
        self.new_game()

    def new_game(self):
        self.weighted_guesses = []
        self.questions = []
        for question in self.questions:
            self.questions.remove(question)
            del question
        self.questions = [q_is_type(),  # q_is_color(),
                          q_name_start_with(), q_is_evolved(),
                          q_is_generation()]
        for i in range(0, len(natdex) - 1):
            self.weighted_guesses.append([0, i])
        self.top_series = self.weighted_guesses
        self.questions_left = 20
        self.questionsleftTB.setText(str(self.questions_left))
        self.set_best_question()

        # === Dumb things ===
        self.unknown_ct = 0

    def set_best_question(self):
        champ_percent = 2
        if self.q_already_queued:
            self.q_already_queued = False
        else:
            for question in self.questions:
                percentage = question.set_best_arg(self.top_series)
                print(f" {type(question).__name__} : {percentage}")
                percentage = abs(percentage - 0.5)
                if percentage < champ_percent:
                    champ_percent = percentage
                    champ = question
            self.cur_question = champ
        self.questionTB.setText(self.cur_question.getText())

    def answer_question(self, answer):
        func = self.cur_question.bool_func
        arg = self.cur_question.cur_arg
        for guess in self.weighted_guesses:
            weight, index = guess
            record = natdex[index]
            if func(record, arg):
                posneg = 1
            else:
                posneg = -1
            delta = min(answer * posneg, 0)
            guess[0] += delta * self.cur_question.multi
        self.cur_question.reduce_args()

        try:
            self.update_top_series()
        except:
            print('haha')
        self.questions_left -= 1
        self.questionsleftTB.setText(str(self.questions_left))
        self.set_best_question()

    def update_top_series(self):
        self.weighted_guesses.sort(reverse=True)
        refval = self.weighted_guesses[0][0]
        i = 1
        while refval == self.weighted_guesses[i][0]:  # ERROR HERE DUMMY
            i += 1
        last_in_series = i
        self.top_series = self.weighted_guesses[0:last_in_series]
        # add q_is_name to questions if top_series is small
        if len(self.top_series) < 6:  # and not any(isinstance(x, q_is_name) for x in self.questions):
            for question in self.questions:
                print('a')
                if type(question).__name__ == "q_is_name":
                    self.questions.remove(question)
                    del question
            self.questions.append(q_is_name(self.top_series))
        if len(self.top_series) == 1:
            for question in self.questions:
                if type(question).__name__ == "q_is_name":
                    self.cur_question = question
            self.cur_question.set_best_arg(self.top_series)
            self.q_already_queued = True


class question():
    def set_best_arg(self, series):
        champ_percent = 2
        for arg in self.potential_args:
            # want closest to 0.5
            percentage = calculate_percent_true(series, self.bool_func, arg)
            if abs(percentage - 0.5) < abs(champ_percent - 0.5):
                champ_percent = percentage
                champ = arg
        self.cur_arg = champ
        return champ_percent

    def reduce_args(self):
        self.potential_args.remove(self.cur_arg)
        # Special case for potential_args as empty
        if len(self.potential_args) == 0:
            UI.questions.remove(self)
            del self


class q_is_type(question):
    def __init__(self):
        super().__init__()
        self.bool_func = is_type
        self.potential_args = ['Bug', 'Dark', 'Dragon',
                               'Electric', 'Fighting', 'Fire',
                               'Flying', 'Ghost', 'Grass',
                               'Ground', 'Ice', 'Normal',
                               'Poison', 'Psychic', 'Rock',
                               'Steel', 'Water']
        self.cur_arg = None
        self.multi = 2

    def getText(self):
        return f"is your pokemon a(n) {self.cur_arg} type?"


class q_is_color(question):  # This question is bad
    def __init__(self):
        super().__init__()
        self.bool_func = is_color
        self.potential_args = ['Black', 'Blue', 'Brown',
                               'Gray', 'Green', 'Pink',
                               'Purple', 'Red', 'White',
                               'Yellow']
        self.cur_arg = None
        self.multi = 1

    def getText(self):
        return f"is your pokemon {self.cur_arg}?"


class q_name_start_with(question):
    def __init__(self):
        super().__init__()
        self.bool_func = name_start_with
        self.potential_args = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                               'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
                               'Y', 'Z']
        self.cur_arg = None
        self.multi = 2

    def getText(self):
        return f"does your pokemon's name start with the letter '{self.cur_arg}'?"


class q_is_evolved(question):
    def __init__(self):
        super().__init__()
        self.bool_func = is_evolved
        self.potential_args = [None]
        self.cur_arg = None
        self.multi = 2

    def getText(self):
        return f"is your pokemon an evolved form of another pokemon?"


class q_is_name(question):
    def __init__(self, series):
        super().__init__()
        self.bool_func = is_name
        self.potential_args = []
        for guess in series:
            index = guess[1]
            self.potential_args.append(natdex[index][get_col('Pokemon')])
        print(self.potential_args)
        self.cur_arg = None
        self.multi = 10

    def getText(self):
        return f"is your pokemon {self.cur_arg}?"


class q_is_generation(question):
    def __init__(self):
        super().__init__()
        self.bool_func = is_generation
        self.potential_args = ["1st", "2nd", "3rd", "4th", "5th"]
        self.cur_arg = None
        self.multi = 2

    def getText(self):
        return f"is your pokemon from the {self.cur_arg} generation"


# ==== BOOL FUNCTIONS ====
def is_type(record, arg):
    if record[get_col('Type I')] == arg or record[get_col('Type II')] == arg:
        return True
    return False


def is_color(record, arg):
    if record[get_col('Color')] == arg:
        return True
    return False


def name_start_with(record, arg):
    if record[get_col('Pokemon')][0] == arg:
        return True
    return False


def is_evolved(record, arg):
    value = record[get_col('Evolve')]
    if (len(value) != 0) and (value != 'N'):
        return True
    return False


def is_name(record, arg):
    if record[get_col('Pokemon')] == arg:
        return True
    return False


def is_generation(record, arg):
    value = record[get_col('Generation')]
    return arg == value  # Oh that's better


# == helpers ==
def get_col(fieldname):
    return natdex[0].index(fieldname)


def calculate_percent_true(series, bool_func, arg):
    total = 0
    for item in series:
        _, index = item
        record = natdex[index]
        if bool_func(record, arg):
            total += 1
    return round(total / len(series), 2)


natdex = []
with open('natdex.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        natdex.append(row)

app = QApplication(sys.argv)
UI = UI_poke20()
app.exec()
