import gspread
from oauth2client.service_account import ServiceAccountCredentials
from Prediction import *
from flask import Flask, render_template
from functools import reduce
import os

def determine_eliminated_countries(reality):
    eliminated_countries = set({})
    for group in reality.group_predictions:
        for country in group[2:]:
            eliminated_countries.add(country)

    for i in range(8):
        country1, country2 = reality.ro16[i]
        if reality.ro8[i//2][i%2] != 'nAn':
            if country1 == reality.ro8[i//2][i%2]:
                eliminated_countries.add(country2)
            else:
                eliminated_countries.add(country1)

    for i in range(4):
        country1, country2 = reality.ro8[i]
        if reality.ro4[i//2][i%2] != 'nAn':
            if country1 == reality.ro4[i//2][i%2]:
                eliminated_countries.add(country2)
            else:
                eliminated_countries.add(country1)
    for i in range(2):
        country1, country2 = reality.ro4[i]
        if reality.ro2[i%2] != 'nAn':
            if country1 == reality.ro4[i%2]:
                eliminated_countries.add(country2)
            else:
                eliminated_countries.add(country1)
    return eliminated_countries

def combine_group_outcomes_with_reality(prediction, reality):
    #combined = [['Predicted: ' + chr(i+65), 'Actual:'] for i in range(8)]
    combined = [[['country',j,0] for j in range(6)] for i in range(8)]
    #print(combined)
    overall_score = 0
    for i in range(8):
        tot_score = 0
        predicted_group = prediction.group_predictions[i]
        actual_group = reality.group_predictions[i]
        combined[i][0][0] = 'Predicted: Group ' + chr(i+65)
        combined[i][0][1] = 'Actual:'
        combined[i][0][2] = 'Score:'
        for j in range(4):
            score_str = ''
            predicted_rank = j+1
            actual_rank = actual_group.index(predicted_group[j])+1
            if predicted_rank == actual_rank:
                score_str+='+1'
                tot_score+=1
            else:
                score_str+= ''
            combined[i][j+1][0] = str(j+1) + '. ' + predicted_group[j].title()
            combined[i][j+1][1] = actual_group.index(predicted_group[j])+1
            combined[i][j+1][2] = score_str

        combined[i][5][0] = ''
        combined[i][5][1] = 'TOT:'
        combined[i][5][2] = str(tot_score)
        overall_score+=tot_score

    return combined,overall_score

def combine_last_x_with_reality(title, predicted_x_countries, actual_x_countries, eliminated_countries, bonus):
    tot_score = 0
    pot_score = 0
    table = [[title, 'Score:']]
    for country in predicted_x_countries:
        scorestr = '-'
        if country in actual_x_countries:
            scorestr='+' + str(bonus)
            tot_score+=bonus
        elif country in eliminated_countries:
            scorestr = ''
        else:
            pot_score += bonus
        table.append([country.title(), scorestr])
    table.append(['TOT', str(tot_score)])
    return table, tot_score, pot_score

def create_for(predicted, reality, eliminated_countries):
    group_data, group_score = combine_group_outcomes_with_reality(predicted,reality)
    def r(x,y):
        return x+y
    s_data, s_score, s_pot = combine_last_x_with_reality("Predicted Ro16:", reduce(r,predicted.ro16), reduce(r, reality.ro16), eliminated_countries, 2)
    q_data, q_score, q_pot = combine_last_x_with_reality("Predicted Ro8:", reduce(r,predicted.ro8), reduce(r, reality.ro8), eliminated_countries, 5)
    h_data, h_score, h_pot = combine_last_x_with_reality("Predicted Semi:", reduce(r,predicted.ro4), reduce(r, reality.ro4), eliminated_countries, 7)
    f_data, f_score, f_pot = combine_last_x_with_reality("Predicted Final/Winner:", predicted.ro2, reality.ro2, eliminated_countries, 12)
    f_data = f_data[:-1]
    f_data.append(["Predicted Winner: ", "-"])
    w_string, w_score, w_pot = '-', 0, 0
    if predicted.winner == reality.winner:
        w_string = '+19'
        w_score += 19
    elif predicted.winner in eliminated_countries:
        w_string = ''
    else:
        w_pot +=19
    tot_score = group_score+s_score+q_score+h_score+f_score+w_score
    pot_score = tot_score + s_pot+q_pot+h_pot+f_pot+w_pot
    f_data.append([predicted.winner.title(), w_string])
    f_data.append(["TOT", str(f_score+w_score)])
    for i in range(6):
        f_data.append(['', ''])
    f_data.append(["Scoring Breakdown:", "Pts:"])
    f_data.append(["From Group Stage: ", str(group_score)+'/32'])
    f_data.append(["From Ro16: ", str(s_score)+'/32'])
    f_data.append(["From Quarters: ", str(q_score)+'/40'])
    f_data.append(["From Semi: ", str(h_score)+'/28'])
    f_data.append(["From Final: ", str(f_score)+'/24'])
    f_data.append(["From Champion: ", str(w_score)+'/19'])
    f_data.append(["TOT: ", str(tot_score)+'/175'])
    return (tot_score, predicted.name.strip(), pot_score, group_data, [s_data, q_data, h_data], f_data)

app = Flask(__name__)
data = []
data_dict = {}
name_id = {}

@app.route('/')
def index():
    table = [["Rank: ", "Name: ", "Cur. Score: ", "Max Pot. Score"]]

    for i in range(len(data)):
        table.append([i+1, data[i][1], data[i][0], data[i][2]])
    #print(table)
    return render_template('overall.html', data_table = table, id_table = name_id)

@app.route('/individual/<id>')
def scoresheet(id):
    data_obj = data_dict[int(id)]
    return render_template('individual.html', tot = data_obj[0], name = data_obj[1], pot = data_obj[2], groups = data_obj[3], brackets = data_obj[4], final=data_obj[5])

if __name__ == "__main__":
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    gc = gspread.authorize(credentials)
    doc = gc.open("World Cup Brackets (Collection)")
    reality = Prediction(sheet = doc.get_worksheet(0))
    eliminated_countries = determine_eliminated_countries(reality)
    id = 1
    for filename in os.listdir("predictdata"):
        if ('.txt' in filename):
            cur_predict = Prediction(filename='predictdata/'+filename)
            cur_data = create_for(cur_predict, reality, eliminated_countries)
            data_dict[id] = cur_data
            name_id[cur_data[1].strip()] = str(id)
            data.append(cur_data)
            id+=1


    data.sort(reverse = True)
    app.run()
