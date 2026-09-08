from extract.extract_fires import load_fire_poligons, load_fire_poligons_in_interval

poligon_path = "data/raw/poligon_shapes/"
year = "2014_2015"
poligono = load_fire_poligons(f"{poligon_path}{year}/if_magnitud_{year}.shp")

datos = load_fire_poligons_in_interval(
    2020,
    2024,
    "data/raw/poligon_shapes/",
    region="Biobío",
)

for year, gdf in datos.items():
    print(f"Year: {year}, Number of fires: {len(gdf)}")
    for idx, row in gdf.iterrows():
        print(f"{row['CODCOM']}:{row['FECHA_INI']}:{row['FECHA_TER']}")
