import io,json,os
from pathlib import Path
from fastapi import FastAPI,HTTPException,Request,UploadFile,File,Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from . import engine as e
from . import llm_service as ai
app=FastAPI(title='CareerPilot AI',version='1.0.0',description='Career intelligence educational prototype with five-question mock interviews')
e.init()
app.mount('/static',StaticFiles(directory=Path(__file__).parent/'static'),name='static')
class Credentials(BaseModel):
 email:str;password:str;name:str='';role:str='student'
class Profile(BaseModel):
 education:str='';skills:list[str]=[];goal:str='AI Engineer';location:str='';resume:str=''
class Query(BaseModel):
 text:str=Field(min_length=1,max_length=10000)
class Application(BaseModel):
 job_id:int;status:str='Saved';notes:str=''
class Interview(BaseModel):
 role:str
 answer:str
 session_id:int
 question_index:int
class Listing(BaseModel):title:str;company:str;location:str;skills:list[str];description:str
class Approval(BaseModel):job_id:int;approved:bool=False

def auth(request:Request):
 t=request.headers.get('authorization','').removeprefix('Bearer ').strip();u=e.user(t)
 if not u:raise HTTPException(401,'Login required')
 return u

def student(u=Depends(auth)):
 if u['role'] != 'student':raise HTTPException(403,'Student account required')
 return u

def recruiter_user(u=Depends(auth)):
 if u['role'] != 'recruiter':raise HTTPException(403,'Recruiter account required')
 return u
@app.get('/')
def index():return FileResponse(Path(__file__).parent/'static'/'index.html')
@app.post('/api/register')
def register(x:Credentials):
 try:return e.register(x.email,x.password,x.name,x.role)
 except ValueError as ex:raise HTTPException(400,str(ex))
@app.post('/api/login')
def login(x:Credentials):
 try:return e.login(x.email,x.password)
 except ValueError as ex:raise HTTPException(401,str(ex))
@app.get('/api/me')
def me(u=Depends(auth)):return u
@app.get('/api/profile')
def profile(u=Depends(student)):
 with e.db() as c:r=c.execute('SELECT * FROM profiles WHERE user_id=?',(u['id'],)).fetchone()
 return {'education':r['education'],'skills':json.loads(r['skills']),'goal':r['goal'],'location':r['location'],'resume':r['resume']} if r else {'education':'','skills':[],'goal':'AI Engineer','location':'','resume':''}
@app.post('/api/profile')
def save_profile(x:Profile,u=Depends(student)):
 with e.db() as c:c.execute('INSERT OR REPLACE INTO profiles VALUES(?,?,?,?,?,?)',(u['id'],x.education,json.dumps(x.skills),x.goal,x.location,x.resume))
 e.audit(u['id'],'profile_update');return {'ok':True}
@app.post('/api/resume/analyze')
def resume(x:Query,u=Depends(student)):
 try:r=e.analyze(x.text)
 except ValueError as ex:raise HTTPException(400,str(ex))
 e.audit(u['id'],'resume_analyze');return r
@app.post('/api/resume/upload')
async def upload(file:UploadFile=File(...),u=Depends(student)):
 raw=await file.read(3_000_001)
 if len(raw)>3_000_000:raise HTTPException(413,'Maximum file size 3 MB')
 ext=Path(file.filename or '').suffix.lower()
 try:
  if ext=='.pdf':
   from pypdf import PdfReader
   text='\n'.join(page.extract_text() or '' for page in PdfReader(io.BytesIO(raw)).pages[:15])
  elif ext=='.docx':
   from docx import Document
   text='\n'.join(p.text for p in Document(io.BytesIO(raw)).paragraphs)
  elif ext=='.txt':text=raw.decode('utf-8')
  else:raise HTTPException(415,'Only PDF, DOCX, TXT supported')
  return {'text':text[:30000],**e.analyze(text[:30000])}
 except HTTPException:raise
 except Exception:raise HTTPException(422,'Could not read document')
@app.get('/api/jobs')
def jobs(q:str='',location:str='',u=Depends(student)):
 items=e.all_jobs();return [j for j in items if (not q or q.lower() in (j['title']+' '+j['description']).lower()) and (not location or location.lower() in j['location'].lower())]
@app.get('/api/matches')
def matches(u=Depends(student)):
 p=profile(u);return e.rank(p['skills'])
@app.get('/api/careers')
def careers(u=Depends(student)):return e.careers(profile(u)['skills'])
@app.get('/api/roadmap')
def roadmap(role:str='',u=Depends(student)):
 p=profile(u);return e.roadmap(role or p['goal'],p['skills'])
@app.post('/api/rag')
def rag(x:Query,u=Depends(student)):
 sources=e.retrieve(x.text);return {'answer':'Based on the retrieved knowledge: '+' '.join(s['text'] for s in sources) if sources else 'No sufficiently relevant document found.','sources':sources,'grounded':bool(sources)}
@app.post('/api/agent/run')
def run(x:Query,u=Depends(student)):
 result=e.execute(x.text,profile(u));e.audit(u['id'],'agent_run',x.text[:120]);return result
@app.get('/api/ai/status')
def ai_status(u=Depends(student)):
 try:
  _,_,model,embedding=ai.config()
  return {'configured':True,'model':model,'embedding_model':embedding,'note':'Credentials configured; use AI features to verify provider connectivity.'}
 except ValueError as ex:
  return {'configured':False,'note':str(ex)}

@app.post('/api/ai/rag')
def ai_rag(x:Query,u=Depends(student)):
 try:
  result=ai.answer(x.text)
  e.audit(u['id'],'llm_rag',x.text[:100])
  return result
 except ValueError as ex:raise HTTPException(503,str(ex))
 except RuntimeError as ex:raise HTTPException(502,str(ex))

