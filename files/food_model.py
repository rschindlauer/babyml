# import pandas as pd
# import matplotlib
# import matplotlib.pyplot as plt
# from io import StringIO
import os
import turicreate as tc
import datetime
# matplotlib.style.use('ggplot')
# %matplotlib inline

DATAFILE_P = 'out_p.csv'
DATAFILE_F = 'out_f.csv'

def import_data(filepath):
    # fix csv files
    with open(os.path.join(filepath, 'Lukas_formula.csv'), 'rt') as fin:
        with open(os.path.join(filepath, DATAFILE_F), 'wt') as fout:
            for line in fin:
                fout.write(line.replace('oz.\n', 'oz.,\n'))
                
    sf_f = tc.SFrame(os.path.join(filepath, DATAFILE_F))

    with open(os.path.join(filepath, './Lukas_pumped.csv'), 'rt') as fin:
        with open(os.path.join(filepath, DATAFILE_P), 'wt') as fout:
            for line in fin:
                fout.write(line.replace('oz.\n', 'oz.,\n'))
                
    sf_p = tc.SFrame(os.path.join(filepath, DATAFILE_P))

    sf_raw = sf_f.append(sf_p)
    sf = sf_raw.remove_columns(['Baby', 'Note'])

    sf['Datetime'] = sf['Time'].apply(lambda t: datetime.datetime.strptime(t, '%m/%d/%y, %I:%M %p'))

    sf['Amount'] = sf['Amount'].apply(lambda a: float(a[:-4]))

    # clean up faulty rows:
    sf = sf[sf['Datetime'] <= datetime.datetime.now()]

    sf = sf.sort('Datetime')

    return sf

def predict(filepath):
    sf = import_data(filepath)

    next_time = [None] * len(sf)
    next_amount = [None] * len(sf)
    feeding_index = [None] * len(sf)
    day = [None] * len(sf)

    lookback = 4

    previous_time = [None] * lookback
    previous_amount = [None] * lookback

    for i in range(0, lookback):
        previous_time[i] = [None] * len(sf)
        previous_amount[i] = [None] * len(sf)

    index = 0
    current_day = sf[0]['Datetime'].timetuple().tm_yday

    for i in range(0, len(sf)):
        for l in range(0, lookback):
            if i > l:
                previous_time[l][i] = (sf[i]['Datetime'] - sf[i-l-1]['Datetime']).seconds
                previous_amount[l][i] = sf[i-l-1]['Amount']

        if i < len(sf) - 1:
            next_time[i] = (sf[i+1]['Datetime'] - sf[i]['Datetime']).seconds
            next_amount[i] = sf[i+1]['Amount']


        index += 1
        
        # reset feeding index when we see a new day
        if sf[i]['Datetime'].timetuple().tm_yday != current_day:
            index = 1
            current_day = sf[i]['Datetime'].timetuple().tm_yday
        
        feeding_index[i] = index
        
        day[i] = current_day
            
    sf['next_time'] = next_time
    sf['next_amount'] = next_amount

    sf['feeding_index'] = feeding_index

    sf['day'] = day

    sf['previous_1_time'] = previous_time[0]
    sf['previous_2_time'] = previous_time[1]
    sf['previous_3_time'] = previous_time[2]
    sf['previous_4_time'] = previous_time[3]

    sf['previous_1_amount'] = previous_amount[0]
    sf['previous_2_amount'] = previous_amount[1]
    sf['previous_3_amount'] = previous_amount[2]
    sf['previous_4_amount'] = previous_amount[3]

    features = ['previous_1_amount', 'previous_2_amount', 'previous_3_amount', 'previous_4_amount',
                'previous_1_time', 'previous_2_time', 'previous_3_time', 'previous_4_time',
                'feeding_index', 'day']

    train = sf.dropna()
    m_time = tc.regression.create(train, target = 'next_time', features = features)
    m_amount = tc.regression.create(train, target = 'next_amount', features = features)

    # we want to predict the feeding after the most recent one:
    last_pick = 1
    next_delta = m_time.predict(sf[-last_pick])
    next_time = sf[-last_pick]['Datetime'] + datetime.timedelta(seconds=next_delta[0])

    next_amount = m_amount.predict(sf[-last_pick])

    return (next_time, next_amount[0])