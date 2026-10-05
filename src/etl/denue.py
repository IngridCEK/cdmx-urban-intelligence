"""ETL del DENUE 05_2026 (INEGI) por AGEB urbana.

Conserva los 462,732 establecimientos y asigna un estatus:
    asignado, dentro_cdmx_sin_ageb, fuera_cdmx, sin_coordenadas_validas.
"""
import argparse
import json
import geopandas as gpd
import pandas as pd
from src.config import PROCESSED_DIR, RAW_DIR
from src.geo.polygons import load_agebs, load_municipios

DEFAULT_CSV = "denue_09_csv/conjunto_de_datos/denue_inegi_09_.csv"
STATUS_ORDER = ["asignado", "dentro_cdmx_sin_ageb", "fuera_cdmx", "sin_coordenadas_validas"]
REQUIRED_COLUMNS = ["id","codigo_act","nombre_act","per_ocu","tipoUniEco","cve_ent","cve_mun","cve_loc","ageb","manzana","latitud","longitud"]

def extract(csv_name=DEFAULT_CSV):
    path=RAW_DIR/csv_name
    if not path.exists(): raise FileNotFoundError(f"No existe {path}")
    df=pd.read_csv(path,encoding="latin-1",dtype=str,low_memory=False)
    missing=[c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing: raise ValueError(f"Faltan columnas en el CSV: {missing}")
    return df

def clean(df):
    report={"registros_crudos":len(df)}; out=df.copy()
    dup=int(out["id"].duplicated().sum())
    if dup: raise ValueError(f"DENUE contiene {dup} IDs duplicados; no se eliminan registros")
    for c in ["latitud","longitud"]: out[c]=pd.to_numeric(out[c],errors="coerce")
    for c in ["cve_ent","cve_mun","cve_loc","ageb"]: out[c]=out[c].fillna("").astype(str).str.strip()
    out["CVEGEO_DENUE"]=(out["cve_ent"].str.zfill(2)+out["cve_mun"].str.zfill(3)+out["cve_loc"].str.zfill(4)+out["ageb"].str.zfill(4))
    bad=out[["cve_ent","cve_mun","cve_loc","ageb"]].eq("").any(axis=1)|(out["CVEGEO_DENUE"].str.len()!=13)
    out.loc[bad,"CVEGEO_DENUE"]=pd.NA
    return out,report

def split_by_coordinates(df,target_crs):
    missing=df.latitud.isna()|df.longitud.isna(); zero=(df.latitud==0)|(df.longitud==0)
    out_of_range=~df.latitud.between(-90,90)|~df.longitud.between(-180,180); valid=~(missing|zero|out_of_range)
    report={"sin_coordenadas":int(missing.sum()),"coordenadas_en_cero":int((zero&~missing).sum()),"coordenadas_fuera_de_rango":int((out_of_range&~missing&~zero).sum()),"con_coordenadas_utiles":int(valid.sum())}
    pts=gpd.GeoDataFrame(df.loc[valid].copy(),geometry=gpd.points_from_xy(df.loc[valid,"longitud"],df.loc[valid,"latitud"]),crs="EPSG:4326").to_crs(target_crs)
    return pts,df.loc[~valid].copy(),report

def _first_match(left,right,cols):
    j=gpd.sjoin(left[["geometry"]],right[cols+["geometry"]],how="left",predicate="within")
    return j[~j.index.duplicated(keep="first")]

def assign_polygons(points,agebs,municipalities):
    jm=_first_match(points,municipalities,["NOMGEO"]); ja=_first_match(points,agebs,["CVEGEO"])
    points["alcaldia_geo"]=jm["NOMGEO"]; points["CVEGEO"]=ja["CVEGEO"]
    # 09 is the study entity. The 3 true outliers are hundreds/thousands of km away;
    # a 100-km plausibility threshold avoids classifying tiny border geocoding errors as outside CDMX.
    distance_m=points.to_crs(municipalities.crs).geometry.distance(municipalities.geometry.union_all())
    inside=points["alcaldia_geo"].notna() | (points["cve_ent"].eq("09") & distance_m.le(100_000))
    points["estatus_asignacion"]="fuera_cdmx"; points.loc[inside,"estatus_asignacion"]="dentro_cdmx_sin_ageb"; points.loc[points.CVEGEO.notna(),"estatus_asignacion"]="asignado"
    return points

def build_final(points,invalid,crs):
    invalid=invalid.copy(); invalid["alcaldia_geo"]=pd.NA; invalid["CVEGEO"]=pd.NA; invalid["estatus_asignacion"]="sin_coordenadas_validas"
    invalid=gpd.GeoDataFrame(invalid,geometry=gpd.GeoSeries([None]*len(invalid),index=invalid.index,crs=crs),crs=crs)
    final=pd.concat([points,invalid]).sort_index(); return gpd.GeoDataFrame(final,geometry="geometry",crs=crs)

def quality_report(final,report,agebs):
    counts=final.estatus_asignacion.value_counts(); status={s:int(counts.get(s,0)) for s in STATUS_ORDER}
    report.update({"registros_salida":len(final),"estatus_asignacion":status,"suma_estatus":sum(status.values())})
    report["reconciliacion_ok"]=report["suma_estatus"]==report["registros_crudos"]==report["registros_salida"]
    a=final[final.estatus_asignacion=="asignado"].copy(); eq=a.CVEGEO.astype("string")==a.CVEGEO_DENUE.astype("string")
    report["reconciliacion_clave_ageb"]={"registros_asignados":len(a),"coinciden":int(eq.fillna(False).sum()),"no_coinciden":int((~eq.fillna(False)).sum()),"sin_clave_denue":int(a.CVEGEO_DENUE.isna().sum())}
    report["agebs_con_establecimientos"]=int(a.CVEGEO.nunique()); report["agebs_sin_establecimientos"]=int(len(set(agebs.CVEGEO)-set(a.CVEGEO.dropna())))
    if not report["reconciliacion_ok"]: raise RuntimeError("La reconciliación de estatus no cuadra con el universo DENUE")
    return report

def run(csv_name=DEFAULT_CSV):
    agebs=load_agebs(); munis=load_municipios(); df,report=clean(extract(csv_name)); pts,invalid,rep=split_by_coordinates(df,agebs.crs); pts=assign_polygons(pts,agebs,munis); final=build_final(pts,invalid,agebs.crs); report.update(rep); report=quality_report(final,report,agebs)
    PROCESSED_DIR.mkdir(parents=True,exist_ok=True); gpkg=PROCESSED_DIR/"denue_2026_ageb.gpkg"; js=PROCESSED_DIR/"denue_2026_reporte_calidad.json"
    final.to_file(gpkg,layer="establecimientos",driver="GPKG"); js.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8"); print(json.dumps(report,indent=2,ensure_ascii=False)); print("Guardado:",gpkg); return final,report

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--csv",default=DEFAULT_CSV); run(p.parse_args().csv)
