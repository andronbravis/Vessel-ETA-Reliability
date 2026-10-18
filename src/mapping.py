import pandas as pd
import numpy as np

def create_port_reference(pt1: pd.DataFrame, pt2: pd.DataFrame, pt3: pd.DataFrame) -> pd.DataFrame:
    columns = ['Change',
      'Country',
      'Location',
      'Name',
      'NameWoDiacritics',
      'SubDiv',
      'Function',
      'Status',
      'Date',
      'IATA',
      'Coordinates',
      'Remarks'
    ]

    port_codes = pd.concat([pt1, pt2, pt3], ignore_index=True)
    port_codes.columns = columns
    port_codes['LOCODE'] = (port_codes['Country'].str.strip()) + (port_codes['Location'].str.strip())

    return port_codes[['Country', 'Location', 'LOCODE', 'Name', 'Function', 'Coordinates']].copy()

def create_unique_dest(df_ais: pd.DataFrame) -> pd.Series:
    return df_ais['Destination'].drop_duplicates().copy()

def filter_port_reference(port_reference: pd.DataFrame) -> pd.DataFrame:
    port_reference = port_reference.sort_values('Coordinates', na_position='last')
    port_reference = port_reference.drop_duplicates(subset='LOCODE', keep='first')

    return port_reference.copy()

def create_unavailable(port_reference: pd.DataFrame, unique_dest: pd.Series) -> pd.DataFrame:
    return port_reference[(port_reference['LOCODE'].isin(unique_dest)) & (port_reference['Coordinates'].isnull())].copy()

def create_wpi_matches(wpi: pd.DataFrame, unavailable: pd.DataFrame) -> pd.DataFrame:
    columns = ['UN/LOCODE', 'Main Port Name', 'Latitude', 'Longitude']
    wpi = wpi[columns].copy()
    wpi['UN/LOCODE'] = wpi['UN/LOCODE'].str.replace(' ', '')

    wpi_matches = wpi[wpi['UN/LOCODE'].isin(unavailable['LOCODE'])]

    return wpi_matches[(wpi_matches['Main Port Name'] != 'Brunsbuttel Canal Terminals') & (wpi_matches['Main Port Name'] != 'Point Lisas Port')].copy()

def create_wpi_coverage(unavailable: pd.DataFrame, wpi_matches: pd.DataFrame) -> pd.DataFrame:
    wpi_coverage = pd.merge(unavailable, wpi_matches, how='left', left_on='LOCODE', right_on='UN/LOCODE')

    return wpi_coverage

def to_decimal(coordinate: str) -> float:
    raw = coordinate
    if pd.isnull(raw) :
        return np.nan
    elif len(raw) == 5:
        lat_deg = float(raw[:2])
        lat_min = int(raw[2:4])
        lat_dir = raw[4:5]
        return (-(lat_deg + (lat_min/60)) if lat_dir == 'S' else lat_deg + (lat_min/60))
    elif len(raw) == 6:
        lon_deg = float(raw[:3])
        lon_min = int(raw[3:5])
        lon_dir = raw[5:6]
        return (-(lon_deg + (lon_min/60)) if lon_dir == 'W' else lon_deg + (lon_min/60))
    else:
        return np.nan

def apply_to_decimal(port_reference: pd.DataFrame) -> pd.DataFrame:
    port_reference = port_reference.copy()
    port_lat = (port_reference['Coordinates'].str.split()).str[0].copy()
    port_lon = (port_reference['Coordinates'].str.split()).str[1].copy()

    port_reference['Latitude'] = port_lat.apply(to_decimal)
    port_reference['Longitude'] = port_lon.apply(to_decimal)

    return port_reference

def create_wpi_reference(wpi_coverage: pd.DataFrame) -> pd.DataFrame:
    wpi_reference = wpi_coverage[['LOCODE', 'Latitude', 'Longitude']][(wpi_coverage['Latitude'].notnull()) & (wpi_coverage['Longitude'].notnull())].copy()

    return wpi_reference

