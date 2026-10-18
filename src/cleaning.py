import pandas as pd

def filter_vessel_types(df: pd.DataFrame) -> pd.DataFrame:
    target = ['Cargo', 'Tanker', 'Passenger']

    return df[df['Ship type'].isin(target)].copy()

def filter_sog(df: pd.DataFrame) -> pd.DataFrame:
    invalid_sog = ['229191000', '352179000', '230712000', '257182700']
    df = df.copy()
    df['MMSI'] = df['MMSI'].astype(str)
    df = df[df['SOG'].notnull()]

    return df[~df['MMSI'].isin(invalid_sog)]

def filter_nav_status(df: pd.DataFrame) -> pd.DataFrame:
    valid_nav = ['Under way using engine', 'Constrained by her draught', 'Under way sailing', 'Restricted maneuverability']

    return df[df['Navigational status'].isin(valid_nav)].copy()

def filter_valid_dest(df: pd.DataFrame) -> pd.DataFrame:
    invalid_dest = ['Unknown', 'FOR ORDERS', 'FOR ORDER']

    return df[~df['Destination'].isin(invalid_dest)].copy()

def normalize_destination(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['Destination'] = df['Destination'].str.upper().str.strip().str.replace(' ', '')

    return df

def eta_validation(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['# Timestamp'] = pd.to_datetime(df['# Timestamp'], dayfirst=True, errors='coerce')
    df['ETA'] = pd.to_datetime(df['ETA'], dayfirst=True, errors='coerce')

    return df[(df['ETA'].notnull()) & (df['ETA'] > df['# Timestamp'])]

def clean_ais(df: pd.DataFrame) -> pd.DataFrame:
    df = filter_vessel_types(df)
    df = filter_sog(df)
    df = filter_nav_status(df)
    df = filter_valid_dest(df)
    df = normalize_destination(df)
    df = eta_validation(df)

    return df
