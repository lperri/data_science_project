import pandas as pd
import argparse

# obtain paths to CSVs
parser = argparse.ArgumentParser(description='Get path to web traffic CSV and spot data CSV')
parser.add_argument('path_web_data',type=str, help='path to web traffic CSV file')
parser.add_argument('path_spot_data',type=str, help='path to spot data CSV file')
args = parser.parse_args()
path_web_data = args.path_web_data
path_spot_data = args.path_spot_data


def cleanData(path_web_data, path_spot_data):
    ''' takes in paths to CSVs and will return Pandas DFs ready for use '''
    # read CSVs into pandas
    web_data = pd.read_csv(path_web_data)
    spot_data = pd.read_csv(path_spot_data)
    # convert time columns of both DFs to pandas datetime variable
    web_data['datetime'] = pd.to_datetime(web_data['time'])
    spot_data['datetime'] = pd.to_datetime(spot_data['time'])
    web_data.drop('time', axis=1)
    # create new dataframe with only direct traffic
    web_direct = web_data[web_data.traffic_source == 'direct'][['time','value']]


def main():


if __name__ == '__main__':
    main()
