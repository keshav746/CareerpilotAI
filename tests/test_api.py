from fastapi.testclient import TestClient
from app.main import app
from uuid import uuid4
client=TestClient(app)
def test_health():assert client.get('/api/health').json()['status']=='ok'
def test_auth_required():assert client.get('/api/profile').status_code==401
def test_recruiter_forbidden_for_student():
 email=f'test_{uuid4().hex}@example.org'
 r=client.post('/api/register',json={'email':email,'password':'safePassword123','name':'Student','role':'student'});assert r.status_code==200
 headers={'Authorization':'Bearer '+r.json()['token']}
 assert client.post('/api/recruiter/jobs',headers=headers,json={'title':'X','company':'Y','location':'Z','skills':['python'],'description':'test'}).status_code==403
 assert client.post('/api/apply/approval',headers=headers,json={'job_id':1,'approved':True}).json()['submitted'] is False
