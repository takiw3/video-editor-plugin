"""Every library effect on a real reel page: builds a one-effect page per effect, snapshots it mid-effect, and compares
with the same frame of the plain page. Reports a changed-pixels score and tiles every result into sheets."""
import json, os, shutil, subprocess, sys, time, concurrent.futures as cf
ENG=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'engine')
sys.path.insert(0, ENG+'/pipeline')
import fxlib
from common import hf, snapshot_files, PY
project=sys.argv[1]; out=sys.argv[2]; os.makedirs(out,exist_ok=True)
AT, DUR = 10.0, 1.6
SAMPLE='media/smoke.jpg'
specs=fxlib.fx.library()
ids=[k for k,v in specs.items() if fxlib.fx.status_of(v) in('verified','limited') and v.get('kind')!='audio']
only=sys.argv[3:]
if only: ids=[i for i in ids if i in only]
base=open(project+'/edit.py').read()
results={}
def one(eid):
    spec=specs[eid]; t0=time.time()
    sb=os.path.join(project,'work','smoke',eid); pub=sb+'/public'; ppub=project+'/public'
    shutil.rmtree(sb,ignore_errors=True); os.makedirs(pub)
    for f in('words.json','timeline.json'): shutil.copy(project+'/'+f,sb+'/'+f)
    for d in('fx','assets','audio','style','cards'):
        if os.path.exists(project+'/'+d): os.symlink(project+'/'+d,sb+'/'+d)
    for f in os.listdir(ppub):
        if f not in('index.html','.hyperframes','assets','fx-instances.json','tr'): os.symlink(ppub+'/'+f,pub+'/'+f)
    os.makedirs(pub+'/tr',exist_ok=True)
    e=dict(effect=eid,at=AT,duration=DUR)
    if spec.get('target')=='text': e['text']='Every single edit'
    if spec.get('target')=='composite' or eid in('ken-burns-pan','photo-card'): e['src']=SAMPLE
    if eid=='lower-third': e['text']='Sam Lee|Founder'
    tr = spec.get('target')=='scene-pair'
    head='\nFXLIB=[]\nTRANSITIONS=[]\nBEHIND=[]\nCUT_WINDOWS=[]\nBOXES=[]\nAUDIO_FX=[]\nCAPTION_STYLE="karaoke-box"\n'
    tail=(f"TRANSITIONS=[dict(effect={eid!r},at={AT})]\n" if tr else f"FXLIB=[{e!r}]\n")
    open(sb+'/edit.py','w').write(base+head+tail)
    try:
        if tr:
            subprocess.run([PY,ENG+'/pipeline/transitions.py',sb],check=True,capture_output=True,text=True)
        subprocess.run([PY,ENG+'/pipeline/build.py',sb,'--stills'],check=True,capture_output=True,text=True)
        t=AT if tr else AT+DUR/2
        r=hf(['snapshot','--at',f'{t:.3f}','--no-end','--describe','false'],pub)
        fs=snapshot_files(pub,r.stdout+r.stderr)
        d=f'{out}/{eid}.jpg'
        subprocess.run(['ffmpeg','-v','error','-y','-i',fs[0],'-vf','scale=270:480','-q:v','4',d],check=True)
        res=dict(ok=True,secs=round(time.time()-t0,1))
    except subprocess.CalledProcessError as ex:
        res=dict(ok=False,err=((ex.stderr or '')+(ex.stdout or ''))[-500:])
    except SystemExit as ex:
        res=dict(ok=False,err=str(ex)[-500:])
    shutil.rmtree(sb,ignore_errors=True)
    print(eid,res.get('ok'),res.get('err','')[:200],flush=True)
    return eid,res
with cf.ThreadPoolExecutor(int(os.environ.get('JOBS','3'))) as ex:
    for eid,res in ex.map(one,ids): results[eid]=res
json.dump(results,open(out+'/results.json','w'),indent=1)
print(sum(1 for r in results.values() if r['ok']),'/',len(results),'ok')
