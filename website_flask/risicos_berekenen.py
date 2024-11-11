import geopandas as gpd
import pandas as pd
def risico(vlaanderen_gemeenten,neerslagdata):
    gemeenten_riscios_path = r"C:\Users\annab\Documents\P&O 3\gemeenten_risicos.csv"
    gemeenten_risicos = pd.read_csv(gemeenten_riscios_path, sep=';')

    return gemeenten_risicos