"""Zero-dependency Python web API/server for the Gold Purity Estimation project.
Runs locally and on Render. The frontend is also served locally from ../frontend.
"""
import json, mimetypes, os, sys, traceback
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import config
from src.predict import MLModel, PredictionHistory, run_prediction
from src.evaluation import load_metrics
from src.project_assistant import ProjectAssistant
from src.report_generator import generate_pdf_report
from src.all_models import predict_all

model = None
assistant = None

def get_model():
    global model
    if model is None:
        model = MLModel.load()
    return model

def get_assistant():
    global assistant
    if assistant is None:
        assistant = ProjectAssistant(model=get_model())
    return assistant

def json_bytes(obj):
    return json.dumps(obj, ensure_ascii=False, default=str).encode('utf-8')

def response(start, status='200 OK', data=b'', content_type='application/json; charset=utf-8', headers=None):
    h=[('Content-Type',content_type),('Cache-Control','no-store'),('Access-Control-Allow-Origin','*'),('Access-Control-Allow-Methods','GET,POST,OPTIONS'),('Access-Control-Allow-Headers','Content-Type')]
    if headers: h.extend(headers)
    start(status,h); return [data]

def api(start, status='200 OK', obj=None): return response(start,status,json_bytes(obj if obj is not None else {}))

def read_json(environ):
    try:
        n=int(environ.get('CONTENT_LENGTH') or 0)
        raw=environ['wsgi.input'].read(n) if n else b'{}'
        return json.loads(raw.decode('utf-8') or '{}')
    except Exception:
        raise ValueError('Request body must be valid JSON.')

def feature_info():
    return {k:{'label':v.label,'unit':v.unit,'minimum':v.minimum,'maximum':v.maximum,'positive':v.must_be_positive} for k,v in config.FIELD_RULES.items()}

def prediction_payload(p):
    return {'timestamp':p.timestamp.isoformat(),'inputs':p.sample.to_dict(),'predicted_purity':round(p.predicted_purity,4),'model_name':p.model_name,'reference_purity':p.reference_purity,'difference':None if p.difference is None else round(p.difference,4),'warnings':p.warnings}

