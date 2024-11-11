from flask import Flask, render_template, request, jsonify
import geopandas as gpd
import pandas as pd
import folium
import os
import json
import kaart_vlaanderen
import risicos_berekenen
import shutil
# HANDIGE SITES
    # voor folium: https://python-visualization.github.io/folium/latest/index.html


# om Flask webapplicatie te initaliseren: moet hier ALTIJD staan    
app = Flask(__name__)

# Bestanden pad initialiseren
vlaanderen_arrondisementen_path = r"C:\Users\annab\Documents\P&O 3\vlaanderen_arrondisement\Refarr25G10.shp"
vlaanderen_gemeenten_path = r"C:\Users\annab\Documents\P&O 3\vlaanderen_gemeentes\Refgem25G100.shp"
gemeenten_riscios_path = r"C:\Users\annab\Documents\P&O 3\gemeenten_risicos.csv"
arrondisement_risicos_path = r"C:\Users\annab\Documents\P&O 3\arrondisement_risicos_test2.csv"
kaart_html_path = r'C:\Users\annab\Documents\P&O 3\website_flask\static/kaarten/kaart_vlaanderen.html'

 #_______________________________________________________________HOME__________________________________________________________________________________________________
@app.route('/', methods=['GET', 'POST'])
def home():
    action = 'default' # er zit ergens een fout dat die na herladen die vorige actie toch nog blijft uitvoeren: MOET NOG GEFIXT WORDEN 
    action = request.args.get('action', 'default') #luistert naar acties van website
    gekozen_gemeente = request.args.get('gemeente', None)
    print('actie is:',action)


###############################################GEGEVENS#################################################
    # Laad de shapefiles en CSV:
    #vlaanderen_arrondisementen = gpd.read_file(vlaanderen_arrondisementen_path)
    vlaanderen_gemeenten = gpd.read_file(vlaanderen_gemeenten_path)
    #arrondisement_risicos = pd.read_csv(arrondisement_risicos_path, sep=';')
    # Naar juist coordinaten-systeem zetten om te plotten: 
    if vlaanderen_gemeenten.crs != "EPSG:4326":
        vlaanderen_gemeenten= vlaanderen_gemeenten.to_crs(epsg=4326)

    # Bestanden klaarmaken om door te geven naar Home-pagina: 
    subset_vlaanderen_gemeenten = vlaanderen_gemeenten[['NAAM', 'geometry']]
    subset_vlaanderen_gemeenten.loc[:, 'geometry'] = subset_vlaanderen_gemeenten['geometry'].apply(lambda x: x.__geo_interface__)
                    # Maak een lijst van tuples met (NAAM, GEOMETRIE)
    gemeenten_lijst = [(row['NAAM'], row['geometry']) for _, row in subset_vlaanderen_gemeenten.iterrows()]
    gemeenten_lijst = sorted(gemeenten_lijst, key=lambda x: x[0])



