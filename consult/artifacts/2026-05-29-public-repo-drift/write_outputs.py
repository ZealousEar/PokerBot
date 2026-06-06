#!/usr/bin/env python3
from pathlib import Path
import json, random, re, hashlib
ROOT=Path('/Users/farhad/Code/PokerBot')
ART=ROOT/'consult/artifacts/2026-05-29-public-repo-drift'
LOG=ART/'logs'
BB=100

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):
            h.update(c)
    return h.hexdigest()

def load(name):
    return json.load(open(LOG/name))

def bb(chips,hands):
    return (chips/BB)/(hands/100) if hands else None

def run_entry(r, repo=None, head=None, bot_path=None, validator=True, new=False, drifted=None, local=None, verdict=None, notes=None):
    return {
        'repo': repo or r.get('repo',''),
        'head_sha': head or r.get('head_sha',''),
        'bot_path': bot_path or r.get('bot_path',''),
        'validator_pass': validator,
        'scheduled_hands': r['attempted_hands'],
        'actual_hands': r['hands_played'],
        'mean_bb_per_100_scheduled': r['hero_bb_per_100'],
        'mean_bb_per_100_actual': r['hero_actual_bb_per_100'],
        'ci_low': r['ci_low'],
        'ci_high': r['ci_high'],
        'hero_errors': r['hero_errors'],
        'opp_errors': r['opponent_errors'],
        'p99_latency_s': r['hero_p99_decide_latency_s'],
        'verdict': verdict or r['verdict'],
        'new_threat': new,
        'drifted': drifted,
        'local_snapshot_sha': local,
        'log_path': r['log_path'],
        'json_path': r['json_path'],
        'notes': notes or '',
    }

def aggregate(name, files, repo, head, bot_path, new, drifted, local, notes=''):
    rows=[load(f) for f in files]
    samples=[]
    for r in rows: samples += r['samples']
    rng=random.Random(0xD21F29)
    means=[]
    for _ in range(5000):
        chips=hands=0
        for _ in range(len(samples)):
            s=samples[rng.randrange(len(samples))]
            chips+=int(s['chip_delta']); hands+=int(s.get('metric_hands',s['hands']))
        means.append(bb(chips,hands))
    means.sort()
    chips=sum(s['chip_delta'] for s in samples)
    sched=sum(s.get('metric_hands',s['hands']) for s in samples)
    actual=sum(r['hands_played'] for r in rows)
    low=means[int(5000*.025)]; high=means[int(5000*.975)]
    mean=bb(chips,sched); actualbb=bb(chips,actual)
    verdict='GREEN' if mean>0 and low>-20 else ('RED' if high<0 or (low<=-20 and mean<=0) else 'AMBER')
    return {
        'repo':repo,'head_sha':head,'bot_path':bot_path,'validator_pass':True,
        'scheduled_hands':sched,'actual_hands':actual,
        'mean_bb_per_100_scheduled':mean,'mean_bb_per_100_actual':actualbb,
        'ci_low':low,'ci_high':high,
        'hero_errors':sum(r['hero_errors'] for r in rows),'opp_errors':sum(r['opponent_errors'] for r in rows),
        'p99_latency_s':max(r['hero_p99_decide_latency_s'] for r in rows),'verdict':verdict,
        'new_threat':new,'drifted':drifted,'local_snapshot_sha':local,
        'component_runs':[str(LOG/f) for f in files], 'notes':notes,
    }

def partial_from_log(filename, repo, head, bot_path, validator, new, drifted, local, note):
    p=LOG/filename; chips=hands=sched=n=hero_err=opp_err=0
    for line in p.read_text().splitlines():
        m=re.search(r'hands=\s*(\d+)/(\d+) hero_chip=\s*([+-]?\d+).*hero_err=(\d+) opp_err=(\d+)', line)
        if m:
            n+=1; hands+=int(m.group(1)); sched+=int(m.group(2)); chips+=int(m.group(3)); hero_err+=int(m.group(4)); opp_err+=int(m.group(5))
    return {
        'repo':repo,'head_sha':head,'bot_path':bot_path,'validator_pass':validator,
        'scheduled_hands':sched,'actual_hands':hands,
        'mean_bb_per_100_scheduled':bb(chips,sched),'mean_bb_per_100_actual':bb(chips,hands),
        'ci_low':None,'ci_high':None,'hero_errors':hero_err,'opp_errors':opp_err,
        'p99_latency_s':None,'verdict':'TIMEBOXED_PARTIAL','new_threat':new,'drifted':drifted,
        'local_snapshot_sha':local,'log_path':str(p),'completed_orientations':n,'notes':note,
    }