def handle(environ,start):
    method=environ.get('REQUEST_METHOD','GET'); path=urlparse(environ.get('PATH_INFO','/')).path
    if method=='OPTIONS': return response(start,'204 No Content',b'')
    try:
        if path=='/api/health': return api(start,obj={'ok':True,'service':'Gold Purity Estimation API'})
        if path=='/api/meta':
            metrics=load_metrics();
            try:
                import pandas as pd
                metrics['dataset_rows']=int(len(pd.read_csv(config.DATASET_PATH)))
            except Exception:
                metrics['dataset_rows']=metrics.get('records_loaded',0)
            return api(start,obj={'title':config.APP_TITLE,'subtitle':config.APP_SUBTITLE,'features':feature_info(),'metrics':metrics,'dataset_label':config.DATASET_LABEL,'disclaimer':config.DISCLAIMER})
        if path=='/api/predict' and method=='POST':
            body=read_json(environ)
            p=run_prediction(body.get('inputs',{}),body.get('reference_purity'),model=get_model())
            PredictionHistory().save(p)
            payload=prediction_payload(p)
            payload['all_model_predictions']=predict_all(body.get('inputs',{}))
            return api(start,obj=payload)
        if path=='/api/sample':
            from src.predict import get_random_test_sample
            inputs,ref=get_random_test_sample(); return api(start,obj={'inputs':inputs,'reference_purity':ref})
        if path=='/api/history':
            df=PredictionHistory().load(); rows=df.fillna('').to_dict(orient='records')
            return api(start,obj={'rows':rows,'count':len(rows)})
        if path=='/api/dataset':
            import pandas as pd
            df=pd.read_csv(config.DATASET_PATH)
            return api(start,obj={'rows':len(df),'columns':list(df.columns),'purity':{'min':float(df.purity.min()),'max':float(df.purity.max()),'mean':float(df.purity.mean())},'preview':df.fillna('').to_dict(orient='records')})
        if path=='/api/insights':
            import pandas as pd
            df=pd.read_csv(config.DATASET_PATH)
            correlations=[]
            for col in config.FEATURE_COLUMNS:
                correlations.append({'feature':col,'label':config.FIELD_RULES[col].label,'correlation':float(df[col].corr(df[config.TARGET_COLUMN]))})
            correlations.sort(key=lambda x:abs(x['correlation']),reverse=True)
            return api(start,obj={'correlations':correlations})
        if path=='/api/compare' and method=='POST':
            body=read_json(environ)
            a=run_prediction(body.get('sample_a',{}), body.get('reference_a'), model=get_model())
            b=run_prediction(body.get('sample_b',{}), body.get('reference_b'), model=get_model())
            return api(start,obj={'a':dict(prediction_payload(a),all_model_predictions=predict_all(body.get('sample_a',{}))), 'b':dict(prediction_payload(b),all_model_predictions=predict_all(body.get('sample_b',{})))})
        if path=='/api/graphs':
            names=[]
            for label,fn in __import__('src.visualization',fromlist=['GRAPH_FILES']).GRAPH_FILES.items():
                if (config.GRAPHS_DIR/fn).exists(): names.append({'label':label,'file':fn})
            return api(start,obj={'graphs':names})
        if path=='/api/reports':
            files=[]
            for p in sorted(config.REPORTS_DIR.glob('*.pdf'),reverse=True): files.append({'name':p.name,'size':p.stat().st_size,'url':'/reports/'+p.name})
            return api(start,obj={'reports':files})
        if path=='/api/report' and method=='POST':
            body=read_json(environ); p=run_prediction(body.get('inputs',{}),body.get('reference_purity'),model=get_model()); out=generate_pdf_report(p,load_metrics()); return api(start,obj={'name':out.name,'url':'/reports/'+out.name})
        if path=='/api/assistant' and method=='POST':
            body=read_json(environ); q=str(body.get('question','')); language=str(body.get('language','en')); return api(start,obj={'answer':get_assistant().answer(q, language=language)})
        if path.startswith('/graphs/'):
            fn=unquote(path[len('/graphs/'):]); p=(config.GRAPHS_DIR/fn).resolve()
            if p.parent!=config.GRAPHS_DIR.resolve() or not p.exists(): return response(start,'404 Not Found',b'Not found', 'text/plain')
            return response(start,data=p.read_bytes(),content_type=mimetypes.guess_type(str(p))[0] or 'application/octet-stream')
        if path.startswith('/reports/'):
            fn=unquote(path[len('/reports/'):]); p=(config.REPORTS_DIR/fn).resolve()
            if p.parent!=config.REPORTS_DIR.resolve() or not p.exists(): return response(start,'404 Not Found',b'Not found', 'text/plain')
            return response(start,data=p.read_bytes(),content_type='application/pdf',headers=[('Content-Disposition',f'inline; filename="{p.name}"')])
        # Local static frontend; Vercel serves the same files independently.
        rel='index.html' if path in ('','/') else path.lstrip('/')
        fp=(ROOT/'frontend'/rel).resolve()
        if fp.exists() and fp.is_file() and (ROOT/'frontend') in fp.parents:
            return response(start,data=fp.read_bytes(),content_type=mimetypes.guess_type(str(fp))[0] or 'text/plain')
        return response(start,'404 Not Found',json_bytes({'error':'Not found'}))
    except Exception as exc:
        traceback.print_exc()
        return api(start,'400 Bad Request' if isinstance(exc,ValueError) else '500 Internal Server Error',{'error':str(exc)})

if __name__=='__main__':
    config.ensure_directories()
    port=int(os.environ.get('PORT','8000'))
    print(f'Gold Purity web app running at http://127.0.0.1:{port}')
    make_server('0.0.0.0',port,handle,handler_class=WSGIRequestHandler).serve_forever()