##########################################KAART#############################################################

    # Maken Folium kaart aan en groepen
    m = kaart_vlaanderen.init_map(vlaanderen_gemeenten)
    regen_groep = folium.FeatureGroup(name="Dagelijkse neerslag", overlay=True, control=True, show=False)
    gemeenten_groep = folium.FeatureGroup(name="Gemeenten",overlay=True,control=True,show=False)


    if gekozen_gemeente:
        kaart_vlaanderen.highlight_selected_gemeente(m, vlaanderen_gemeenten, gekozen_gemeente)
    m.save(kaart_html_path)

    if request.method == 'POST':
        # Controleer of er bestanden zijn geüpload
        if 'rainfile' in request.files:
            files = request.files.getlist('rainfile')  # Haal alle bestanden op als lijst
            
            # Print de lengte van de bestandenlijst voor debugging
            print(f"Aantal geüploade bestanden: {len(files)}")

            upload_folder = r'C:\Users\annab\Documents\P&O 3\website_flask\upload_regen'
            if os.path.exists(upload_folder):
                shutil.rmtree(upload_folder)

            for file in files:
                if file:
                    filepath = os.path.join(upload_folder, file.filename)
        
                    # Zorg ervoor dat de map bestaat door de directory-structuur aan te maken
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    file.save(filepath)
                    print(f"Bestand opgeslagen: {filepath}")

            return "Bestanden succesvol geüpload en opgeslagen.", 200


    datums_neerslag = [r'C:\Users\annab\Documents\P&O 3\website_flask\HDF_DAGEN\hdf - 15jul',
                       r'C:\Users\annab\Documents\P&O 3\website_flask\HDF_DAGEN\hdf - 26aug',
                       r'C:\Users\annab\Documents\P&O 3\website_flask\HDF_DAGEN\hdf - 28aug'] #data en gegevens-paths voor de 3 neerslagen
    if action == 'rainfall1':
            gemeenten_risicos = risicos_berekenen.risico(vlaanderen_gemeenten,datums_neerslag[0])
            m = kaart_vlaanderen.init_map(vlaanderen_gemeenten)
            m = kaart_vlaanderen.add_rainfall_layer_h(m,datums_neerslag[0])  #KAN NIET IN EEN FEATURE GROEP WANT DAN WERKT HET NIET, naamgeving in de heatmap functie zelf (kaart_vlaanderen)
            gemeenten_groep2 = folium.FeatureGroup(name="Gemeenten", overlay=True, control=True, show=True)
            gemeenten_groep2 = kaart_vlaanderen.add_gemeenten_layer(gemeenten_groep2, vlaanderen_gemeenten,0.3, gemeenten_risicos) #vervaging nodig om wolkjes te zien
            gemeenten_groep2.add_to(m)
            regen_groep = kaart_vlaanderen.add_rainfall_layer_d(regen_groep, datums_neerslag[0]) #dagelijkse neerslag
            regen_groep.add_to(m)
        
            folium.LayerControl().add_to(m) #hiermee kan je verschillende lagen aan en uitzetten (show=F/T om ze op het begin uit of aan te zetten)
            m.save(kaart_html_path)
            iframe_html = f'<iframe src="/static/kaarten/kaart_vlaanderen.html" width="100%" height="100%"></iframe >'
            print('iframe gemaakt')
            return iframe_html  # Stuur de iframe HTML terug voor de kaart

    elif action == 'rainfall2':
            gemeenten_risicos = risicos_berekenen.risico(vlaanderen_gemeenten,datums_neerslag[1])
            m = kaart_vlaanderen.init_map(vlaanderen_gemeenten)
            m = kaart_vlaanderen.add_rainfall_layer_h(m, datums_neerslag[1])  # KAN NIET IN EEN FEATURE GROEP WANT DAN WERKT HET NIET
            gemeenten_groep2 = folium.FeatureGroup(name="Gemeenten", overlay=True, control=True, show=True)
            gemeenten_groep2 = kaart_vlaanderen.add_gemeenten_layer(gemeenten_groep2, vlaanderen_gemeenten,0.3, gemeenten_risicos)  # vervaging nodig om wolkjes te zien
            regen_groep = kaart_vlaanderen.add_rainfall_layer_d(regen_groep,datums_neerslag[1])
            regen_groep.add_to(m)
            gemeenten_groep2.add_to(m)
            #gemeenten_groep = folium.FeatureGroup(name="Gemeenten",overlay=True,control=True,show=False)
            #gemeenten_groep = kaart_vlaanderen.add_gemeenten_layer(gemeenten_groep, vlaanderen_gemeenten)
            #gemeenten_groep.add_to(m)
            folium.LayerControl().add_to(m)
            m.save(kaart_html_path)
            iframe_html = f'<iframe src="/static/kaarten/kaart_vlaanderen.html" width="100%" height="100%"></iframe >'
            print('inframe gemaakt')
            return iframe_html  # Stuur de iframe HTML terug voor de kaart
    elif action == 'rainfall3':
            gemeenten_risicos = risicos_berekenen.risico(vlaanderen_gemeenten,datums_neerslag[2])
            m = kaart_vlaanderen.init_map(vlaanderen_gemeenten)
            m = kaart_vlaanderen.add_rainfall_layer_h(m, datums_neerslag[2])  # KAN NIET IN EEN FEATURE GROEP WANT DAN WERKT HET NIET
            gemeenten_groep2 = folium.FeatureGroup(name="Gemeenten", overlay=True, control=True, show=True)
            gemeenten_groep2 = kaart_vlaanderen.add_gemeenten_layer(gemeenten_groep2, vlaanderen_gemeenten,0.3, gemeenten_risicos)  # vervaging nodig om wolkjes te zien
            regen_groep = kaart_vlaanderen.add_rainfall_layer_d(regen_groep, datums_neerslag[2])
            regen_groep.add_to(m)
            gemeenten_groep2.add_to(m)
            folium.LayerControl().add_to(m)
            m.save(kaart_html_path)
            iframe_html = f'<iframe src="/static/kaarten/kaart_vlaanderen.html" width="100%" height="100%"></iframe >'
            print('inframe gemaakt')
            return iframe_html  # Stuur de iframe HTML terug voor de kaart

    elif action == 'select_gemeente':
            gekozen_gemeente = request.args.get('gemeente')
            print(f'Gekozen gemeente: {gekozen_gemeente}')
            iframe_html = f'<iframe src="/gemeente/{gekozen_gemeente}" width="90%" height="200px"></iframe>'
            return jsonify({
                'kaart_vlaanderen_html': f'<iframe src="/static/kaarten/kaart_vlaanderen.html" width="100%" height="100%"></iframe >' ,
                'gemeente_html': iframe_html,
            })

    m.save(kaart_html_path)
    return render_template('home.html', title='Home', vlaanderen_gemeenten=gemeenten_lijst)


