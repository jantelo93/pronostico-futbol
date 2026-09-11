"""
Modelo de pronostico de partidos de futbol.
Descarga resultados, recalcula el modelo y genera el dashboard HTML.
Se ejecuta solo en GitHub Actions. No requiere instalacion local.
"""
import os, re, io, json, math, glob, time, shutil, subprocess, unicodedata
import collections, difflib
from datetime import datetime, timedelta, timezone
import numpy as np
from scipy.optimize import minimize
from scipy.stats import poisson
import urllib.request, urllib.error

HOY = datetime.now(timezone.utc)
BOLIVIA = timezone(timedelta(hours=-4))
DATOS = "_datos"

# ---------------------------------------------------------------- 1. DESCARGA
REPOS = {
    "champions-league": [("champions-league/*/cl.txt", "UCL"), ("champions-league/*/clq.txt", "UCL")],
    "england":   [("england/*/1-premierleague.txt", "ENG")],
    "espana":    [("espana/*/1-liga.txt", "ESP")],
    "deutschland":[("deutschland/*/1-bundesliga.txt", "GER")],
    "italy":     [("italy/*/1-seriea.txt", "ITA")],
    "europe":    [("europe/france/*_fr1*.txt", "FRA"), ("europe/portugal/*.txt", "POR"),
                  ("europe/netherlands/*.txt", "NED"), ("europe/turkey/*_tr1.txt", "TUR"),
                  ("europe/greece/*_gr1.txt", "GRE"), ("europe/ukraine/*_ua1.txt", "UKR"),
                  ("europe/czech-republic/*_cz1.txt", "CZE"), ("europe/norway/*_no1.txt", "NOR"),
                  ("europe/denmark/*_dk1.txt", "DEN"), ("europe/switzerland/*_ch1.txt", "SUI"),
                  ("europe/slovakia/*_sk1.txt", "SVK"), ("europe/azerbaijan/*_az1.txt", "AZE"),
                  ("europe/poland/*_pl1.txt", "POL"), ("europe/sweden/*_se1.txt", "SWE"),
                  ("europe/russia/*_ru1.txt", "RUS"), ("europe/serbia/*_rs1.txt", "SRB"),
                  ("europe/croatia/*_hr1.txt", "CRO"), ("europe/romania/*_ro1.txt", "ROU")],
}

def descargar():
    os.makedirs(DATOS, exist_ok=True)
    for repo in REPOS:
        destino = os.path.join(DATOS, repo)
        if os.path.isdir(destino):
            continue
        url = f"https://github.com/openfootball/{repo}.git"
        r = subprocess.run(["git", "clone", "--depth", "1", "-q", url, destino],
                           capture_output=True, text=True)
        print(("  OK  " if r.returncode == 0 else "  FALLO ") + repo, flush=True)

# ---------------------------------------------------------------- 2. LECTURA
MESES = dict(Jan=1,Feb=2,Mar=3,Apr=4,May=5,Jun=6,Jul=7,Aug=8,Sep=9,Oct=10,Nov=11,Dec=12)
RE_FECHA = re.compile(r'^\s*(?:#\s*)?(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+([A-Z][a-z]{2})\s+(\d{1,2})(?:\s+(\d{4}))?\s*$')
RE_A = re.compile(r'^\s*(?:\d{1,2}:\d{2}\s+)?(.+?)\s+v\s+(.+?)\s+(\d+)-(\d+)(?:\s*\((\d+)-(\d+)\))?\s*$')
RE_B = re.compile(r'^\s*(?:\d{1,2}:\d{2}\s+)?(\S.*?)\s\s+(\d+)-(\d+)(?:\s*\(\d+-\d+\))?\s\s*(\S.*?)\s*$')

def limpiar(n):
    n = re.sub(r'\s*\((?:[A-Z]{3}\d?)\)\s*$', '', n).strip()
    return re.sub(r'\s+', ' ', n)