def create_enriched_reference(port_reference: pd.DataFrame, wpi_reference: pd.DataFrame) -> pd.DataFrame:
    enriched_reference = pd.merge(port_reference, wpi_reference, how='left', on='LOCODE')

    return enriched_reference

def format_enriched_reference(enriched_reference: pd.DataFrame) -> pd.DataFrame:
    enriched_reference = enriched_reference.copy()

    enriched_reference['Latitude'] = enriched_reference['Latitude_x'].fillna(enriched_reference['Latitude_y'])
    enriched_reference['Longitude'] = enriched_reference['Longitude_x'].fillna(enriched_reference['Longitude_y'])

    enriched_reference['Source'] = 'Unresolved'
    enriched_reference.loc[(enriched_reference['Latitude_x'].notnull()) & (enriched_reference['Longitude_x'].notnull()), 'Source'] = 'UNECE'
    enriched_reference.loc[(enriched_reference['Latitude_y'].notnull()) & (enriched_reference['Longitude_y'].notnull()) & (enriched_reference['Source'] != 'UNECE'), 'Source'] = 'WPI'

    dropped = ['Latitude_x', 'Latitude_y', 'Longitude_x', 'Longitude_y']
    enriched_reference = enriched_reference.drop(columns=dropped)

    return enriched_reference

def manual_enriched_reference(enriched_reference: pd.DataFrame, manual_coords: pd.DataFrame) -> pd.DataFrame:
    enriched_reference = enriched_reference.copy()

    lat_index = manual_coords.set_index('LOCODE')['Latitude']
    lon_index = manual_coords.set_index('LOCODE')['Longitude']
    source_index = manual_coords.set_index('LOCODE')['Source']

    manual_lat = enriched_reference['LOCODE'].map(lat_index)
    manual_lon = enriched_reference['LOCODE'].map(lon_index)
    manual_source = enriched_reference['LOCODE'].map(source_index)

    lat_lookup = manual_lat.notnull()
    lon_lookup = manual_lon.notnull()
    source_lookup = manual_source.notnull()

    enriched_reference.loc[lat_lookup, 'Latitude'] = manual_lat[lat_lookup]
    enriched_reference.loc[lon_lookup, 'Longitude'] = manual_lon[lon_lookup]
    enriched_reference.loc[source_lookup, 'Source'] = manual_source[source_lookup]

    return enriched_reference

def create_dest_stats(df_ais: pd.DataFrame) -> pd.DataFrame:
    return df_ais.groupby('Destination').agg(observations=('MMSI', 'size'), unique_vessels=('MMSI', 'nunique')).copy()

def create_unmatched_dests(dest_stats: pd.DataFrame, enriched_reference: pd.DataFrame) -> pd.DataFrame:
    return dest_stats[~dest_stats.index.isin(enriched_reference['LOCODE'])].copy()

def create_layer_2(df_ais: pd.DataFrame, unmatched_dests: pd.DataFrame) -> pd.DataFrame:
    return df_ais[(df_ais['Destination'].isin(unmatched_dests.index)) & (~df_ais['Destination'].str.contains(r'[<>=/-]',na=False))].copy()

def create_layer_2_stats(layer_2: pd.DataFrame) -> pd.DataFrame:
    return layer_2.groupby('Destination').agg(observations=('MMSI', 'size'), unique_vessels=('MMSI', 'nunique')).copy()

def create_layer_2_mapping(layer_2_stats: pd.DataFrame) -> pd.DataFrame:
    layer_2_mapping = layer_2_stats.copy()

    layer_2_mapping['class'] = 'Unresolved'
    layer_2_mapping['mapped_LOCODE'] = 'Unresolved'

    return layer_2_mapping

