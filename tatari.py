import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates


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


def generatePlot(datetime_start, datetime_end, dataframe):
    ''' takes a datetime interval (strings) and a dataframe and returns plot of website visits in that interval '''
    sns.set(rc={'figure.figsize':(11, 4)})
    plot = web_direct.plot(x='datetime',y='value')
    plot.set_xlim(pd.Timestamp('2017-11-12 23:23:00+00'), pd.Timestamp('2017-11-12 23:50:00+00'))
    plot.set_xlabel('datetime: [date] [hour]:[minute]')
    plot.set_ylabel('value')
    plot.set_title('Website visits (direct) on 11/12/2017')
    plot.xaxis.set_minor_locator(mdates.HourLocator())
    plot.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plot.set_ylim(0,500)
    plt.show()


def main():
    web_data, spot_data, web_direct = cleanDataFrames(path_spot_data,path_web_data)
    #creative_ids = spot_data.creative_id.unique()
    #programs = spot_data.program.unique()
    #network_codes = spot_data.network_code.unique()
    #rotations = spot_data.rotation.unique()
    #rotation_days = spot_data.rotation_days.unique()
    #rotation_start = spot_data.rotation_start.unique()
    #rotation_end = spot_data.rotation_end.unique()
    sns.set(rc={'figure.figsize':(11, 4)})
    #x_ax = pd.Series(web_direct['datetime'])
    #y_ax = pd.Series(web_direct['value'])
    plot = web_direct.plot(x='datetime',y='value')
    plot.set_xlim(pd.Timestamp('2017-11-12 23:23:00+00'), pd.Timestamp('2017-11-12 23:50:00+00'))
    plot.set_xlabel('datetime: [date] [hour]:[minute]')
    plot.set_ylabel('value')
    plot.set_title('Website visits (direct) on 11/12/2017')
    plot.xaxis.set_minor_locator(mdates.HourLocator())
    plot.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    plot.set_ylim(0,500)
    plt.show()
    #print web_direct.loc['2017-10-16'].head(5)
    #print web_data['date'].head(5)
    #print web_direct.head(5)
    #plt.savefig('.png')
    

if __name__ == '__main__':
    main()
