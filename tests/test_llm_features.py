import json
import pytest
from app import llm_service as ai

def test_prompt_versions_and_security():
 assert all(x in ai.PROMPTS for x in ('planner_v2','rag_v2','synthesis_v2'))
 assert 'untrusted' in ai.PROMPTS['rag_v2'].lower()

def test_no_fake_llm_without_key(monkeypatch):
 monkeypatch.setenv('LLM_API_KEY','')
 with pytest.raises(ValueError,match='LLM_API_KEY'): ai.config()

def test_real_embedding_retrieval_with_mock_provider(monkeypatch):
 monkeypatch.setattr(ai,'knowledge',lambda:[{'id':'a','title':'Python','text':'Python skills for backend'},{'id':'b','title':'Data','text':'SQL analytics and charts'}])
 monkeypatch.setattr(ai,'embeddings',lambda inputs:[[1.,0.],[1.,0.],[0.,1.]])
 assert ai.semantic_retrieve('python')[0]['id']=='a'

def test_grounded_answer_uses_retrieved_sources(monkeypatch):
 monkeypatch.setattr(ai,'semantic_retrieve',lambda q:[{'id':'doc#1','title':'Guide','text':'Python and SQL are useful.','relevance':0.92}])
 monkeypatch.setattr(ai,'chat',lambda system,user:'Learn Python and SQL [1].')
 result=ai.answer('What should I learn?')
 assert result['grounded'] and '[1]' in result['answer']
 assert result['prompt_version']=='rag_v2'

def test_llm_plan_rejects_unapproved_tools(monkeypatch):
 monkeypatch.setattr(ai,'chat',lambda system,user:'{"tools":["delete_database"]}')
 with pytest.raises(RuntimeError,match='allowed tool plan'):ai.plan('do anything')

def test_llm_plan_selects_real_tools(monkeypatch):
 monkeypatch.setattr(ai,'chat',lambda system,user:'{"tools":["career_matches","skill_roadmap"],"reason":"Find fit"}')
 assert ai.plan('help me')['tools']==['career_matches','skill_roadmap']