def initiate_layer_2_mapping(layer_2_mapping: pd.DataFrame, destination_aliases: pd.DataFrame ) -> pd.DataFrame:
    layer_2_mapping = layer_2_mapping.copy()

    alias_index = destination_aliases.loc[destination_aliases['mapped_value'] != 'operational_text'].set_index('Destination')['mapped_value']
    operational_index = destination_aliases.loc[destination_aliases['mapped_value'] == 'operational_text'].set_index('Destination')['mapped_value']
    aliases = layer_2_mapping.index.map(alias_index)
    operational  = layer_2_mapping.index.map(operational_index)

    alias_lookup = aliases.notna()
    operational_lookup = operational.notna()

    layer_2_mapping.loc[alias_lookup, 'mapped_LOCODE'] = aliases[alias_lookup]
    layer_2_mapping.loc[alias_lookup, 'class'] = 'port_alias'
    layer_2_mapping.loc[operational_lookup, 'class'] = operational[operational_lookup]

    return layer_2_mapping

def create_layer_2_reference(layer_2_mapping: pd.DataFrame, enriched_reference: pd.DataFrame) -> pd.DataFrame:
    layer_2_reference = layer_2_mapping[(layer_2_mapping['mapped_LOCODE'] != 'Unresolved') & (layer_2_mapping['class'] == 'port_alias') & (layer_2_mapping['mapped_LOCODE'].isin(enriched_reference['LOCODE']))].copy()

    return layer_2_reference[['observations', 'unique_vessels', 'class', 'mapped_LOCODE']]

def create_layer_3(df_ais: pd.DataFrame, unmatched_dests: pd.DataFrame, layer_2_reference: pd.DataFrame) -> pd.DataFrame:
    return df_ais[(df_ais['Destination'].isin(unmatched_dests.index)) & (df_ais['Destination'].str.contains(r'[<>=/-]',na=False)) & (~df_ais['Destination'].isin(layer_2_reference.index))].copy()

def create_layer_3_stats(layer_3: pd.DataFrame) -> pd.DataFrame:
    return layer_3.groupby('Destination').agg(observations=('MMSI', 'size'), unique_vessels=('MMSI', 'nunique')).copy()

def create_directional(layer_3_stats: pd.DataFrame) -> pd.DataFrame:
    return layer_3_stats[(layer_3_stats.index.str.contains(r'[>]', na=False)) & (~layer_3_stats.index.str.contains(r'[<]', na=False))].copy()

def create_enriched_nnull(enriched_reference: pd.DataFrame) -> pd.DataFrame:
    return enriched_reference[enriched_reference['Latitude'].notnull() & enriched_reference['Longitude'].notnull() & enriched_reference['LOCODE'].notnull()].copy()

def update_directional(directional: pd.DataFrame, enriched_reference: pd.DataFrame, enriched_nnull: pd.DataFrame) -> pd.DataFrame:
    directional = directional.copy()

    directional['candidate_dest'] = directional.index.str.split('>').str[-1]

    directional = directional[directional['candidate_dest'].isin(enriched_reference['LOCODE']) & directional['candidate_dest'].isin(enriched_nnull['LOCODE'])].copy()
    directional['mapped_LOCODE'] = directional['candidate_dest']
    directional['class'] = 'directional_route'

    return directional

def create_layer_3_reference(directional: pd.DataFrame) -> pd.DataFrame:
    layer_3_reference = directional.copy()

    layer_3_reference = layer_3_reference[['observations', 'unique_vessels', 'class', 'mapped_LOCODE']]

    return layer_3_reference

def create_layer_1_reference(dest_stats: pd.DataFrame, enriched_nnull: pd.DataFrame) -> pd.DataFrame:
    layer_1_reference = dest_stats[dest_stats.index.isin(enriched_nnull['LOCODE'])].copy()

    layer_1_reference['class'] = 'exact_locode'
    layer_1_reference['mapped_LOCODE'] = layer_1_reference.index

    return layer_1_reference