prior = {
 'vladimir_prior_snapshot': {'repo':'vladimirfilip/fullhouse-engine','head_sha':'1fbf389224eed471a54768898acdecb093a2bd6e','bot_path':'bots/vlad/bot.py','validator_pass':True,'scheduled_hands':400000,'actual_hands':20081,'mean_bb_per_100_scheduled':3.70,'mean_bb_per_100_actual':73.70,'ci_low':2.40,'ci_high':5.00,'hero_errors':0,'opp_errors':0,'p99_latency_s':0.0399,'verdict':'GREEN','new_threat':False,'drifted':False,'local_snapshot_sha':'1fbf389224eed471a54768898acdecb093a2bd6e','notes':'Prior 2026-05-28 public saturation baseline, not rerun for this exact snapshot.'},
 'famadeo': {'repo':'famadeo/fullhouse-engine','head_sha':'c94dace1c6bf523aa49e9c149d897c6b71a19c5e','bot_path':'bots/codex_holdem/bot.py','validator_pass':True,'scheduled_hands':200000,'actual_hands':43914,'mean_bb_per_100_scheduled':0.65,'mean_bb_per_100_actual':2.96,'ci_low':-1.30,'ci_high':2.60,'hero_errors':0,'opp_errors':0,'p99_latency_s':0.0643,'verdict':'GREEN','new_threat':False,'drifted':False,'local_snapshot_sha':'c94dace1c6bf523aa49e9c149d897c6b71a19c5e','notes':'Live main unchanged from local baseline; prior H2H reused.'},
 'neel': {'repo':'agrawalneel25/fullhouse-engine','head_sha':'071d54c302cbd2d9d5fcc773260e7f5f894c642f','bot_path':'bots/neel/bot.py','validator_pass':True,'scheduled_hands':200000,'actual_hands':102276,'mean_bb_per_100_scheduled':14.69,'mean_bb_per_100_actual':28.73,'ci_low':13.50,'ci_high':15.81,'hero_errors':0,'opp_errors':0,'p99_latency_s':0.0633,'verdict':'GREEN','new_threat':False,'drifted':False,'local_snapshot_sha':'071d54c302cbd2d9d5fcc773260e7f5f894c642f','notes':'Tracked branch neel-work unchanged from local baseline; prior H2H reused.'},
 'dominic_prior_snapshot': {'repo':'TobyCoad/fullhouse-engine','head_sha':'fc1cfb6413389f431db8e360d2a0b73b3feaabaf','bot_path':'bots/dominic/bot.py','validator_pass':True,'scheduled_hands':200000,'actual_hands':77337,'mean_bb_per_100_scheduled':-1.22,'mean_bb_per_100_actual':-3.15,'ci_low':-3.24,'ci_high':0.72,'hero_errors':0,'opp_errors':0,'p99_latency_s':0.0764,'verdict':'AMBER','new_threat':False,'drifted':False,'local_snapshot_sha':'fc1cfb6413389f431db8e360d2a0b73b3feaabaf','notes':'Prior 2026-05-28 local snapshot baseline, superseded by live drift test below.'},
}

results=dict(prior)
results['pav_skantbot7_9']=run_entry(load('pav_skantbot7_9_s142.json'), new=True, drifted=True, local=None, notes='Pav canonical/latest inferred from play_human_hu.py default skantbot7.9 and highest skantbot version. First-pass 20k only; GREEN so no escalation.')
results['pav_skantbot7_6']=run_entry(load('pav_skantbot7_6_s142.json'), new=True, drifted=True, local=None, notes='Headline requested variant; first-pass 20k only; GREEN so no escalation.')
results['vladimir_live_vlad_partial']=partial_from_log('vladimir_live_vlad_s142.log','vladimirfilip/fullhouse-engine','f8b8723ce324685429a5098d6b76586005010210','bots/vlad/bot.py',True,False,True,'1fbf389224eed471a54768898acdecb093a2bd6e','Live repo drifted and lacks public bots/vlad/data/gto_strategy.npz; validator passed via Monte Carlo fallback. H2H aborted/time-boxed after 3 completed orientations because projected first pass exceeded 20 min.')
results['dominic_live_master']=aggregate('dominic_live_master',['dominic_live_master_100k_b142_s142.json','dominic_live_master_100k_b242_s242.json'],'TobyCoad/fullhouse-engine','93516f33675d32beaeb3228a554c1323926cd71d','bots/master/bot.py',False,True,'fc1cfb6413389f431db8e360d2a0b73b3feaabaf','Live default repo no longer has bots/dominic; bots/master is the strongest/canonical named bot. RED after required 100k x bases 142,242 escalation.')
results['stoppedtime24_mybot']=run_entry(load('stoppedtime24_mybot_s142.json'), new=True, drifted=True, local=None, notes='Top-5 recent fork non-template bot; first-pass 20k GREEN.')
results['mehedi_mybot']=run_entry(load('mehedi_mybot_s142.json'), new=True, drifted=True, local=None, notes='Top-5 recent fork non-template bot; first-pass 20k RED. 100k escalation was attempted but time-boxed; partial remains negative.')
results['mehedi_mybot_100k_partial']=partial_from_log('mehedi_mybot_100k_b142_s142.log','Mehedi-dev-2404/fullhouse-engine','aa14a35a4f185f8608ae962aef17a7c620909a4b','bots/mybot/bot.py',True,True,True,None,'Escalation attempt partial only; aborted after runtime projected ~50 min per 100k base.')

out={
 'created_at':'2026-05-29T00:00:00Z',
 'top_line_verdict':'PUBLIC_PRIORS_INVALIDATED',
 'hero_zip':'submissions/v_final.zip',
 'hero_sha256':sha(ROOT/'submissions/v_final.zip'),
 'artifact_dir':str(ART),
 'forks_api_count':30,
 'forks_top5_inspected':['vladimirfilip/fullhouse-engine','MatusGib/fullhouse-engine','stoppedtime24/fullhouse-engine','Benjamin-Yu-Sheng-Chang/fullhouse-hackathon','Mehedi-dev-2404/fullhouse-engine'],
 'results':results,
}
(ART/'RESULTS.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'wrote':str(ART/'RESULTS.json'),'verdict':out['top_line_verdict'],'entries':len(results)},indent=2))
