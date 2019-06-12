import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
import matplotlib.axes as ax


# obtain paths to CSVs from command line
parser = argparse.ArgumentParser(description='Get path to web traffic CSV and spot data CSV')
parser.add_argument('path_spot_data',type=str, help='path to spot data CSV file')
parser.add_argument('path_web_data',type=str, help='path to web traffic CSV file')
args = parser.parse_args()
path_spot_data = args.path_spot_data
path_web_data = args.path_web_data


def cleanDataFrames(path_spot_data, path_web_data):
    ''' takes in paths to CSVs and will return Pandas DFs ready for use '''
    # read CSVs into pandas
    web_data = pd.read_csv(path_web_data)
    spot_data = pd.read_csv(path_spot_data)
    # convert time columns of both DFs to pandas datetime variable
    web_data['datetime'] = pd.to_datetime(web_data['time'], utc=True)
    spot_data['datetime'] = pd.to_datetime(spot_data['time'], utc=True)
    web_data['date'] = web_data['datetime'].dt.date
    spot_data['date'] = spot_data['datetime'].dt.date
    web_data.drop('time', axis=1)
    spot_data.drop('time',axis=1)
    # create new dataframe with only direct traffic
    web_direct = web_data[web_data.traffic_source == 'direct'][['datetime','value']]
    return web_data, spot_data, web_direct


def generateVisitsPlot(datetime_start, datetime_end, dataframe, fig_name):
    ''' takes a datetime start & end (strings), a dataframe, and figure name and returns plot of website visits in that interval called fig_name '''
    sns.set(rc={'figure.figsize':(11, 4)})
    plot = dataframe.plot(x='datetime',y='value')
    plot.set_xlim(pd.Timestamp(datetime_start), pd.Timestamp(datetime_end))
    if (pd.Timestamp(datetime_end) - pd.Timestamp(datetime_start)).days == 0:
        plot.set_xlabel('Datetime [hour]:[minute]')
        plot.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    else:
        plot.set_xlabel('Datetime [date]:[hour]:[minute]')
        plot.xaxis.set_major_formatter(mdates.DateFormatter('%D:%H:%M'))
    plot.set_ylabel('Number of Visits')
    plot.set_title('Website Visits (Traffic Source = Direct) From {} UTC'.format(datetime_start + ' to ' + datetime_end))
    max_y_interval = dataframe[(dataframe.datetime >= pd.Timestamp(datetime_start)) & (dataframe.datetime <= pd.Timestamp(datetime_end))]['value'].max()
    plot.set_ylim(0,(max_y_interval + 50))
    plt.savefig(('{}.png').format(fig_name))
    return plot

def main():
    # retrieve clean dataframes
    web_data, spot_data, web_direct = cleanDataFrames(path_spot_data,path_web_data)
    # create dictionary {creative_id: spend}
    spend_per_creative = (spot_data.groupby('creative_id')['spend'].agg('sum')).to_dict()
    for key in spend_per_creative:
        spend_per_creative[key] = round(spend_per_creative[key],2)
    visits_plot = generateVisitsPlot('2017-11-13 02:00:00+00','2017-11-13 02:20:00+00',web_direct,'visits')
    visits_plot.vlines('2017-11-13 02:12:11+00',0,1500, color='r', label='Spot at 2017-11-13 02:12:11+00')
    visits_plot.vlines('2017-11-13 02:13:12+00',0,1500, color='r', label='Spot at 2017-11-13 02:13:12+00')
    plt.legend()
    plt.show()
    

    # 2017-11-12 18:12:11-08:00
    # 2017-11-12 18:13:12-08:00
if __name__ == '__main__':
    main()
