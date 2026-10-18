import pandas as pd

def filter_eta_outliers(df: pd.DataFrame, eta_outliers: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    eta_outliers = eta_outliers.copy()

    keys = ['MMSI', '# Timestamp', 'ETA', 'Destination']

    merged = df.merge(eta_outliers, on=keys, how='left', indicator=True, validate='m:1')
    merged = merged[merged['_merge'] == 'left_only']

    return merged.drop(columns=['_merge'])