def leer(path):
    salida, anio, fecha, mes_prev = [], None, None, None
    try:
        txt = open(path, encoding='utf-8', errors='ignore').read()
    except Exception:
        return salida
    cab = re.search(r'#\s*Date\s+\w{3}\s+\w{3}\s+\d{1,2}\s+(\d{4})', txt[:600])
    if cab:
        anio = int(cab.group(1))
    for linea in txt.splitlines():
        linea = linea.rstrip('\r')
        f = RE_FECHA.match(linea)
        if f:
            mm, dd, yy = f.group(1), int(f.group(2)), f.group(3)
            if yy:
                anio = int(yy); mes_prev = MESES[mm]
            elif anio is not None:
                n = MESES[mm]
                if mes_prev is not None and n < mes_prev:
                    anio += 1
                mes_prev = n
            if anio is None:
                continue
            try:
                fecha = datetime(anio, MESES[mm], dd)
            except Exception:
                fecha = None
            continue
        if fecha is None:
            continue
        if ' v ' in linea:
            m = RE_A.match(linea)
            if not m: continue
            h, a, gh, ga = limpiar(m.group(1)), limpiar(m.group(2)), int(m.group(3)), int(m.group(4))
        else:
            m = RE_B.match(linea)
            if not m: continue
            h, a, gh, ga = limpiar(m.group(1)), limpiar(m.group(4)), int(m.group(2)), int(m.group(3))
        if len(h) < 2 or len(a) < 2:
            continue
        salida.append((fecha, h, a, gh, ga))
    return salida

# --------------------------------------------------------- 3. NOMBRES
DESCARTE = {'fc','cf','ac','sc','afc','ss','ssc','as','sk','fk','ca','cd','ud','rc','rcd',
            'club','de','del','da','do','of','the','calcio','cfc','acf','bc','kv','sv',
            'vfb','vfl','tsg','sad','sa','clube','sporting'}
ALIAS = {
 'bayern munchen':'bayern munich','bayern':'bayern munich','manchester city':'man city',
 'manchester united':'man utd','manchester utd':'man utd','internazionale milano':'inter',
 'internazionale':'inter','inter milano':'inter','atletico de madrid':'atletico madrid',
 'psv eindhoven':'psv','sporting clube portugal':'sporting cp','sporting portugal':'sporting cp',
 'sport lisboa e benfica':'benfica','sl benfica':'benfica','paris saint germain':'psg',
 'paris saint-germain':'psg','olympique marseille':'marseille','olympique lyonnais':'lyon',
 'olympique lyon':'lyon','bayer 04 leverkusen':'leverkusen','bayer leverkusen':'leverkusen',
 'bor monchengladbach':'gladbach','borussia monchengladbach':'gladbach','borussia dortmund':'dortmund',
 'real betis balompie':'betis','real betis':'betis','betis seville':'betis','lille osc':'lille',
 'ssc napoli':'napoli','juventus torino':'juventus','juventus turin':'juventus','ac milan':'milan',
 'as roma':'roma','lazio roma':'lazio','lazio rome':'lazio','atalanta bergamo':'atalanta',
 'tottenham hotspur':'tottenham','newcastle united':'newcastle','feyenoord rotterdam':'feyenoord',
 'galatasaray istanbul':'galatasaray','fenerbahce istanbul':'fenerbahce','club brugge kv':'brugge',
 'club brugge':'brugge','shakhtar donetsk':'shakhtar','shakhtar donetsk':'shakhtar',
 'rasenballsport leipzig':'leipzig','rb leipzig':'leipzig','vfb stuttgart':'stuttgart',
 'pae aek':'aek athen','aek athens':'aek athen','aek athina':'aek athen','aek':'aek athen','lask linz':'lask',
 'slovan bratislava':'slovan','sk slovan bratislava':'slovan','slavia praha':'slavia',
 'slavia prague':'slavia','sk slavia praha':'slavia','bod /glimt':'bodo glimt',
 'bodoe/glimt':'bodo glimt','bodo/glimt':'bodo glimt','bodoe glimt':'bodo glimt',
 'viking':'viking','viking fk':'viking','racing lens':'lens','racing club lens':'lens',
 'racing club de lens':'lens','lens':'lens','como 1907':'como','athletic club':'athletic bilbao',
 'sabah':'sabah masazir','1 cologne':'1 koln','parma':'parma 1913',
 'real sociedad san sebastian':'real sociedad futbol','rc deportivo a coruna':'deportivo la coruna',
 'strasbourg alsace':'strasbourg','stade brest 29':'brest','estac troyes':'troyes',
 'stade rennais':'rennes','hamburger':'hamburger sv','fsv mainz':'mainz',
 'sv 07 elversberg':'elversberg','paderborn 07':'paderborn','brighton hove albion':'brighton',
}
def norm(nombre):
    n = unicodedata.normalize('NFKD', nombre)
    n = ''.join(c for c in n if not unicodedata.combining(c)).lower()
    n = re.sub(r'\(.*?\)', ' ', n)
    n = re.sub(r'[^a-z0-9/ ]', ' ', n)
    n = re.sub(r'\s+', ' ', n).strip()
    if n in ALIAS: return ALIAS[n]
    n2 = ' '.join(t for t in n.split() if t not in DESCARTE).strip()
    if n2 in ALIAS: return ALIAS[n2]
    return n2 or n

