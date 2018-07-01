from difflib import get_close_matches
import os

countries = [
            ['russia', 'egypt', 'saudi arabia', 'uruguay'],
            ['spain', 'portugal', 'morocco', 'iran'],
            ['france', 'denmark', 'australia', 'peru'],
            ['argentina', 'croatia', 'nigeria', 'iceland'],
            ['brazil', 'switzerland', 'serbia', 'costa rica'],
            ['mexico', 'germany', 'sweden', 'south korea'],
            ['england', 'belgium', 'panama', 'tunisia'],
            ['poland', 'senegal', 'japan', 'colombia']
            ]

def get_closest_country(word, possibilities, spelling_errors = {}):
    if word == 'sk' or word == 's. korea' or word == 's korea' :
        word = 'south korea'
    elif word == 'saudi':
        word = 'saudi arabia'
    elif word == 'brasil':
        word = 'brazil'
    elif word == 'swiss':
        word = 'switzerland'
    cur_country = (get_close_matches(word, possibilities, 1, cutoff = 0.2) + ['nAn'])[0]
    if word != cur_country:
        if cur_country not in spelling_errors:
            spelling_errors[cur_country] = [word]
        else:
            spelling_errors[cur_country].append(word)
    return cur_country

def write_line(f, line):
    f.write(list_to_str(line) + '\n')
def list_to_str(lst):
    s = ''
    for x in lst:
        s+=str(x) + ','
    return s

class Prediction:
    def __init__(self, sheet = None, filename = None):
        self.name = ''
        self.group_predictions = [[str(i)+''+str(j) for j in range(4)]
                        for i in range(8)]
        self.ro16 = [[self.group_predictions[2*i%8][i//4],
                        self.group_predictions[(2*i+1)%8][(i//4+1)%2]]
                        for i in range(8)]
        self.ro8 = [[str(i) + '0', str(i) + '1'] for i in range (4)]
        self.ro4 = [[str(i) + '0', str(i) + '1'] for i in range (2)]
        self.ro2 = ['0', '1']
        self.winner = ''
        self.spelling_errors = {}
        if sheet:
            self.initialize_prediction_from_sheets(sheet)
            self.write_to_file()
        else:
            self.intialize_prediction_from_file(filename)
    def initialize_prediction_from_sheets(self,wks):
        self.name = wks.title
        group_picks_col = wks.col_values(1)
        ro8_picks_col = wks.col_values(5)
        ro4_picks_col = wks.col_values(7)
        ro2_picks_col = wks.col_values(9)
        for i in range(8):
            start_index = 5*i+2
            for j in range(4):
                in_string = group_picks_col[j+start_index].strip().lower()
                cur_country = get_closest_country(in_string, countries[i], self.spelling_errors)

                if not cur_country in countries[i]:
                    print ('group', cur_country)
                self.group_predictions[i][j] = cur_country

        self.ro16 = [[self.group_predictions[2*i%8][i//4],
                        self.group_predictions[(2*i+1)%8][(i//4+1)%2]]
                        for i in range(8)]

        for i in range(4):
            start_index = 8*i + 5 -1
            for j in range(2):
                in_string = ro8_picks_col[j+start_index].strip().lower()
                cur_country = get_closest_country(in_string, self.ro16[2*i+j], self.spelling_errors)
                if not cur_country in self.ro16[2*i+j]:
                    print ('8', cur_country, in_string, self.ro16[2*i+j])
                self.ro8[i][j] = cur_country
        for i in range(2):
            start_index = 14*i + 8 - 1
            for j in range(2):
                in_string = ro4_picks_col[j+start_index].strip().lower()
                cur_country = get_closest_country(in_string, self.ro8[2*i+j], self.spelling_errors)
                if not cur_country in self.ro8[2*i+j]:
                    print ('4', cur_country)
                self.ro4[i][j] = cur_country
        start_index = 14-1
        for j in range(2):
            in_string = ro2_picks_col[j+start_index].strip().lower()
            cur_country = get_closest_country(in_string, self.ro4[j], self.spelling_errors)
            if not cur_country in self.ro4[j]:
                print ('2', cur_country)
            self.ro2[j] = cur_country
        in_string = wks.cell(15,10).value.strip().lower()
        self.winner = get_closest_country(in_string, self.ro2, self.spelling_errors)

        if not self.winner in self.ro2:
            print ('winner', self.winner)
    def intialize_prediction_from_file(self, filename):
        with open(filename, 'r') as f:
            count = 0
            for line in f:
                if count == 0:
                    self.name = line
                elif count >= 1 and count <= 8:
                    for i in range(4):
                        self.group_predictions[count-1][i] = line.split(",")[i]
                elif count >= 9 and count <= 16:
                    for i in range(2):
                        self.ro16[count-9][i] = line.split(",")[i]
                elif count >= 17 and count <= 20:
                    for i in range(2):
                        self.ro8[count-17][i] = line.split(",")[i]
                elif count >= 21 and count <= 22:
                    for i in range(2):
                        self.ro4[count-21][i] = line.split(",")[i]
                elif count == 23:
                    for i in range(2):
                        self.ro2[i] = line.split(",")[i]
                elif count == 24:
                    self.winner = line
                elif count>24:
                    words = line.split(",")
                    self.spelling_errors[line[0]] = line[1:]
                count+=1
    def write_to_file(self):
        script_dir = os.path.dirname(__file__)
        with open('predictdata/' + self.name + '.txt', 'w+') as f:
            f.write(self.name + '\n')
            for line in self.group_predictions:
                write_line(f,line)
            for line in self.ro16:
                write_line(f,line)
            for line in self.ro8:
                write_line(f,line)
            for line in self.ro4:
                write_line(f,line)
            write_line(f,self.ro2)
            f.write(self.winner + '\n')
            for key in self.spelling_errors.keys():
                s = key
                for word in self.spelling_errors[key]:
                    s+= ' ' + word
                f.write(s + '\n')