@app.post('/api/ai/agent/run')
def ai_agent_run(x:Query,u=Depends(student)):
 try:
  result=ai.run_agent(x.text,profile(u))
  e.audit(u['id'],'llm_agent',x.text[:100])
  return result
 except ValueError as ex:raise HTTPException(503,str(ex))
 except RuntimeError as ex:raise HTTPException(502,str(ex))

@app.post('/api/interview/start')
def interview_start(x:Query,u=Depends(student)):
 role=x.text.strip()[:100]
 if not role:raise HTTPException(400,'Interview role required')
 questions=e.interview_questions(role)
 with e.db() as c:
  cur=c.execute('INSERT INTO interview_sessions(user_id,role,created,completed) VALUES(?,?,?,0)',(u['id'],role,e.stamp()))
  sid=cur.lastrowid
 return {'session_id':sid,'role':role,'total':len(questions),'question_index':0,'question':questions[0]}

@app.post('/api/interview')
def interview(x:Interview,u=Depends(student)):
 with e.db() as c:
  session=c.execute('SELECT * FROM interview_sessions WHERE id=? AND user_id=?',(x.session_id,u['id'])).fetchone()
  if not session:raise HTTPException(404,'Interview session not found')
  if session['completed']:raise HTTPException(409,'Interview already completed')
  questions=e.interview_questions(session['role'])
  idx=c.execute('SELECT COUNT(*) FROM interview_answers WHERE session_id=?',(x.session_id,)).fetchone()[0]
  if x.question_index!=idx:raise HTTPException(409,'Question already answered or incorrect sequence')
  if not x.answer.strip():raise HTTPException(400,'Please enter an answer')
  result=e.interview_feedback(x.answer,questions[idx],idx)
  c.execute('INSERT INTO interview_answers(session_id,question_index,question,answer,feedback,score) VALUES(?,?,?,?,?,?)',
   (x.session_id,idx,questions[idx],x.answer,result['feedback'],result['score']))
  c.execute('INSERT INTO interviews(user_id,role,question,answer,feedback) VALUES(?,?,?,?,?)',
   (u['id'],session['role'],questions[idx],x.answer,result['feedback']))
  completed=idx+1==len(questions)
  if completed:
   c.execute('UPDATE interview_sessions SET completed=1 WHERE id=?',(x.session_id,))
   answers=[dict(row) for row in c.execute('SELECT question_index,question,answer,feedback,score FROM interview_answers WHERE session_id=? ORDER BY question_index',(x.session_id,))]
   avg=round(sum(a['score'] for a in answers)/len(answers))
   return {'completed':True,'feedback':result['feedback'],'score':result['score'],'word_count':result['word_count'],
    'summary':{'role':session['role'],'overall_score':avg,'total_questions':len(answers),'answers':answers,
    'note':'Rule-based practice score, not a hiring prediction or LLM evaluation.'}}
  return {'completed':False,'feedback':result['feedback'],'score':result['score'],'word_count':result['word_count'],
   'question_index':idx+1,'question':questions[idx+1],'total':len(questions)}

@app.get('/api/interviews')
def interviews(u=Depends(student)):
 with e.db() as c:return [dict(r) for r in c.execute('SELECT * FROM interviews WHERE user_id=? ORDER BY id DESC',(u['id'],))]
@app.get('/api/applications')
def applications(u=Depends(student)):
 with e.db() as c:return [dict(r) for r in c.execute('SELECT * FROM applications WHERE user_id=? ORDER BY id DESC',(u['id'],))]
@app.post('/api/applications')
def add_app(x:Application,u=Depends(student)):
 if x.status not in ['Saved','Applied','Assessment','Interview','Offer','Rejected']:raise HTTPException(400,'Invalid status')
 if x.job_id not in [j['id'] for j in e.all_jobs()]:raise HTTPException(404,'Job not found')
 with e.db() as c:c.execute('INSERT INTO applications(user_id,job_id,status,notes,created) VALUES(?,?,?,?,?)',(u['id'],x.job_id,x.status,x.notes,e.stamp()))
 return {'ok':True,'notice':'Internal tracking only; no external application was submitted.'}
@app.get('/api/market')
def market(u=Depends(student)):
 from collections import Counter
 j=e.all_jobs();return {'skills':Counter(s for x in j for s in x['skills']).most_common(12),'locations':Counter(x['location'] for x in j).most_common(),'sample_size':len(j),'disclaimer':'Demo/recruiter listings only; not representative of the overall job market.'}
@app.post('/api/recruiter/jobs')
def recruiter(x:Listing,u=Depends(recruiter_user)):
 if u['role']!='recruiter':raise HTTPException(403,'Recruiter only')
 with e.db() as c:c.execute('INSERT INTO listings(title,company,location,skills,description,created_by) VALUES(?,?,?,?,?,?)',(x.title,x.company,x.location,json.dumps(x.skills),x.description,u['id']))
 e.audit(u['id'],'job_post');return {'ok':True}
@app.get('/api/admin/audit')
def admin(u=Depends(auth)):
 if u['role']!='admin':raise HTTPException(403,'Admin only')
 with e.db() as c:return [dict(r) for r in c.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 100')]
@app.post('/api/apply/approval')
def approve(x:Approval,u=Depends(student)):
 e.audit(u['id'],'application_approval',f'job={x.job_id},approved={x.approved}')
 return {'approved':x.approved,'submitted':False,'notice':'This prototype never submits external job applications.'}
@app.get('/api/health')
def health():return {'status':'ok','version':'1.0.0'}