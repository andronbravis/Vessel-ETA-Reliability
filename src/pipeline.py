import pandas as pd

from cleaning import clean_ais
from eta_validation import filter_eta_outliers
from mapping import map_ais
from loading import load_ais

def main():
    cols = ['MMSI', 'Latitude', 'Longitude', 'SOG', 'Ship type', 'Destination',
         'ETA', '# Timestamp', 'Type of mobile', 'Navigational status', 'Name']

    df_ais = pd.read_csv('data/raw/aisdk-2024-08-07.csv', usecols=cols)

    part1 = pd.read_csv('data/reference/UNLOCODE CodeListPart1.csv', header=None)
    part2 = pd.read_csv('data/reference/UNLOCODE CodeListPart2.csv', header=None)
    part3 = pd.read_csv('data/reference/UNLOCODE CodeListPart3.csv', header=None)

    wpi = pd.read_csv('data/reference/world_port_index.csv')

    manual_coords = pd.read_csv('data/mapping/manual_port_coordinates.csv')
    destination_aliases = pd.read_csv('data/mapping/destination_aliases.csv')
    eta_outliers = pd.read_csv('data/mapping/eta_outliers.csv')

    eta_outliers['MMSI'] = eta_outliers['MMSI'].astype(str)
    eta_outliers['ETA'] = pd.to_datetime(eta_outliers['ETA'])
    eta_outliers['# Timestamp'] = pd.to_datetime(eta_outliers['# Timestamp'])

    df_ais = clean_ais(df_ais)
    df_ais = filter_eta_outliers(df_ais, eta_outliers)
    df_ais = map_ais(part1, part2, part3, df_ais, wpi, manual_coords, destination_aliases)
    load_ais(df_ais)


if __name__ == "__main__":
    main()