def cargar_partidos():
    vistos, salida = set(), []
    for repo, patrones in REPOS.items():
        for patron, comp in patrones:
            for f in sorted(glob.glob(os.path.join(DATOS, patron))):
                for fecha, h, a, gh, ga in leer(f):
                    if fecha > HOY.replace(tzinfo=None):
                        continue
                    h, a = norm(h), norm(a)
                    k = (fecha, h, a)
                    if k in vistos: continue
                    vistos.add(k)
                    salida.append((fecha, h, a, gh, ga, comp))
    salida.sort(key=lambda x: x[0])
    return salida

# ---------------------------------------------------------------- 4. MODELO
K_ELO, VENTAJA_ELO, BASE_ELO = 20.0, 65.0, 1500.0

def ajustar(M, equipos, comps, media_vida, l2):
    ti = {t: i for i, t in enumerate(equipos)}
    ci = {c: i for i, c in enumerate(comps)}
    NT, NC = len(equipos), len(comps)
    ref = (HOY.replace(tzinfo=None) - datetime(2000, 1, 1)).days
    dias = np.array([(m[0] - datetime(2000, 1, 1)).days for m in M])
    w = np.exp(-math.log(2) / media_vida * (ref - dias))
    hi = np.array([ti[m[1]] for m in M]); ai = np.array([ti[m[2]] for m in M])
    gh = np.array([m[3] for m in M], float); ga = np.array([m[4] for m in M], float)
    cj = np.array([ci[m[5]] for m in M])
    def objetivo(p):
        att, dfn = p[:NT], p[NT:2*NT]
        c, hf = p[2*NT:2*NT+NC], p[2*NT+NC:]
        eh = c[cj] + hf[cj] + att[hi] - dfn[ai]
        ea = c[cj] + att[ai] - dfn[hi]
        lh = np.exp(np.clip(eh, -4, 3)); la = np.exp(np.clip(ea, -4, 3))
        f = np.sum(w*(lh - gh*eh)) + np.sum(w*(la - ga*ea)) + l2*(np.sum(att**2)+np.sum(dfn**2))
        rh = w*(lh - gh); ra = w*(la - ga)
        g = np.zeros_like(p)
        np.add.at(g, hi, rh);          np.add.at(g, ai, ra)
        np.add.at(g, NT+ai, -rh);      np.add.at(g, NT+hi, -ra)
        np.add.at(g, 2*NT+cj, rh+ra);  np.add.at(g, 2*NT+NC+cj, rh)
        g[:NT] += 2*l2*att; g[NT:2*NT] += 2*l2*dfn
        return f, g
    p0 = np.zeros(2*NT + 2*NC); p0[2*NT:2*NT+NC] = 0.2; p0[2*NT+NC:] = 0.25
    r = minimize(objetivo, p0, jac=True, method='L-BFGS-B',
                 options={'maxiter': 700, 'maxfun': 800})
    return r.x

def calcular_elo(M):
    R = {}
    for fecha, h, a, gh, ga, c in M:
        rh, ra = R.get(h, BASE_ELO), R.get(a, BASE_ELO)
        e = 1/(1+10**(-((rh+VENTAJA_ELO)-ra)/400))
        d = abs(gh-ga); mult = 1.0 if d <= 1 else (1.5 if d == 2 else 1.75+(d-3)/8)
        res = 1.0 if gh > ga else (0.5 if gh == ga else 0.0)
        delta = K_ELO*mult*(res-e)
        R[h] = rh+delta; R[a] = ra-delta
    return R

def calcular_momento(M, equipos, att, dfn, c_, h_, n=10):
    ti = {t: i for i, t in enumerate(equipos)}
    reg = collections.defaultdict(list)
    for fecha, h, a, gh, ga, c in M:
        if c not in c_: continue
        lh = math.exp(c_[c]+h_[c]+att[ti[h]]-dfn[ti[a]])
        la = math.exp(c_[c]+att[ti[a]]-dfn[ti[h]])
        reg[h].append((fecha, gh-lh, la-ga))
        reg[a].append((fecha, ga-la, lh-gh))
    out = {}
    for t, v in reg.items():
        v = sorted(v)[-n:]
        if len(v) < 5:
            out[t] = (0.0, 0.0)
        else:
            out[t] = (round(sum(x[1] for x in v)/len(v), 2),
                      round(sum(x[2] for x in v)/len(v), 2))
    return out

