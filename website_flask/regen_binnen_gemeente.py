import os
import pysteps
import numpy as np
from zipfile import ZipFile
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point

#Locatie van mapje
data_path = r'C:\Users\annab\Documents\P&O 3\website_flask\HDF_DAGEN\hdf - 26aug'


hdf_filepath = data_path
hdf_files = os.listdir(hdf_filepath)
agg_type = "ACRR"


# Create empty arrays for precipitation and timestamps
precipitation = []
timestamps = []

# Read hdf file with pysteps for all files in path
agg_type = "ACRR"  # Or 'RATE', 'DBZH' depending on your data type
"""
"ACRR" voor geaccumuleerde neerslag --> deze voor gegevens van KMI
"RATE" voor regenvalintensiteit
"DBZH" voor radarreflectiviteit
"""
for hdf_file in hdf_files:
    hdf_datetime = hdf_file.split('.')[0]
    hdf_timestamp = datetime.strptime(hdf_datetime, '%Y%m%d%H%M%S')
    [hdf_precipitation, _, metadata
        ] = pysteps.io.importers.import_odim_hdf5(f'{hdf_filepath}/{hdf_file}',qty=agg_type.upper())
    precipitation = np.append(precipitation, hdf_precipitation)
    timestamps = np.append(timestamps, hdf_timestamp)

# Reshape qpe array
n_timesteps = len(hdf_files)
gridsize = 700
precipitation = precipitation.reshape((n_timesteps, gridsize,gridsize))
precipitation = np.nan_to_num(precipitation,nan=0.0)

#######################hier berekeningen############################
vlaanderen_gemeenten_path = r"C:\Users\annab\Documents\P&O 3\vlaanderen_gemeentes\Refgem25G100.shp"
vlaanderen_gemeenten = gpd.read_file(vlaanderen_gemeenten_path)
if vlaanderen_gemeenten.crs != "EPSG:4326":
        vlaanderen_gemeenten= vlaanderen_gemeenten.to_crs(epsg=4326)

for _, row in vlaanderen_gemeenten.iterrows():
    print('START')
    gemeente_naam = row['NAAM']
    print(gemeente_naam)
    gemeente_gdf = vlaanderen_gemeenten[vlaanderen_gemeenten['NAAM'] == gemeente_naam]
    gemeente_geom = gemeente_gdf.geometry.iloc[0]

    gemeente_oppervlakte = gemeente_geom.area 
    # Coördinaten van het gebied waarvoor we de neerslag willen berekenen
    # !!!!!Zorg ervoor dat de coördinaten en het grid van je neerslagdata overeenkomen!!!!

    min_lon, min_lat, max_lon, max_lat = gemeente_geom.bounds
    
    # Pas de gridgrenzen aan op basis van de bounding box
    latitudes = np.linspace(min_lat, max_lat, gridsize)
    longitudes = np.linspace(min_lon, max_lon, gridsize)
    print('begin mask')
    # Maak een masker voor het gebied Leuven
    mask = np.zeros((gridsize, gridsize), dtype=bool)
    print('begin for lus')
    # Loop door het grid en zet `True` voor cellen binnen het Leuven polygon
    for i, lat in enumerate(latitudes):
        for j, lon in enumerate(longitudes):
            point = Point(lon, lat)  # Maak een Point object
            if gemeente_geom.contains(point):  # Controleer of het punt binnen de geometrie van Leuven ligt
                mask[i, j] = True
    print('end for lus')

    # Maskeren van de neerslagdata voor Leuven
    masked_precipitation = precipitation[:, mask]
    print('end masked_precipitation')
    # Som van de neerslag binnen Leuven per tijdstap
    total_precipitation_per_timestep = np.sum(masked_precipitation, axis=1)

    # Som van neerslag over alle tijdstappen
    total_precipitation_leuven_all_time = np.sum(total_precipitation_per_timestep)/gemeente_oppervlakte
    print(f"Totale neerslag voor alle tijdstappen binnen {gemeente_naam}: {total_precipitation_leuven_all_time}")
