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


def calcBaseline(web_direct_df, spot_df, datetime, creative_id):
    ''' takes web and spot DFs, datetime of specific spot and its creative_id; returns baseline # visits '''
    baseline_window_end = pd.to_datetime(datetime).floor('min')
    baseline_window_start = baseline_window_end - pd.Timedelta(minutes=5)
    # check if there is an ad between when baseline calc should start and end
    # if there is, choose the closest consecutive 5-minute interval that doesn't conflict with any ad
    while spotsInInterval(baseline_window_start, baseline_window_end, spot_df) != None:
        baseline_window_end -= pd.Timedelta(minutes=1)
        baseline_window_start-= pd.Timedelta(minutes=1)
    # create dataframe for baseline within this interval that now is conflict-free
    baseline_df = web_direct_df[(web_direct_df.datetime >= pd.Timestamp(baseline_window_start)) & (web_direct_df.datetime <= pd.Timestamp(baseline_window_end))]
    baseline = baseline_df['value'].mean()
    return baseline


def calcLift(web_direct_df, spot_df, datetime, creative_id, baseline):    
    ''' takes web and spot DFs, datetime of specific spot and its creative_id; returns lift as measured from baseline '''
    lift_window_start = pd.Timestamp(datetime)
    lift_window_end = lift_window_start + pd.Timedelta(minutes=5)
    # check if there are more than 1 spot airing in the lift window
    lift_df = web_direct_df[(web_direct_df.datetime >= pd.Timestamp(lift_window_start)) & (web_direct_df.datetime <= pd.Timestamp(lift_window_end))]
    # find overlaps by calling spotsInInterval (the time delta of 1 second is to ensure that the spot of interest won't count as overlapping itself
    overlaps = spotsInInterval(lift_window_start + pd.Timedelta(seconds=1), lift_window_end, spot_df)[1]
    # subtract_overlap will keep track of how much traffic we need to subtract from lift (that we are attributing to this particular ad)
    subtract_overlap = 0
    # len > 0, there is more than just the ad of interest in this window
    if len(overlaps) > 0:
        index = range(len(overlaps))
        overlaps_df = pd.DataFrame(overlaps, columns=['datetime', 'creative_id'])
        overlaps_df = overlaps_df.sort_values(by='datetime',ascending=False)
        overlaps_df.reindex(index)
        # grab the latest spot (then the 2nd latest, etc...) that overlaps with spot of interest and find time they share
        i = 0
        # initialize overlap_end to be the end of the lift window; this will change throughout iterations
        overlap_end = lift_window_end
        while i < len(overlaps):
            # start at the LATEST starting ad that overlaps ad of interest
            overlap_start = overlaps_df.iloc[i][0]
            # check if any other overlapping spots also overlap in the same window
            other_overlaps = overlaps_df[(overlaps_df.datetime < overlap_start) & (overlaps_df.datetime + pd.Timedelta(minutes=5) > overlap_end)]
            if i == 0:
                len_other_overlaps = len(other_overlaps.index)
            overlap_traffic = web_direct_df[(web_direct_df.datetime >= overlap_start) & (web_direct_df.datetime < overlap_end)]
            # assume traffic can be divided evenly between ads that overlap
            subtract_overlap += (overlap_traffic['value'].sum())*len_other_overlaps/(1+len_other_overlaps)
            # set the overlap_end for the next iteration to be where we started last time
            overlap_end = overlap_start
            i += 1
    lift = lift_df['value'].sum() - subtract_overlap - baseline
    return lift


#def cpvGraph():
#    return graph

def main():
    # retrieve clean dataframes
    web_df, spot_df, web_direct_df = cleanDataFrames(path_spot_data,path_web_data)
    # create & populate dictionary {creative_id: spend}
    spend_per_creative = (spot_df.groupby('creative_id')['spend'].agg('sum')).to_dict()
    for key in spend_per_creative:
        spend_per_creative[key] = round(spend_per_creative[key],2)
    # create & populate dictionary {(datetime, creative_id): [baseline, lift]}
    baseline_lift_per_spot = {}
    #print spotsInInterval('2017-10-17 22:38:00+00', '2017-10-17 22:44:00+00', spot_df)
    baseline = calcBaseline(web_direct_df, spot_df, '2017-10-17 22:39:16+00','f3483f810d44cef79d90a66ab2da1bf0')
    lift = calcLift(web_direct_df, spot_df, '2017-10-17 22:39:16+00','f3483f810d44cef79d90a66ab2da1bf0',baseline)
    
    #print calcBaselineLift(web_direct_df, spot_df, '2017-11-13 02:12:11+00', '6e69270e444e10a1ec9a2bdfbb739c05')
    #spots_datetimes_df, spots_datetimes_list = spotsInInterval('2017-10-16 00:00:00+00','2017-11-14 00:00:00+00', spot_df)
        

if __name__ == '__main__':
    main()