# -------------------------------------------------------------- 5. FIXTURES
COMPETENCIAS = {"CL": "UCL", "PL": "ENG", "PD": "ESP", "BL1": "GER", "SA": "ITA", "FL1": "FRA"}
NOMBRES = {"UCL":"Champions League","ENG":"Premier League","ESP":"LaLiga",
           "GER":"Bundesliga","ITA":"Serie A","FRA":"Ligue 1"}

def pedir(url, token):
    req = urllib.request.Request(url, headers={"X-Auth-Token": token})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())

def traer_api(token, equipos):
    """Descarga de football-data.org los resultados recientes y los partidos pendientes."""
    fx, planteles, resultados = {}, {}, []
    if not token:
        print("  Sin token: no se descarga nada de la API.")
        return fx, planteles, resultados
    temporada = HOY.year if HOY.month >= 7 else HOY.year - 1
    for codigo, comp in COMPETENCIAS.items():
        try:
            d = pedir(f"https://api.football-data.org/v4/competitions/{codigo}/matches?season={temporada}", token)
        except Exception as e:
            print(f"  {codigo}: error {e}")
            time.sleep(7); continue
        partidos = d.get("matches", [])
        nombres = set()
        for m in partidos:
            for lado in ("homeTeam", "awayTeam"):
                if m[lado].get("name"): nombres.add(m[lado]["name"])
        mapa = emparejar(nombres, equipos)
        planteles[comp] = sorted({mapa[n] for n in nombres if mapa.get(n)})
        prox, jugados = [], 0
        for m in partidos:
            hn, an = m["homeTeam"].get("name"), m["awayTeam"].get("name")
            h, a = mapa.get(hn), mapa.get(an)
            if not h or not a: continue
            t = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).astimezone(BOLIVIA)
            estado = m.get("status")
            if estado in ("SCHEDULED", "TIMED"):
                prox.append({"d": t.strftime("%Y-%m-%d"), "t": t.strftime("%H:%M"),
                             "h": h, "a": a, "hn": hn, "an": an, "ord": t.timestamp()})
            elif estado == "FINISHED":
                ft = (m.get("score") or {}).get("fullTime") or {}
                gh, ga = ft.get("home"), ft.get("away")
                if gh is None or ga is None: continue
                resultados.append((t.replace(tzinfo=None).replace(hour=0, minute=0),
                                   h, a, int(gh), int(ga), comp))
                jugados += 1
        prox.sort(key=lambda x: x["ord"])
        fx[comp] = prox[:24]
        print(f"  {NOMBRES[comp]}: {len(fx[comp])} pendientes, {jugados} jugados, "
              f"{len(planteles[comp])} equipos")
        time.sleep(7)   # el plan gratuito permite 10 llamadas por minuto
    return fx, planteles, resultados


def fusionar(M, resultados):
    """Suma los resultados de la API que no esten ya en el historico de openfootball."""
    indice = collections.defaultdict(list)
    for f, h, a, gh, ga, c in M:
        indice[(h, a)].append(f)
    nuevos = []
    for f, h, a, gh, ga, c in resultados:
        if any(abs((f - v).days) <= 3 for v in indice[(h, a)]):
            continue
        indice[(h, a)].append(f)
        nuevos.append((f, h, a, gh, ga, c))
    if nuevos:
        M = sorted(M + nuevos, key=lambda x: x[0])
        print(f"   {len(nuevos)} partidos nuevos incorporados desde la API")
        for f, h, a, gh, ga, c in nuevos[-6:]:
            print(f"     {f.strftime('%d/%m')} {c}  {h} {gh}-{ga} {a}")
    else:
        print("   Sin partidos nuevos que incorporar")
    return M

def emparejar(nombres, equipos):
    conocidos = set(equipos)
    mapa = {}
    for n in nombres:
        k = norm(n)
        if k in conocidos:
            mapa[n] = k; continue
        g = difflib.get_close_matches(k, list(conocidos), 1, 0.78)
        mapa[n] = g[0] if g else None
        if not g:
            print(f"    sin equivalencia: {n}  ->  '{k}'")
    return mapa

