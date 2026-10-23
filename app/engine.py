import re, math, json, os, sqlite3, hashlib, secrets, hmac, datetime, urllib.request
from pathlib import Path
from collections import Counter
BASE=Path(__file__).parent
DB=BASE/'careerpilot.db'
SKILLS=['python','java','javascript','typescript','react','node.js','sql','postgresql','mongodb','fastapi','django','flask','machine learning','deep learning','tensorflow','pytorch','scikit-learn','data analysis','power bi','excel','tableau','aws','azure','docker','kubernetes','git','linux','html','css','rest api','salesforce','apex','lwc','cybersecurity','networking','communication','problem solving','nlp','rag','langchain','langgraph','statistics','pandas','numpy']
JOBS=[
 {'id':1,'title':'Junior Python Developer','company':'Northstar Labs (sample)','location':'Pune','type':'Internship','salary':'Not specified','skills':['python','sql','git','fastapi'],'description':'Build REST APIs and database-backed Python applications.','url':'','source':'sample'},
 {'id':2,'title':'Frontend React Intern','company':'Pixelworks (sample)','location':'Remote','type':'Internship','salary':'Not specified','skills':['javascript','react','html','css','git'],'description':'Build responsive user interfaces and collaborate with designers.','url':'','source':'sample'},
 {'id':3,'title':'Data Analyst Trainee','company':'InsightWorks (sample)','location':'Bengaluru','type':'Entry level','salary':'Not specified','skills':['python','sql','excel','power bi','statistics'],'description':'Analyze data and create stakeholder dashboards.','url':'','source':'sample'},
 {'id':4,'title':'AI/ML Engineer Intern','company':'VectorAI (sample)','location':'Hyderabad','type':'Internship','salary':'Not specified','skills':['python','machine learning','pandas','numpy','scikit-learn'],'description':'Prototype and evaluate machine learning models.','url':'','source':'sample'},
 {'id':5,'title':'Salesforce Developer Trainee','company':'CloudBridge (sample)','location':'Pune','type':'Entry level','salary':'Not specified','skills':['salesforce','apex','lwc','javascript','sql'],'description':'Build Salesforce automations and Lightning components.','url':'','source':'sample'},
 {'id':6,'title':'Cloud Support Associate','company':'InfraCloud (sample)','location':'Mumbai','type':'Entry level','salary':'Not specified','skills':['aws','linux','docker','networking'],'description':'Support cloud deployments and troubleshoot services.','url':'','source':'sample'}]
CAREERS={'AI Engineer':['python','machine learning','pandas','numpy','scikit-learn','docker'],'Full Stack Developer':['javascript','react','node.js','sql','git'],'Data Analyst':['python','sql','excel','power bi','statistics'],'Salesforce Developer':['salesforce','apex','lwc','javascript'],'Cloud Engineer':['aws','linux','docker','networking'],'Cybersecurity Analyst':['cybersecurity','linux','networking','python']}
DOCS=[{'title':'Career guide: Data Analyst','text':'A data analyst typically works with SQL, spreadsheets, statistics, dashboards, and Python. Build portfolio projects that clean, analyze, and visualize real datasets.'},{'title':'Career guide: AI Engineer','text':'AI engineering uses Python, machine learning, data processing, model evaluation, and deployment. Study statistics, scikit-learn, and reproducible experiments.'},{'title':'Resume writing guidance','text':'Write concise evidence-based bullet points with actions and measurable results. Include projects, education, relevant skills, and links. Never invent qualifications.'},{'title':'Interview preparation','text':'Prepare to explain project architecture, technical decisions, debugging steps, tradeoffs, and teamwork. Practice structured behavioral answers.'},{'title':'Career guide: Full Stack','text':'Full stack developers use HTML, CSS, JavaScript, React, backend APIs, SQL, Git, and testing. Build end-to-end portfolio applications.'}]
def db():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def init():
 with db() as c:
  c.executescript("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE,name TEXT,role TEXT,password TEXT,salt TEXT,created TEXT);CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER);CREATE TABLE IF NOT EXISTS profiles(user_id INTEGER PRIMARY KEY,education TEXT,skills TEXT,goal TEXT,location TEXT,resume TEXT);CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY,user_id INTEGER,job_id INTEGER,status TEXT,notes TEXT,created TEXT);CREATE TABLE IF NOT EXISTS interviews(id INTEGER PRIMARY KEY,user_id INTEGER,role TEXT,question TEXT,answer TEXT,feedback TEXT);CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,user_id INTEGER,action TEXT,details TEXT,created TEXT);CREATE TABLE IF NOT EXISTS listings(id INTEGER PRIMARY KEY,title TEXT,company TEXT,location TEXT,skills TEXT,description TEXT,created_by INTEGER);CREATE TABLE IF NOT EXISTS interview_sessions(id INTEGER PRIMARY KEY,user_id INTEGER,role TEXT,created TEXT,completed INTEGER DEFAULT 0);CREATE TABLE IF NOT EXISTS interview_answers(id INTEGER PRIMARY KEY,session_id INTEGER,question_index INTEGER,question TEXT,answer TEXT,feedback TEXT,score INTEGER);""")
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def audit(uid,action,details=''):
 with db() as c:c.execute('INSERT INTO audit(user_id,action,details,created) VALUES(?,?,?,?)',(uid,action,str(details)[:400],stamp()))
