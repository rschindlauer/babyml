import pandas as pd
import matplotlib as mpl
# this is so we can create figures on a host without an X server ($DISPLAY not set)
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import collections as matcoll
import matplotlib.ticker as ticker
from matplotlib.patches import Rectangle
import os
import datetime
# import pytz

def daily(filepath, day_range=7, chart_filename='lukey_eating'):
    # merge different feeding types
    df_f = pd.DataFrame.from_csv(os.path.join(filepath, 'Lukas_formula.csv'),
                                              parse_dates=['Time'],
                                              index_col = 'Time')
    df_p = pd.DataFrame.from_csv(os.path.join(filepath, 'Lukas_pumped.csv'),
                                              parse_dates=['Time'],
                                              index_col = 'Time')

    df_raw = pd.concat([df_f, df_p])

    df_all = df_raw.drop('Baby', 1)
    df_all = df_all.drop('Note', 1)

    # convert amount column to real floats
    df_all['Amount'] = df_all['Amount'].str[:-4]
    df_all['Amount'] = df_all['Amount'].astype(float)

    # get date for each row, as a timedelta relative to the latest one
    df_all['day'] = df_all.index.max().date() - df_all.index.date
    # convert timedelta into int
    df_all['day'] = df_all['day'].dt.days

    df = df_all[df_all['day'] < day_range]

    # we need that for the running sums:
    daily_sum = df.groupby(['day'])['Amount'].sum()
    max_sum = daily_sum.max()

    fig, ax = plt.subplots(figsize=(day_range * 3, 10))

    ax.margins(0)
    ax.set_xlim(0, day_range)
    ax.set_ylim(0, 24)

    # running sum bars:
    sum_patches = []
    # sum_lines_width = []
    # running_sum = 0
    current_day = None
    df = df.sort_index()

    sum_color = (0.8, 0.8, 1, 1)

    running_amount = range(0, day_range)

    now = datetime.datetime.now()
    # datetime.datetime.now(pytz.utc).astimezone(tzlocal())
    now_y = now.hour + now.minute / 60.0

    lines = []
    for index, row in df.iterrows():
        
        # amount bars
        x = day_range - row['day'] - 1
        y = index.hour + index.minute / 60.0
        length = x + row['Amount'] / (df['Amount'].max() + 2)
        pair = [(x, y), (length, y)]
        lines.append(pair)
        # add a label:
        plt.text(length, y, row['Amount'], fontsize=16, verticalalignment='center')

        # running sum boxes    
        if row['day'] != current_day:
            running_sum = 0
            current_day = row['day']
            
        last_width = running_sum / max_sum
        box_x = x + last_width
        running_sum += row['Amount']
        width = running_sum / max_sum - last_width
        r = Rectangle((box_x, y), width, 24-y, facecolor=sum_color, edgecolor=sum_color)
        sum_patches.append(r)

        plt.text(length, y + 0.8, running_sum, fontsize=14, color=(0.5, 0.5, 0.5, 1))
        
        if now_y > y:
            running_amount[int(row['day'])] = running_sum

    patchcoll = matcoll.PatchCollection(sum_patches, alpha=0.4, match_original=True)
    ax.add_collection(patchcoll)

    linecoll = matcoll.LineCollection(lines, linewidths = (4,))
    ax.add_collection(linecoll)

    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(4))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(1))

    ax.set_xlabel('days ago', fontsize=16)
    ax.set_ylabel('time', fontsize=16)

    plt.gca().invert_yaxis()

    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")

    plt.rc('xtick', labelsize=18) 
    plt.rc('ytick', labelsize=18) 

    # override x-axis labels to be more intutitive (range..0 days ago instead of 0..range)
    labels = range(0, day_range+1)
    ax.set_xticklabels(labels[::-1])

    # ax.minorticks_on()
    ax.grid(which='minor', linestyle=':', linewidth='0.3', color='grey')
    ax.grid(which='major', linestyle='-', linewidth='0.3', color='grey')

    plt.savefig(chart_filename, bbox_inches='tight')

    print('figure {} created'.format(chart_filename))

    return chart_filename, running_amount

    # plt.show()