def create_final_reference(layer_1_reference: pd.DataFrame, layer_2_reference: pd.DataFrame, layer_3_reference: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([layer_1_reference, layer_2_reference, layer_3_reference])

def apply_final_reference(df_ais: pd.DataFrame, final_reference: pd.DataFrame) -> pd.DataFrame:
    df_ais = df_ais.copy()

    df_ais.loc[df_ais['Destination'].isin(final_reference.index), 'mapped_LOCODE'] = df_ais['Destination'].map(final_reference['mapped_LOCODE'])
    df_ais.loc[df_ais['Destination'].isin(final_reference.index), 'class'] = df_ais['Destination'].map(final_reference['class'])

    return df_ais

def apply_coordinates(df_ais: pd.DataFrame, enriched_nnull: pd.DataFrame) -> pd.DataFrame:
    df_ais = df_ais.copy()

    lat_index = enriched_nnull.set_index('LOCODE')['Latitude']
    lon_index = enriched_nnull.set_index('LOCODE')['Longitude']

    df_ais['dest_lat'] = df_ais['mapped_LOCODE'].map(lat_index)
    df_ais['dest_lon'] = df_ais['mapped_LOCODE'].map(lon_index)

    return df_ais

def build_enriched_reference(pt1: pd.DataFrame, pt2: pd.DataFrame, pt3: pd.DataFrame,
    df_ais: pd.DataFrame, wpi: pd.DataFrame, manual_coords: pd.DataFrame) -> pd.DataFrame:
        port_reference = create_port_reference(pt1, pt2, pt3)
        unique_dest = create_unique_dest(df_ais)
        port_reference = filter_port_reference(port_reference)

        unavailable = create_unavailable(port_reference, unique_dest)
        wpi_matches = create_wpi_matches(wpi, unavailable)
        wpi_coverage = create_wpi_coverage(unavailable, wpi_matches)

        port_reference = apply_to_decimal(port_reference)
        wpi_reference = create_wpi_reference(wpi_coverage)

        enriched_reference = create_enriched_reference(port_reference, wpi_reference)
        enriched_reference = format_enriched_reference(enriched_reference)
        enriched_reference = manual_enriched_reference(enriched_reference, manual_coords)

        return enriched_reference

def build_layer_2_reference(df_ais: pd.DataFrame, destination_aliases: pd.DataFrame,
    enriched_reference: pd.DataFrame, unmatched_dests: pd.DataFrame) -> pd.DataFrame:
        layer_2 = create_layer_2(df_ais, unmatched_dests)
        layer_2_stats = create_layer_2_stats(layer_2)

        layer_2_mapping = create_layer_2_mapping(layer_2_stats)
        layer_2_mapping = initiate_layer_2_mapping(layer_2_mapping, destination_aliases)
        layer_2_reference = create_layer_2_reference(layer_2_mapping, enriched_reference)

        return layer_2_reference

def build_layer_3_reference(df_ais: pd.DataFrame, unmatched_dests: pd.DataFrame, 
    layer_2_reference: pd.DataFrame, enriched_reference: pd.DataFrame, enriched_nnull: pd.DataFrame) -> pd.DataFrame:
        layer_3 = create_layer_3(df_ais, unmatched_dests, layer_2_reference)
        layer_3_stats = create_layer_3_stats(layer_3)

        directional = create_directional(layer_3_stats)
        directional = update_directional(directional, enriched_reference, enriched_nnull)

        layer_3_reference = create_layer_3_reference(directional)

        return layer_3_reference


def map_ais(pt1: pd.DataFrame, pt2: pd.DataFrame, pt3: pd.DataFrame,
        df_ais: pd.DataFrame, wpi: pd.DataFrame, manual_coords: pd.DataFrame,
        destination_aliases: pd.DataFrame) -> pd.DataFrame:
    enriched_reference = build_enriched_reference(pt1, pt2, pt3, df_ais, wpi, manual_coords)
    dest_stats = create_dest_stats(df_ais)

    unmatched_dests = create_unmatched_dests(dest_stats, enriched_reference)
    enriched_nnull = create_enriched_nnull(enriched_reference)

    layer_2_reference = build_layer_2_reference(df_ais, destination_aliases, enriched_reference, unmatched_dests)
    layer_3_reference = build_layer_3_reference(df_ais, unmatched_dests, layer_2_reference, enriched_reference, enriched_nnull)
    layer_1_reference = create_layer_1_reference(dest_stats, enriched_nnull)
    final_reference = create_final_reference(layer_1_reference, layer_2_reference, layer_3_reference)

    df_ais = apply_final_reference(df_ais, final_reference)
    df_ais = apply_coordinates(df_ais, enriched_nnull)

    return df_ais

