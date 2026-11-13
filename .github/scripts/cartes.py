import datetime as dt
import json
import os
import urllib.request
from xml.sax.saxutils import escape

LOGIN = "vortexturize-ai"
DEPOTS = [("carte-paperasse.svg", ["paperasse"]), ("carte-crochetage.svg", ["Crochetage", "ILikeBaylife"])]
SORTIE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "cartes")
ROUGE = "#E8000B"
POLICE = "'Segoe UI',Ubuntu,'Helvetica Neue',Arial,sans-serif"

ICONE_DEPOT = ("M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z")
ICONE_ETOILE = ("M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z")
ICONE_FORK = ("M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z")


def graphql(requete, variables):
    jeton = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    corps = json.dumps({"query": requete, "variables": variables}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=corps,
                                 headers={"Authorization": f"bearer {jeton}", "Content-Type": "application/json",
                                          "User-Agent": "cartes-profil"})
    with urllib.request.urlopen(req, timeout=30) as r:
        rep = json.load(r)
    return rep.get("data") or {}


def contributions(jours=31):
    fin = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    debut = fin - dt.timedelta(days=jours - 1)
    q = """query($login:String!,$de:DateTime!,$a:DateTime!){user(login:$login){
      contributionsCollection(from:$de,to:$a){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    d = graphql(q, {"login": LOGIN, "de": debut.isoformat(), "a": fin.isoformat()})
    semaines = d["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    jours_ = [j for s in semaines for j in s["contributionDays"]]
    return jours_[-jours:]


def depot(noms):
    q = """query($o:String!,$n:String!){repository(owner:$o,name:$n){name description stargazerCount forkCount
      primaryLanguage{name color}}}"""
    for n in noms:
        try:
            r = graphql(q, {"o": LOGIN, "n": n}).get("repository")
        except Exception:
            r = None
        if r:
            return r
    return None


def lisse(points):
    d = f"M{points[0][0]:.1f},{points[0][1]:.1f}"
    for i in range(len(points) - 1):
        p0 = points[max(0, i - 1)]
        p1, p2 = points[i], points[i + 1]
        p3 = points[min(len(points) - 1, i + 2)]
        bas, haut = min(p1[1], p2[1]), max(p1[1], p2[1])
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, min(haut, max(bas, p1[1] + (p2[1] - p0[1]) / 6)))
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, min(haut, max(bas, p2[1] - (p3[1] - p1[1]) / 6)))
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def graphique(jours):
    W, H = 1000, 420
    x0, x1, y0, y1 = 80, 965, 70, 350
    vals = [j["contributionCount"] for j in jours]
    haut = max(4, max(vals))
    haut = haut + (-haut % 4)
    n = len(vals)
    pts = [(x0 + (x1 - x0) * i / max(1, n - 1), y1 - (y1 - y0) * v / haut) for i, v in enumerate(vals)]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<defs><linearGradient id="aire" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ROUGE}" stop-opacity=".55"/>'
         f'<stop offset="1" stop-color="{ROUGE}" stop-opacity=".04"/></linearGradient></defs>',
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="#0d1117" stroke="{ROUGE}"/>',
         f'<text x="{W / 2}" y="38" text-anchor="middle" font-family="{POLICE}" font-size="18" font-weight="600" fill="#ffffff">Mes contributions</text>']
    for k in range(5):
        y = y1 - (y1 - y0) * k / 4
        s.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="#ffffff" stroke-opacity=".12" stroke-dasharray="4 4"/>')
        s.append(f'<text x="{x0 - 12}" y="{y + 4:.1f}" text-anchor="end" font-family="{POLICE}" font-size="11" fill="#ffffff">{haut * k // 4}</text>')
    for i, j in enumerate(jours):
        if i % 3 == 0 or i == n - 1:
            x = pts[i][0]
            s.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" stroke="#ffffff" stroke-opacity=".05"/>')
            s.append(f'<text x="{x:.1f}" y="{y1 + 20}" text-anchor="middle" font-family="{POLICE}" font-size="11" fill="#ffffff">{int(j["date"][8:])}</text>')
    courbe = lisse(pts)
    s.append(f'<path d="{courbe} L{pts[-1][0]:.1f},{y1} L{pts[0][0]:.1f},{y1} Z" fill="url(#aire)"/>')
    s.append(f'<path d="{courbe}" fill="none" stroke="{ROUGE}" stroke-width="2.5"/>')
    for x, y in pts:
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#ffffff"/>')
    s.append(f'<text x="{(x0 + x1) / 2}" y="{H - 18}" text-anchor="middle" font-family="{POLICE}" font-size="12" fill="#ffffff">Jours</text>')
    s.append(f'<text transform="translate(24,{(y0 + y1) / 2}) rotate(-90)" text-anchor="middle" font-family="{POLICE}" font-size="12" fill="#ffffff">Contributions</text>')
    s.append("</svg>")
    return "\n".join(s)


def couper(texte, n):
    mots, lignes, cour = (texte or "").split(), [], ""
    for m in mots:
        if len(cour) + len(m) + 1 > n:
            lignes.append(cour)
            cour = m
        else:
            cour = (cour + " " + m).strip()
    if cour:
        lignes.append(cour)
    if len(lignes) > 2:
        lignes = lignes[:2]
        lignes[1] = lignes[1][: n - 1].rstrip() + "…"
    return lignes


def carte(r):
    W, H = 400, 120
    lang = r.get("primaryLanguage") or {}
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="4.5" fill="{ROUGE}" stroke="{ROUGE}"/>',
         f'<g transform="translate(25,22)"><path d="{ICONE_DEPOT}" fill="#000000"/></g>',
         f'<text x="50" y="35" font-family="{POLICE}" font-size="16" font-weight="700" fill="#000000">{escape(r["name"])}</text>']
    for i, l in enumerate(couper(r.get("description"), 52)):
        s.append(f'<text x="25" y="{62 + i * 17}" font-family="{POLICE}" font-size="13" fill="#000000">{escape(l)}</text>')
    x = 25
    if lang:
        s.append(f'<circle cx="{x + 6}" cy="101" r="6" fill="{lang.get("color") or "#000000"}" stroke="#000000" stroke-width=".8"/>')
        s.append(f'<text x="{x + 18}" y="105" font-family="{POLICE}" font-size="12" fill="#000000">{escape(lang["name"])}</text>')
        x += 30 + 7 * len(lang["name"])
    for icone, val in ((ICONE_ETOILE, r["stargazerCount"]), (ICONE_FORK, r["forkCount"])):
        s.append(f'<g transform="translate({x},93)"><path d="{icone}" fill="#000000"/></g>')
        s.append(f'<text x="{x + 21}" y="105" font-family="{POLICE}" font-size="12" fill="#000000">{val}</text>')
        x += 60
    s.append("</svg>")
    return "\n".join(s)


def main():
    os.makedirs(SORTIE, exist_ok=True)
    with open(os.path.join(SORTIE, "contributions.svg"), "w", encoding="utf-8") as f:
        f.write(graphique(contributions()))
    for fichier, noms in DEPOTS:
        r = depot(noms)
        if r:
            with open(os.path.join(SORTIE, fichier), "w", encoding="utf-8") as f:
                f.write(carte(r))
    print("cartes à jour")


if __name__ == "__main__":
    main()
