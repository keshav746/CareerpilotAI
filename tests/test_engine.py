from app import engine as e

def test_skill_extraction():assert 'python' in e.extract_skills('Python, SQL, Git')
def test_no_false_skill():assert 'java' not in e.extract_skills('JavaScript and Python')
def test_resume_score():assert e.analyze('Education Projects Skills test@example.com 20% improvement')['readiness_score']==100
def test_empty_resume():
 try:e.analyze('');assert False
 except ValueError:pass
def test_match_rank():assert e.match(['python','sql'],e.JOBS[0])['score']==50
def test_career_rank():assert e.careers(['salesforce','apex','lwc'])[0]['career']=='Salesforce Developer'
def test_roadmap():assert len(e.roadmap('AI Engineer',['python'])['milestones'])==3
def test_retrieve():assert any('Data Analyst' in x['title'] for x in e.retrieve('SQL data analyst dashboards'))
def test_agent_trace():assert len(e.execute('Find jobs',{'skills':['python','sql']})['trace'])>=8
def test_no_external_application():assert 'approval' in e.execute('apply',{'skills':[]})['trace'][-1]['tool']
def test_interview():assert 'feedback' in e.interview_feedback('I built an API')
def test_job_labels():assert all(j['source']=='sample' for j in e.JOBS)