def hashpw(p,s):return hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(s),260000).hex()
def register(email,password,name,role='student'):
 if role not in ('student','recruiter'):raise ValueError('Invalid registration role')
 if len(password)<8:raise ValueError('Password must be at least 8 characters')
 salt=secrets.token_hex(16)
 with db() as c:
  try:
   cur=c.execute('INSERT INTO users(email,name,role,password,salt,created) VALUES(?,?,?,?,?,?)',(email.lower().strip(),name.strip(),role,hashpw(password,salt),salt,stamp()));uid=cur.lastrowid
  except sqlite3.IntegrityError:raise ValueError('Email already registered')
 audit(uid,'register');return login(email,password)
def login(email,password):
 with db() as c:
  u=c.execute('SELECT * FROM users WHERE email=?',(email.lower().strip(),)).fetchone()
  if not u or not hmac.compare_digest(u['password'],hashpw(password,u['salt'])):raise ValueError('Invalid credentials')
  t=secrets.token_urlsafe(32);c.execute('INSERT INTO sessions VALUES(?,?)',(t,u['id']))
 return {'token':t,'user':{'id':u['id'],'name':u['name'],'email':u['email'],'role':u['role']}}
def user(token):
 with db() as c:r=c.execute('SELECT u.id,u.name,u.email,u.role FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token=?',(token,)).fetchone()
 return dict(r) if r else None
def extract_skills(text):
 low=text.lower();return [s for s in SKILLS if re.search(r'(?<![a-z0-9])'+re.escape(s)+r'(?![a-z0-9])',low)]
def tokens(text):return re.findall(r'[a-z][a-z0-9+#.-]*',text.lower())
def cosine(a,b):
 aa=Counter(tokens(a));bb=Counter(tokens(b));dot=sum(v*bb.get(k,0) for k,v in aa.items());den=math.sqrt(sum(v*v for v in aa.values())*sum(v*v for v in bb.values()));return dot/den if den else 0

def match(skills,job):
 have=set(s.lower() for s in skills);need=set(job['skills']);matched=sorted(have&need);missing=sorted(need-have)
 score=round(100*len(matched)/len(need)) if need else 0
 return {**job,'score':score,'matched':matched,'missing':missing,'explanation':f'{len(matched)} of {len(need)} listed skills match; this is a skills-overlap score, not a hiring probability.'}
def rank(skills,jobs=None):return sorted([match(skills,j) for j in (jobs or all_jobs())],key=lambda x:x['score'],reverse=True)
def all_jobs():
 jobs=[dict(x) for x in JOBS]
 with db() as c:
  for r in c.execute('SELECT * FROM listings').fetchall():
   d=dict(r);jobs.append({'id':100000+d['id'],'title':d['title'],'company':d['company'],'location':d['location'],'type':'Recruiter listing','salary':'Not specified','skills':json.loads(d['skills']),'description':d['description'],'url':'','source':'recruiter'})
 return jobs
def careers(skills):
 have=set(skills);out=[]
 for name,needed in CAREERS.items():
  matched=sorted(have&set(needed));missing=sorted(set(needed)-have)
  out.append({'career':name,'score':round(100*len(matched)/len(needed)),'matched':matched,'missing':missing})
 return sorted(out,key=lambda x:x['score'],reverse=True)
def retrieve(question,k=3):
 scored=[(cosine(question,d['text']+' '+d['title']),d) for d in DOCS]
 return [{**d,'relevance':round(s,3)} for s,d in sorted(scored,key=lambda z:z[0],reverse=True)[:k] if s>0]
def roadmap(role,skills):
 req=CAREERS.get(role,CAREERS['AI Engineer']);missing=[s for s in req if s not in skills]
 return {'role':role,'missing':missing,'milestones':[{'period':'Days 1–30','tasks':missing[:2] or ['Strengthen fundamentals'],'deliverable':'Study notes and exercises'},{'period':'Days 31–60','tasks':missing[2:4] or ['Build an intermediate project'],'deliverable':'Portfolio project'},{'period':'Days 61–90','tasks':missing[4:] or ['Practice interviews and apply'],'deliverable':'Project documentation and interview preparation'}]}
