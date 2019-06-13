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
    web_df = pd.read_csv(path_web_data)
    spot_df = pd.read_csv(path_spot_data)
    # convert time columns of both DFs to pandas datetime variable
    web_df['datetime'] = pd.to_datetime(web_df['time'], utc=True)
    spot_df['datetime'] = pd.to_datetime(spot_df['time'], utc=True)
    web_df['date'] = web_df['datetime'].dt.date
    spot_df['date'] = spot_df['datetime'].dt.date
    web_df.drop('time', axis=1)
    spot_df.drop('time',axis=1)
    # create new dataframe with only direct traffic
    web_direct_df = web_df[web_df.traffic_source == 'direct'][['datetime','value']]
    return web_df, spot_df, web_direct_df


def spotsInInterval(datetime_start, datetime_end, spot_df):
    ''' takes start time, end time (as strings) and spot data DF; returns DF & list of tuples like (datetime, creative_id) aired during that interval '''
    spots_datetimes_df = spot_df[(spot_df.datetime >= pd.Timestamp(datetime_start)) & (spot_df.datetime <= pd.Timestamp(datetime_end))][['datetime', 'creative_id']]
    spots_datetimes_list = []
    for index, rows in spots_datetimes_df.iterrows():
        spots_datetimes_list.append((rows.datetime,rows.creative_id))
    if spots_datetimes_df.empty:
        return None
    else:
        return spots_datetimes_df, spots_datetimes_list


def generateVisitsPlot(datetime_start, datetime_end, web_direct_df, spot_df, fig_name):
    ''' takes a datetime start & end (strings), a web DF, a spot DF, and figure name and returns plot of website visits in that interval called fig_name '''
    sns.set(rc={'figure.figsize':(11, 4)})
    plot = web_direct_df.plot(x='datetime',y='value')
    plot.set_xlim(pd.Timestamp(datetime_start), pd.Timestamp(datetime_end))
    # include date in x-axis labels if the time interval spans multiple days
    if (pd.Timestamp(datetime_end) - pd.Timestamp(datetime_start)).days == 0:
        plot.set_xlabel('Datetime [hour]:[minute]')
        plot.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    else:
        plot.set_xlabel('Datetime [date]:[hour]:[minute]')
        plot.xaxis.set_major_formatter(mdates.DateFormatter('%D:%H:%M'))
    plot.set_ylabel('Number of Visits')
    plot.set_title('Website Visits (Traffic Source = Direct) From {} UTC'.format(datetime_start + ' to ' + datetime_end))
    # scale y axis according to the peak value 
    max_y = web_direct_df[(web_direct_df.datetime >= pd.Timestamp(datetime_start)) & (web_direct_df.datetime <= pd.Timestamp(datetime_end))]['value'].max()
    plot.set_ylim(0,(max_y + 0.2*max_y))
    # add vertical line markers representing spots
    # first need to find all spots airing during the interval
    spots_datetimes_df, spots_datetimes_list = spotsInInterval(datetime_start, datetime_end, spot_df) 
    for spot in spots_datetimes_list:
        plot.vlines(str(spot[0]), 0, max_y, color='r', label='Creative '+ str(spot[1]) +' at time '+ str(spot[0]))
    plt.legend()
    plt.savefig(('{}.png').format(fig_name))
    return plot


def calcBaselineLift(web_direct_df, spot_df, datetime, creative_id):
    ''' takes web and spot DFs, datetime of specific spot and its creative_id; returns baseline # visits '''
    baseline_window_end = pd.to_datetime(datetime).floor('min')
    baseline_window_start = baseline_window_end - pd.Timedelta(minutes=5)
    # check if there is an ad between when baseline calc should start and end
    # if there is, choose the closest consecutive 5-minute interval that doesn't conflict with any ad
    #print spotsInInterval(baseline_window_start, baseline_window_end, spot_df)
    #import pdb;pdb.set_trace()
    while spotsInInterval(baseline_window_start, baseline_window_end, spot_df) != None:
        baseline_window_end -= pd.Timedelta(minutes=1)
        baseline_window_start-= pd.Timedelta(minutes=1)
    # create dataframe for baseline within this interval that now is conflict-free
    baseline_df = web_direct_df[(web_direct_df.datetime >= pd.Timestamp(baseline_window_start)) & (web_direct_df.datetime <= pd.Timestamp(baseline_window_end))]
    baseline = baseline_df['value'].mean()
    # do the same for lift
    lift_window_start = pd.to_datetime(datetime) + pd.Timedelta(minutes=1)
    lift_window_end = lift_window_start + pd.Timedelta(minutes=5)
    #while spotsInInterval(lift_window_start, lift_window_end, spot_df) != None:
    #    lift_window_end += pd.Timedelta(minutes=1)
    #    lift_window_start += pd.Timedelta(minutes=1)
    print lift_window_start, lift_window_end
    print spotsInInterval(lift_window_start, lift_window_end, spot_df)
    lift_df = web_direct_df[(web_direct_df.datetime >= pd.Timestamp(lift_window_start)) & (web_direct_df.datetime <= pd.Timestamp(lift_window_end))]
    # lift = all visits in lift window - baseline
    lift = lift_df['value'].sum() - baseline
    return [baseline, lift]


def main():
    # retrieve clean dataframes
    web_df, spot_df, web_direct_df = cleanDataFrames(path_spot_data,path_web_data)
    # create & populate dictionary {creative_id: spend}
    spend_per_creative = (spot_df.groupby('creative_id')['spend'].agg('sum')).to_dict()
    for key in spend_per_creative:
        spend_per_creative[key] = round(spend_per_creative[key],2)
    # create & populate dictionary {(datetime, creative_id): [baseline, lift]}
    baseline_lift_per_spot = {}
    print calcBaselineLift(web_direct_df, spot_df, '2017-11-13 02:12:11+00', '6e69270e444e10a1ec9a2bdfbb739c05')
    spots_datetimes_df, spots_datetimes_list = spotsInInterval('2017-10-16 00:00:00+00','2017-11-14 00:00:00+00', spot_df)
    #for spot in spots_datetimes_list:
        #baseline_lift_per_spot[spot] =  
        

if __name__ == '__main__':
    main()