#_____________________________________________________________________________GEMEENTE_________________________________________________________________________________________
@app.route('/gemeente/<string:gemeente_naam>')
def gemeente(gemeente_naam):
    # Laad de shapefile voor gemeenten
    vlaanderen_gemeenten = gpd.read_file(vlaanderen_gemeenten_path)

    if vlaanderen_gemeenten.crs != "EPSG:4326":
        vlaanderen_gemeenten= vlaanderen_gemeenten.to_crs(epsg=4326)

    # Filter de geselecteerde gemeente
    geselecteerde_gemeente = vlaanderen_gemeenten[vlaanderen_gemeenten['NAAM'] == gemeente_naam]

    # Controleer of de gemeente bestaat
    if not geselecteerde_gemeente.empty:
        # Haal de geometrie en coördinaten van de geselecteerde gemeente op
        gemeente_geo = geselecteerde_gemeente.geometry.values[0]
        gemeente_centroid = gemeente_geo.centroid
        gemeente_lat = gemeente_centroid.y
        gemeente_lon = gemeente_centroid.x


                # Maak een Folium-kaart voor de geselecteerde gemeente
        m_gemeente = folium.Map(location=[gemeente_lat, gemeente_lon], tiles='OpenStreetMap')
        #folium.GeoJson(gemeente_geo).__geo_interface__.add_to(m_gemeente)
        folium.GeoJson(
            gemeente_geo,  # De geometrie van de gemeente
            style_function=lambda feature: {
                'color': 'black',  # Kleur van de omtrek
                'weight': 2,      # Dikte van de omtrek
                'fillColor': 'none',
            }
        ).add_to(m_gemeente)

        # Pad naar het GML-bestand
        gml_path = r"C:\Users\annab\Documents\P&O 3\website_flask\static\data\overstroombaar_gebied_FLU_hCC.gml"

        # Laad het GML-bestand
        overstromingsdata = gpd.read_file(gml_path)

        if overstromingsdata.crs != "EPSG:4326":
            overstromingsdata = overstromingsdata.to_crs(epsg=4326)

        folium.GeoJson(overstromingsdata).add_to(m_gemeente)

        folium.LayerControl().add_to(m_gemeente)

        # Sla de gemeente kaart op
        gemeente_html_path = os.path.join('website_flask','static','kaarten', f'kaart_{gemeente_naam}.html')
        os.makedirs(os.path.dirname(gemeente_html_path), exist_ok=True)

        print(f'Saving gemeente map to {gemeente_html_path}')
        gemeente_html_path_doorsturen = os.path.join('static','kaarten', f'kaart_{gemeente_naam}.html')
        m_gemeente.save(gemeente_html_path)

        return render_template('gemeente.html', gemeente=gemeente_naam, kaart_path=gemeente_html_path_doorsturen)
    else:
        print(f'Gemeente {gemeente_naam} niet gevonden.')
        return "Gemeente niet gevonden.", 404
 

 #_____________________________________________________________________________________ABOUT_____________________________________________________________________________________
@app.route('/about')  # Route voor de About Us-pagina
def about():
    return render_template('about.html', title='About Us')

#______________________________________________________________________________________MAATREGELINGEN________________________________________________________________________________
@app.route('/maatregelingen')  # Route voor de About Us-pagina
def maatregelingen():
    return render_template('maatregelingen.html', title='Maatregelingen')

if __name__ == '__main__':
    app.run(debug=True)
# dit zorgt dat bestand runt 
# debug=True: activeert de debug-modus, wat betekent dat de server automatisch opnieuw opstart als je wijzigingen aanbrengt in de code. 



