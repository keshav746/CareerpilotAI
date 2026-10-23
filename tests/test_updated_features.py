from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def account(role):
    r=client.post('/api/register',json={'email':f'{uuid4().hex}@example.org','password':'Password123','name':'Demo','role':role})
    assert r.status_code==200,r.text
    return {'Authorization':'Bearer '+r.json()['token']}
def test_removed_endpoints():
    h=account('student')
    for url in ('/api/alerts','/api/analytics','/api/prompts','/api/feedback'):
        assert client.get(url,headers=h).status_code==404

def test_recruiter_isolation():
    h=account('recruiter')
    assert client.get('/api/profile',headers=h).status_code==403
    assert client.get('/api/jobs',headers=h).status_code==403
    assert client.post('/api/interview/start',headers=h,json={'text':'AI Engineer'}).status_code==403
    assert client.post('/api/recruiter/jobs',headers=h,json={'title':'Backend Intern','company':'Demo Company','location':'Pune','skills':['python'],'description':'API work'}).status_code==200

def test_interview_five_questions_and_summary():
    h=account('student')
    r=client.post('/api/interview/start',headers=h,json={'text':'AI Engineer'})
    assert r.status_code==200,r.text
    d=r.json();sid=d['session_id'];assert d['total']==5
    for i in range(5):
        r=client.post('/api/interview',headers=h,json={'role':'AI Engineer','session_id':sid,'question_index':i,'answer':'First I built a Python project with my team. Then I tested it and documented the result. We improved the API for 100 users.'})
        assert r.status_code==200,r.text
        d=r.json()
        assert d['completed']==(i==4)
    assert len(d['summary']['answers'])==5
    assert 0<=d['summary']['overall_score']<=100
    assert client.post('/api/interview',headers=h,json={'role':'AI Engineer','session_id':sid,'question_index':4,'answer':'Again'}).status_code==409
