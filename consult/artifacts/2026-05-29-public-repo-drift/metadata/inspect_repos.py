from pathlib import Path
import json, subprocess, os
root=Path(__file__).resolve().parents[1]
clones=root/'_clones'
local_root=Path('/Users/farhad/Code/PokerBot')
repos={
'Pav1602/fullhouse-engine': clones/'Pav1602_fullhouse-engine',
'vladimirfilip/fullhouse-engine': clones/'vladimirfilip_fullhouse-engine',
'TobyCoad/fullhouse-engine': clones/'TobyCoad_fullhouse-engine',
'MatusGib/fullhouse-engine': clones/'MatusGib_fullhouse-engine',
'stoppedtime24/fullhouse-engine': clones/'stoppedtime24_fullhouse-engine',
'Benjamin-Yu-Sheng-Chang/fullhouse-hackathon': clones/'Benjamin-Yu-Sheng-Chang_fullhouse-hackathon',
'Mehedi-dev-2404/fullhouse-engine': clones/'Mehedi-dev-2404_fullhouse-engine',
'famadeo/fullhouse-engine(local)': local_root/'ext/public-bots/famadeo',
'agrawalneel25/fullhouse-engine(neel-work local)': local_root/'ext/public-bots/neel',
}

def git(repo,*args):
    try:
        return subprocess.check_output(['git','-C',str(repo),*args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception as e:
        return None

def rel(p, base):
    try: return str(p.relative_to(base))
    except: return str(p)

def bot_dirs(repo):
    bots=repo/'bots'
    out=[]
    if not bots.is_dir(): return out
    for d in sorted([p for p in bots.iterdir() if p.is_dir()]):
        bp=d/'bot.py'
        data=[]
        if (d/'data').is_dir():
            data=[str(f.relative_to(d)) for f in sorted((d/'data').rglob('*')) if f.is_file()]
        out.append({
            'name': d.name,
            'path': rel(d, repo),
            'bot_py': rel(bp, repo) if bp.exists() else None,
            'bot_py_size': bp.stat().st_size if bp.exists() else None,
            'bot_py_lines': sum(1 for _ in bp.open(errors='ignore')) if bp.exists() else None,
            'data_files': data,
            'data_bytes': sum((d/f).stat().st_size for f in data) if data else 0,
        })
    return out

summary=[]
for name,path in repos.items():
    item={'repo': name, 'path': str(path), 'exists': path.exists()}
    if path.exists():
        item['head_sha']=git(path,'rev-parse','HEAD')
        item['head_short']=git(path,'rev-parse','--short=12','HEAD')
        item['head_date']=git(path,'show','-s','--format=%cI','HEAD')
        item['head_subject']=git(path,'show','-s','--format=%s','HEAD')
        item['default_branch']=git(path,'branch','--show-current')
        item['bots']=bot_dirs(path)
        readmes=[]
        for nm in ['README.md','readme.md','README.txt']:
            f=path/nm
            if f.exists():
                txt=f.read_text(errors='ignore')[:5000]
                readmes.append({'file':nm,'mentions':[line for line in txt.splitlines() if 'skant' in line.lower() or 'bot' in line.lower()][:20]})
        item['readme_mentions']=readmes
    summary.append(item)
print(json.dumps(summary, indent=2))