# ------------------------------------------------------------- 6. PRINCIPAL
# calibracion por competencia (factor de empate, temperatura), encogida al 75%
CALIBRACION = {"ENG":[0.95,0.95],"ESP":[1.10,0.85],"GER":[1.15,0.95],"ITA":[1.35,0.85],
               "FRA":[1.05,1.00],"POR":[0.90,0.95],"NED":[0.95,1.00],"UCL":[0.80,0.85],
               "TUR":[1.10,0.95],"GRE":[1.35,1.20],"CZE":[1.15,0.90],"RUS":[1.15,0.85],
               "SUI":[0.90,1.15],"SWE":[0.75,1.35]}
FIABILIDAD = {"UCL":[56.3,0.5686],"GER":[52.5,0.5922],"FRA":[51.2,0.5973],"ITA":[51.6,0.5977],
              "ESP":[49.3,0.6032],"ENG":[48.1,0.6191]}
CONFIANZA = [[0.33,0.40,36.7],[0.40,0.45,42.6],[0.45,0.50,47.1],[0.50,0.55,49.4],
             [0.55,0.65,60.4],[0.65,0.75,67.5],[0.75,1.01,79.8]]
PESOS = [0.45, 0.35, 0.20]

def main():
    print("1. Descargando datos historicos", flush=True)
    descargar()
    print("2. Leyendo partidos", flush=True)
    M = cargar_partidos()
    equipos = sorted({m[1] for m in M} | {m[2] for m in M})
    comps = sorted({m[5] for m in M})
    print(f"   {len(M)} partidos | {len(equipos)} equipos | {len(comps)} competencias", flush=True)
    print("3. Trayendo resultados y partidos pendientes de la API", flush=True)
    fx, planteles, resultados = traer_api(os.environ.get("FOOTBALL_DATA_TOKEN", "").strip(), equipos)
    M = fusionar(M, resultados)
    print("4. Calculando Elo", flush=True)
    elo = calcular_elo(M)
    print("5. Ajustando ataque y defensa (nivel estructural)", flush=True)
    PL = ajustar(M, equipos, comps, 540.0, 0.02)
    print("6. Ajustando forma reciente", flush=True)
    PS = ajustar(M, equipos, comps, 120.0, 0.06)
    NT, NC = len(equipos), len(comps)
    attL, defL = PL[:NT], PL[NT:2*NT]
    cL = dict(zip(comps, PL[2*NT:2*NT+NC])); hL = dict(zip(comps, PL[2*NT+NC:]))
    attS, defS = PS[:NT], PS[NT:2*NT]
    cS = dict(zip(comps, PS[2*NT:2*NT+NC])); hS = dict(zip(comps, PS[2*NT+NC:]))
    print("7. Calculando momento", flush=True)
    mom = calcular_momento(M, equipos, attL, defL, cL, hL)
    if not planteles:
        print("   Sin fixtures: se usan todos los equipos conocidos por competencia.")
        porcomp = collections.defaultdict(set)
        for f, h, a, gh, ga, c in M:
            if (HOY.replace(tzinfo=None) - f).days < 400:
                porcomp[c].add(h); porcomp[c].add(a)
        planteles = {c: sorted(v) for c, v in porcomp.items() if c in NOMBRES}
    ti = {t: i for i, t in enumerate(equipos)}
    usados = sorted({t for v in planteles.values() for t in v})
    datos = {"generado": datetime.now(BOLIVIA).strftime("%d/%m/%Y %H:%M"),
             "nom": NOMBRES, "w": PESOS, "cal": CALIBRACION, "lam": 0.75,
             "conf": CONFIANZA, "rel": FIABILIDAD, "rosters": planteles, "fx": fx,
             "cL": {k: v for k, v in cL.items() if k in NOMBRES},
             "hL": {k: v for k, v in hL.items() if k in NOMBRES},
             "cS": {k: v for k, v in cS.items() if k in NOMBRES},
             "hS": {k: v for k, v in hS.items() if k in NOMBRES},
             "nPartidos": len(M), "teams": {}}
    for t in usados:
        i = ti[t]
        datos["teams"][t] = {"elo": round(elo.get(t, BASE_ELO), 1),
            "aL": round(float(attL[i]), 4), "dL": round(float(defL[i]), 4),
            "aS": round(float(attS[i]), 4), "dS": round(float(defS[i]), 4),
            "fA": mom.get(t, (0.0, 0.0))[0], "fD": mom.get(t, (0.0, 0.0))[1]}
    print("8. Generando dashboard", flush=True)
    from plantilla import construir
    open("index.html", "w", encoding="utf-8").write(construir(datos))
    print(f"   Listo: {len(datos['teams'])} equipos, "
          f"{sum(len(v) for v in fx.values())} partidos pendientes", flush=True)

if __name__ == "__main__":
    main()
