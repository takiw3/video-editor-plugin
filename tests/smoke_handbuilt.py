import os,re,shutil,subprocess,sys,json,concurrent.futures as cf
ENG=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'engine')
sys.path.insert(0,ENG+'/pipeline')
from common import hf,snapshot_files,PY
import effects as EF
project,out=sys.argv[1],sys.argv[2]; os.makedirs(out,exist_ok=True)
rows=[(n,c) for n,c in EF.table_rows(ENG+'/fx/LIBRARY.md')]
base=open(project+'/edit.py').read()
def one(item):
    name,cells=item
    layer=re.sub(r'[^a-z]','',cells[1].split('+')[0].split()[0]) if len(cells)>1 else 'top'
    if layer not in('behind','cam','top','over'): layer='top'
    sb=f'{project}/work/smokefx/{name}'; pub=sb+'/public'; ppub=project+'/public'
    shutil.rmtree(sb,ignore_errors=True); os.makedirs(pub); os.makedirs(sb+'/fx')
    for f in('words.json','timeline.json'): shutil.copy(project+'/'+f,sb+'/'+f)
    for d in('assets','audio','style','cards'):
        if os.path.exists(project+'/'+d): os.symlink(project+'/'+d,sb+'/'+d)
    for f in os.listdir(ppub):
        if f not in('index.html','.hyperframes','assets','fx-instances.json','fx'): os.symlink(ppub+'/'+f,pub+'/'+f)
    shutil.copytree(f'{ENG}/fx/{name}',sb+'/fx/'+name)
    A,B=4.0,8.0
    head=f'\nFXLIB=[]\nTRANSITIONS=[]\nBEHIND=[]\nBOXES=[]\nAUDIO_FX=[]\nCUT_WINDOWS=[({A},{B})]\nFX=[dict(id="{name}",layer="{layer}",at={A},end={B})]\nKARAOKE=dict(hide=[])\n'
    open(sb+'/edit.py','w').write(base+head)
    try:
        subprocess.run([PY,ENG+'/pipeline/build.py',sb,'--stills'],check=True,capture_output=True,text=True)
        r=hf(['snapshot','--at','5.5','--no-end','--describe','false'],pub)
        fs=snapshot_files(pub,r.stdout+r.stderr)
        subprocess.run(['ffmpeg','-v','error','-y','-i',fs[0],'-vf','scale=270:480','-q:v','4',f'{out}/{name}.jpg'],check=True)
        res=(name,True,'')
    except subprocess.CalledProcessError as ex: res=(name,False,((ex.stderr or '')+(ex.stdout or ''))[-300:])
    except SystemExit as ex: res=(name,False,str(ex)[-300:])
    shutil.rmtree(sb,ignore_errors=True); print(res[0],res[1],res[2][:160],flush=True); return res
with cf.ThreadPoolExecutor(3) as ex: R=list(ex.map(one,rows))
print(sum(r[1] for r in R),'/',len(R))