def analyze(text):
 if not text.strip():raise ValueError('Resume contains no readable text')
 skills=extract_skills(text);low=text.lower();sections={k:bool(re.search(k,low)) for k in ['education','experience','projects','skills','certifications']}
 checks={'contact_email':bool(re.search(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}',text,re.I)),'has_projects':sections['projects'],'has_education':sections['education'],'has_skills':sections['skills'],'has_measurable_results':bool(re.search(r'\b\d+%|\b\d+ (users|projects|requests|hours)\b',low))}
 score=round(100*sum(checks.values())/len(checks));return {'skills':skills,'sections':sections,'checks':checks,'readiness_score':score,'score_note':'Heuristic document completeness score, not a validated ATS or employer acceptance score.','suggestions':[k.replace('_',' ').capitalize() for k,v in checks.items() if not v]}
def interview_question(role):return f'Describe a project relevant to {role}. Explain its architecture, a challenge you faced, and how you measured success.'
def interview_questions(role):
 role=role.strip()[:100] or 'Software Developer'
 technical={
  'ai': 'How would you prepare a dataset, train a model, and evaluate whether it generalizes?',
  'data': 'How would you clean missing values and explain the insights from a dataset?',
  'python': 'How do Python functions, exceptions, and data structures help you write maintainable code?',
  'java': 'Explain object-oriented design and how you would use interfaces in a real project.',
  'frontend': 'How would you make a web interface responsive, accessible, and performant?',
  'full stack': 'How would you design a frontend, REST API, and database for an application?',
  'salesforce': 'When would you use a Flow versus Apex in Salesforce?',
  'cloud': 'How would you deploy and monitor an application in the cloud?',
  'cyber': 'How would you investigate a suspicious login and reduce the security risk?'
 }
 role_lower=role.lower()
 tech=next((question for key,question in technical.items() if key in role_lower),f'Which technical concepts and tools are most important for a {role}, and how have you applied them?')
 return [
  f'Introduce yourself and explain why you want to work as a {role}.',
  tech,
  f'Describe a project relevant to {role}. Explain its architecture, your contribution, and the outcome.',
  f'Imagine you encounter a critical problem while working as a {role}. How would you investigate and solve it?',
  'Describe a time you handled a disagreement, setback, or deadline. What did you do and what did you learn?'
 ]
def interview_feedback(answer,question='',index=0):
 words=len(tokens(answer));lower=answer.lower()
 structure=any(x in lower for x in ['first','then','finally','because','therefore','result','learned'])
 examples=any(x in lower for x in ['project','example','built','implemented','team','used','developed'])
 measurable=bool(re.search(r'\b\d+(?:%|\s*(?:users|hours|days|weeks|requests|projects))\b',lower))
 score=min(100,20+min(words,80)*0.6+(15 if structure else 0)+(10 if examples else 0)+(7 if measurable else 0))
 score=round(score)
 notes=[]
 if words<35:notes.append('Add more detail (aim for at least 35 words)')
 if not structure:notes.append('Organize your answer into clear steps and explain your reasoning')
 if not examples:notes.append('Include a specific example or your own contribution')
 if index==2 and not measurable:notes.append('Explain the project outcome with evidence where possible')
 if not notes:notes.append('Good structure and supporting detail; keep practicing clarity and relevance')
 return {'word_count':words,'score':score,'feedback':'. '.join(notes)+'.','note':'Rule-based coaching score, not a hiring decision.'}
def execute(goal,profile):
 goal=goal[:1000];skills=profile.get('skills',[]);trace=[]
 def step(agent,tool,result):trace.append({'agent':agent,'tool':tool,'status':'completed','result':result})
 step('Planner','intent_router','Plan: assess profile → discover jobs → rank matches → identify gaps → retrieve knowledge → propose roadmap')
 step('Resume Intelligence','profile_skill_extractor',f'{len(skills)} skills available')
 jobs=rank(skills);step('Job Discovery','job_catalog',f'{len(jobs)} sample/recruiter listings checked')
 step('Job Matching','skill_overlap_ranker',f'Top score: {jobs[0]["score"] if jobs else 0}%')
 top=careers(skills);step('Career Advisor','career_ranker',top[0]['career'] if top else 'No career')
 path=roadmap(top[0]['career'],skills) if top else {}
 step('Skill Development','roadmap_builder',f'{len(path.get("missing",[]))} gaps identified')
 sources=retrieve(goal+' '+(top[0]['career'] if top else ''))
 step('Market Research','rag_retriever',f'{len(sources)} source passages retrieved')
 step('Interview Coach','question_generator','Prepared practice question')
 step('Application Manager','approval_gate','External applications require user approval; no submissions made')
 return {'mode':'deterministic multi-tool agent workflow','plan':trace[0]['result'],'trace':trace,'jobs':jobs[:4],'careers':top[:3],'roadmap':path,'sources':sources,'interview_question':interview_question(top[0]['career'] if top else 'developer'),'notice':'Job catalog includes explicitly labeled sample listings. No live job availability is claimed.'}