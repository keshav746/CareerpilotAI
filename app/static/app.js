
let token = localStorage.getItem('cp_token') || '';
let me = null;
let page = 'overview';
let isRegister = false;
let profile = { skills: [], goal: 'AI Engineer' };

const pages = [
  ['overview', '◫', 'Overview'],
  ['profile', '♙', 'Career Profile'],
  ['resume', '▤', 'Resume Intelligence'],
  ['jobs', '▣', 'Job Discovery'],
  ['careers', '◎', 'Career Recommendations'],
  ['roadmap', '↗', 'Skill Roadmap'],
  ['agent', '✦', 'Agent Workspace'],
  ['ai-agent', '✧', 'LLM Agent Planner'],
  ['rag', '▥', 'RAG Knowledge Base'],
  ['ai-rag', '✧', 'LLM + Semantic RAG'],
  ['interview', '♧', 'Interview Coach'],
  ['applications', '☷', 'Applications'],
  ['market', '◈', 'Market Intelligence'],
  ['recruiter', '▣', 'Recruiter Portal']
];

const $ = id => document.getElementById(id);

function safe(s) {
  return String(s ?? '').replace(
    /[&<>"']/g,
    c => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[c])
  );
}

function toast(t) {
  $('toast').textContent = t;
  $('toast').style.display = 'block';
  setTimeout(() => $('toast').style.display = 'none', 3500);
}

async function api(path, method = 'GET', data) {
  let opt = {
    method,
    headers: { Authorization: 'Bearer ' + token }
  };

  if (data instanceof FormData) {
    opt.body = data;
  } else if (data !== undefined) {
    opt.headers['Content-Type'] = 'application/json';
    opt.body = JSON.stringify(data);
  }

  let r = await fetch('/api' + path, opt);
  let j = await r.json();

  if (!r.ok) {
    throw Error(j.detail || 'Request failed');
  }

  return j;
}

function toggleAuth(v) {
  isRegister = v;
  $('name').style.display = v ? 'block' : 'none';
  $('role').style.display = v ? 'block' : 'none';
  $('authSubmit').textContent = v ? 'Create account' : 'Sign in';
  $('loginTab').className = v ? '' : 'selected';
  $('regTab').className = v ? 'selected' : '';
}

async function authenticate() {
  try {
    let x = await api(
      isRegister ? '/register' : '/login',
      'POST',
      {
        email: $('email').value,
        password: $('password').value,
        name: $('name').value,
        role: $('role').value
      }
    );

    token = x.token;
    localStorage.setItem('cp_token', token);
    await boot();
  } catch (e) {
    toast(e.message);
  }
}

function logout() {
  localStorage.removeItem('cp_token');
  token = '';
  $('app').classList.add('hidden');
  $('auth').classList.remove('hidden');
}

async function boot() {
  try {
    me = await api('/me');

    profile = me.role === 'recruiter'
      ? { skills: [], goal: 'AI Engineer' }
      : await api('/profile');

    $('auth').classList.add('hidden');
    $('app').classList.remove('hidden');

    $('userBadge').textContent = me.name + ' · ' + me.role;
    $('avatar').textContent = me.name.slice(0, 2).toUpperCase();

    $('nav').innerHTML = pages
      .filter(p =>
        me.role === 'recruiter'
          ? p[0] === 'recruiter'
          : p[0] !== 'recruiter'
      )
      .map(p => `
        <button id="nav-${p[0]}" onclick="navigate('${p[0]}')">
          ${p[1]} &nbsp; ${p[2]}
        </button>
      `)
      .join('');

    navigate(me.role === 'recruiter' ? 'recruiter' : 'overview');
  } catch (e) {
    logout();
  }
}

function navigate(p) {
  if (me && me.role === 'recruiter' && p !== 'recruiter') {
    p = 'recruiter';
  }

  if (me && me.role !== 'recruiter' && p === 'recruiter') {
    p = 'overview';
  }

  page = p;

  document.querySelectorAll('nav button').forEach(b => {
    b.classList.toggle('active', b.id === 'nav-' + p);
  });

  $('pageTitle').textContent =
    (pages.find(x => x[0] === p) || [])[2] || p;

  $('content').innerHTML =
    '<div class="card">Loading workspace...</div>';

  render().catch(e => {
    $('content').innerHTML =
      `<div class="notice danger">${safe(e.message)}</div>`;
  });
}

function box(t, c) {
  return `<section class="card"><h2>${t}</h2>${c}</section>`;
}

function pills(a) {
  return (a || [])
    .map(x => `<span class="pill">${safe(x)}</span>`)
    .join('');
}

function bars(a) {
  return (a || []).map(([n, v]) => `
    <div class="chartbar">
      <label>${safe(n)}</label>
      <div class="progress">
        <span style="width:${Math.min(100, Math.max(0, v))}%"></span>
      </div>
      <b>${v}%</b>
    </div>
  `).join('');
}

function jobsHtml(items, match = false) {
  return items.map(j => `
    <div class="job">
      <div class="row">
        <div>
          <h3>${safe(j.title)}</h3>
          <small>
            ${safe(j.company)} · ${safe(j.location)} ·
            ${safe(j.type)} · ${safe(j.source)}
          </small>
        </div>
        ${match ? `<div class="score">${j.score}% match</div>` : ''}
      </div>

      <p class="mini">${safe(j.description)}</p>
      <div>${pills(j.skills)}</div>

      ${match ? `
        <p class="mini good">
          Matched: ${safe(j.matched.join(', ') || 'None')}
        </p>
        <p class="mini">
          Missing: ${safe(j.missing.join(', ') || 'None')}
        </p>
      ` : ''}

      <button class="secondary" onclick="saveJob(${j.id})">
        + Save to tracker
      </button>

      ${j.url ? `
        <a href="${safe(j.url)}"
           target="_blank"
           rel="noopener noreferrer">
          Original listing ↗
        </a>
      ` : ''}
    </div>
  `).join('') || '<p>No results.</p>';
}

async function saveJob(id) {
  try {
    await api('/applications', 'POST', {
      job_id: id,
      status: 'Saved'
    });
    toast('Saved to application tracker');
  } catch (e) {
    toast(e.message);
  }
}

async function render() {
  let c = $('content');

  if (page === 'overview') {
    let [m, applications, interviews, jobs] = await Promise.all([
      api('/matches'),
      api('/applications'),
      api('/interviews'),
      api('/jobs')
    ]);

    let a = {
      profile_skills: profile.skills.length,
      jobs: jobs.length,
      applications: { total: applications.length },
      interviews: interviews.length
    };

    c.innerHTML = `
      <div class="hero">
        <div class="eyebrow" style="color:#c8dcff">
          WELCOME BACK, ${safe(me.name.toUpperCase())}
        </div>
        <h2>Your career, intelligently guided.</h2>
        <p>
          Discover opportunities, improve your resume and
          let specialized agents build your next steps.
        </p>
        <button onclick="navigate('agent')">
          Launch AI career assistant →
        </button>
      </div>

      <div class="grid">
        ${[
          ['Profile skills', a.profile_skills],
          ['Available listings', a.jobs],
          [
            'Tracked applications',
            Object.values(a.applications).reduce((x, y) => x + y, 0)
          ],
          ['Mock interviews', a.interviews]
        ].map(x => `
          <div class="card stat">
            <div class="label">${x[0]}</div>
            <div class="value">${x[1]}</div>
            <small>CareerPilot workspace</small>
          </div>
        `).join('')}
      </div>

      <div class="two">
        ${box('Recommended opportunities', jobsHtml(m.slice(0, 3), true))}
        ${box('Quick actions', `
          <div class="three" style="grid-template-columns:1fr 1fr">
            <button class="secondary" onclick="navigate('resume')">
              Analyze resume
            </button>
            <button class="secondary" onclick="navigate('jobs')">
              Explore jobs
            </button>
            <button class="secondary" onclick="navigate('roadmap')">
              Career roadmap
            </button>
            <button class="secondary" onclick="navigate('interview')">
              Mock interview
            </button>
          </div>
          <div class="notice">
            Job listings labeled “sample” are illustrative,
            not verified vacancies.
          </div>
        `)}
      </div>
    `;
  }

  if (page === 'profile') {
    c.innerHTML = box('Your professional profile', `
      <div class="form-row">
        <div class="field">
          <label>Education</label>
          <input id="edu" value="${safe(profile.education)}"
                 placeholder="B.Tech IT">
        </div>
        <div class="field">
          <label>Preferred location</label>
          <input id="loc" value="${safe(profile.location)}"
                 placeholder="Pune / Remote">
        </div>
      </div>

      <div class="field">
        <label>Technical skills (comma separated)</label>
        <textarea id="skills">${safe(profile.skills.join(', '))}</textarea>
      </div>

      <div class="field">
        <label>Target career</label>
        <select id="goal">
          ${[
            'AI Engineer',
            'Full Stack Developer',
            'Data Analyst',
            'Salesforce Developer',
            'Cloud Engineer',
            'Cybersecurity Analyst'
          ].map(x => `
            <option ${profile.goal === x ? 'selected' : ''}>
              ${x}
            </option>
          `).join('')}
        </select>
      </div>

      <button class="primary" onclick="saveProfile()">
        Save career profile
      </button>
    `);
  }

  if (page === 'resume') {
    c.innerHTML = box('Resume Intelligence', `
      <p>
        Upload a PDF, DOCX or TXT resume (max 3 MB),
        or paste its text below.
      </p>

      <div class="field">
        <label>Upload document</label>
        <input type="file" id="resumeFile"
               accept=".pdf,.docx,.txt"
               onchange="uploadResume()">
      </div>

      <div class="field">
        <label>Resume content</label>
        <textarea id="resumeText"
                  style="min-height:210px"
                  placeholder="Paste your resume content...">${safe(profile.resume || '')}</textarea>
      </div>

      <button class="primary" onclick="analyzeResume()">
        Analyze resume →
      </button>

      <div id="resumeOutput"></div>
    `);
  }

  if (page === 'jobs') {
    let j = await api('/jobs');

    c.innerHTML = box('Explore opportunities', `
      <div class="toolbar">
        <input id="jobQuery" placeholder="Search roles, keywords...">
        <input id="jobLoc" placeholder="Location">
        <button class="primary" onclick="searchJobs()">Search</button>
      </div>

      <div class="notice">
        The default catalog contains sample listings.
        Recruiter-posted listings are marked separately.
      </div>

      <div id="jobResults">${jobsHtml(j)}</div>
    `);
  }

  if (page === 'careers') {
    let r = await api('/careers');

    c.innerHTML = box('Career fit analysis', `
      <p>
        Skill overlap is used to rank career paths;
        scores are not predictions of employment outcomes.
      </p>

      ${r.map(x => `
        <div class="job">
          <div class="row">
            <h3>${safe(x.career)}</h3>
            <span class="score">${x.score}%</span>
          </div>

          <div class="progress">
            <span style="width:${x.score}%"></span>
          </div>

          <p class="mini">
            Your skills: ${safe(x.matched.join(', ') || 'No direct matches')}
          </p>
          <p class="mini">
            Suggested learning:
            ${safe(x.missing.join(', ') || 'Strengthen existing skills')}
          </p>

          <button class="secondary"
                  onclick="roadmapFor('${x.career}')">
            Build roadmap →
          </button>
        </div>
      `).join('')}
    `);
  }

  if (page === 'roadmap') {
    let r = await api('/roadmap');
    c.innerHTML = roadmapHtml(r);
  }

  if (page === 'agent') {
    c.innerHTML = box('Multi-agent career workspace', `
      <p>
        One request activates the planner and eight specialized
        tool-based agents. The execution trace shows actual
        completed steps.
      </p>

      <div class="field">
        <label>What would you like to achieve?</label>
        <textarea id="agentGoal">Analyze my profile, find matching internships and build a 90-day career roadmap.</textarea>
      </div>

      <button class="primary" onclick="runAgent()">
        ✦ Execute multi-agent plan
      </button>

      <div id="agentOutput"></div>
    `);
  }

  // LLM AGENT PLANNER
  // The blue "Configured" status message has been removed.
  if (page === 'ai-agent') {
    c.innerHTML = box('LLM-planned career workflow', `
      <p>
        This mode calls a real configured LLM to select approved
        career tools, executes them on the server, and uses the
        LLM to synthesize the results.
        No API key means no simulated output.
      </p>

      <textarea id="aiAgentGoal"
                placeholder="What career help do you need?">Analyze my current skills, suggest suitable jobs, and explain what I should learn for an AI Engineer role.</textarea>

      <br><br>

      <button class="primary" onclick="runLlmAgent()">
        Run real LLM agent →
      </button>

      <div id="aiAgentOutput"></div>
    `);
  }

  // LLM + SEMANTIC RAG
  // The blue "Configured" status message has been removed.
  if (page === 'ai-rag') {
    c.innerHTML = box('LLM-powered semantic RAG', `
      <p>
        Real embedding search across the local knowledge
        documents, followed by a grounded LLM answer with
        numbered source citations.
        Sources are maintained in app/knowledge/*.md.
      </p>

      <textarea id="aiRagQuestion"
                placeholder="Ask about a career...">What skills should I learn to become an AI Engineer?</textarea>

      <br><br>

      <button class="primary" onclick="askSemanticRag()">
        Ask with semantic RAG →
      </button>

      <div id="aiRagOutput"></div>
    `);
  }

  if (page === 'rag') {
    c.innerHTML = box('Grounded career knowledge search', `
      <p>
        Search the curated local career knowledge base.
        Results cite source titles and passages.
      </p>

      <textarea id="ragQuestion">What skills do I need to become an AI Engineer?</textarea>

      <br><br>

      <button class="primary" onclick="askRag()">
        Retrieve evidence →
      </button>

      <div id="ragOutput"></div>
    `);
  }

  if (page === 'interview') {
    c.innerHTML = box('Five-question mock interview', `
      <p>
        Practice five questions, one at a time.
        Each answer receives rule-based feedback,
        followed by an overall review.
      </p>

      <div class="field">
        <label>Interview role</label>
        <input id="interviewRole" value="${safe(profile.goal)}">
      </div>

      <button class="primary" onclick="startInterview()">
        Start 5-question interview →
      </button>

      <div id="interviewOutput"></div>
    `);
  }

  if (page === 'applications') {
    let a = await api('/applications');
    let js = await api('/jobs');

    c.innerHTML = box('Application pipeline', `
      <p>
        Track your own progress.
        Saving a listing does not submit an application.
      </p>

      <div class="grid">
        ${['Saved', 'Applied', 'Assessment', 'Interview'].map(s => `
          <div class="card stat">
            <div class="label">${s}</div>
            <div class="value">
              ${a.filter(x => x.status === s).length}
            </div>
          </div>
        `).join('')}
      </div>

      ${a.map(x => `
        <div class="job">
          <b>
            ${safe(
              (js.find(j => j.id === x.job_id) || {}).title ||
              'Listing #' + x.job_id
            )}
          </b>
          ${pills([x.status])}
          <small>${safe(x.created)}</small>
        </div>
      `).join('') || '<p>No saved jobs yet.</p>'}
    `);
  }

  if (page === 'market') {
    let a = await api('/market');
    let max = Math.max(...a.skills.map(x => x[1]), 1);

    c.innerHTML = box('Job catalog intelligence', `
      <div class="notice">
        ${safe(a.disclaimer)}
        Catalog size: ${a.sample_size}.
      </div>

      <h3>Most common listed skills</h3>

      ${bars(
        a.skills.map(([k, v]) => [k, Math.round(v / max * 100)])
      )}

      <h3>Locations</h3>

      ${a.locations.map(x => `
        <p>${safe(x[0])}: ${x[1]} listings</p>
      `).join('')}
    `);
  }

  if (page === 'recruiter') {
    c.innerHTML = box('Publish a recruiter listing', `
      <div class="form-row">
        <input id="company" placeholder="Company name">
        <input id="jobTitle" placeholder="Job title">
      </div>

      <div class="form-row">
        <input id="jobLocation" placeholder="Location">
        <input id="jobSkills" placeholder="Skills, comma separated">
      </div>

      <textarea id="jobDescription"
                placeholder="Role description"></textarea>

      <br><br>

      <button class="primary" onclick="postListing()">
        Publish listing
      </button>
    `);
  }
}

function roadmapHtml(r) {
  return box('90-day personalized roadmap', `
    <div class="row">
      <h3>${safe(r.role)}</h3>
      <span class="pill">90-day plan</span>
    </div>

    <p>
      Skills to develop:
      ${safe(
        r.missing.join(', ') ||
        'No gaps identified from the configured skill list'
      )}
    </p>

    <div class="three">
      ${r.milestones.map(m => `
        <div class="card">
          <h3>${safe(m.period)}</h3>
          ${pills(m.tasks)}
          <p class="mini">
            Deliverable: ${safe(m.deliverable)}
          </p>
        </div>
      `).join('')}
    </div>
  `);
}

async function saveProfile() {
  try {
    profile = {
      education: $('edu').value,
      location: $('loc').value,
      skills: $('skills').value
        .split(',')
        .map(x => x.trim().toLowerCase())
        .filter(Boolean),
      goal: $('goal').value,
      resume: profile.resume || ''
    };

    await api('/profile', 'POST', profile);
    toast('Profile saved');
  } catch (e) {
    toast(e.message);
  }
}

async function uploadResume() {
  try {
    let f = new FormData();
    f.append('file', $('resumeFile').files[0]);

    let r = await api('/resume/upload', 'POST', f);

    $('resumeText').value = r.text;
    displayResume(r);
  } catch (e) {
    toast(e.message);
  }
}

async function analyzeResume() {
  try {
    let text = $('resumeText').value;

    let r = await api('/resume/analyze', 'POST', { text });

    profile.resume = text;
    profile.skills = [
      ...new Set([...profile.skills, ...r.skills])
    ];

    await api('/profile', 'POST', profile);
    displayResume(r);
  } catch (e) {
    toast(e.message);
  }
}

function displayResume(r) {
  $('resumeOutput').innerHTML = `
    <div class="separator"></div>

    <div class="row">
      <h3>Document completeness</h3>
      <div class="score">${r.readiness_score}/100</div>
    </div>

    <div class="progress">
      <span style="width:${r.readiness_score}%"></span>
    </div>

    <p class="mini">${safe(r.score_note)}</p>

    <h3>Extracted skills</h3>
    ${pills(r.skills)}

    <h3>Suggestions</h3>
    ${r.suggestions.map(s => `
      <p>• ${safe(s)}</p>
    `).join('') || '<p>All configured checks passed.</p>'}
  `;

  toast('Resume analyzed');
}

async function searchJobs() {
  let j = await api(
    '/jobs?q=' + encodeURIComponent($('jobQuery').value) +
    '&location=' + encodeURIComponent($('jobLoc').value)
  );

  $('jobResults').innerHTML = jobsHtml(j);
}

async function roadmapFor(role) {
  page = 'roadmap';
  $('pageTitle').textContent = 'Skill Roadmap';

  let r = await api(
    '/roadmap?role=' + encodeURIComponent(role)
  );

  $('content').innerHTML = roadmapHtml(r);
}

async function runAgent() {
  try {
    $('agentOutput').innerHTML =
      '<p>Executing workflow...</p>';

    let r = await api('/agent/run', 'POST', {
      text: $('agentGoal').value
    });

    $('agentOutput').innerHTML = `
      <div class="separator"></div>
      <h3>Agent execution trace</h3>

      ${r.trace.map(t => `
        <div class="trace">
          <b>${safe(t.agent)} ✓</b>
          <p>
            ${safe(t.tool)} — ${safe(t.result)}
          </p>
        </div>
      `).join('')}

      <div class="two">
        ${box('Top job matches', jobsHtml(r.jobs, true))}

        ${box('Career development', `
          <h3>${safe(r.roadmap.role)}</h3>
          <p>
            Skill gaps: ${safe(r.roadmap.missing.join(', '))}
          </p>

          ${r.roadmap.milestones.map(x => `
            <p>
              <b>${safe(x.period)}:</b>
              ${safe(x.tasks.join(', '))}
            </p>
          `).join('')}

          <h3>Interview practice</h3>
          <p>${safe(r.interview_question)}</p>
        `)}
      </div>

      <div class="notice">${safe(r.notice)}</div>
    `;
  } catch (e) {
    toast(e.message);
  }
}

async function askRag() {
  try {
    let r = await api('/rag', 'POST', {
      text: $('ragQuestion').value
    });

    $('ragOutput').innerHTML = `
      <div class="separator"></div>
      <p>${safe(r.answer)}</p>

      <h3>Retrieved sources</h3>

      ${r.sources.map(x => `
        <div class="job">
          <b>${safe(x.title)}</b>
          <p>${safe(x.text)}</p>
        </div>
      `).join('') || '<p>No supporting sources found.</p>'}
    `;
  } catch (e) {
    toast(e.message);
  }
}

let interviewSession = null;

async function startInterview() {
  try {
    let r = await api('/interview/start', 'POST', {
      text: $('interviewRole').value
    });

    interviewSession = {
      id: r.session_id,
      role: r.role,
      index: 0
    };

    showInterviewQuestion(r.question, 0, r.total);
  } catch (e) {
    toast(e.message);
  }
}

function showInterviewQuestion(question, index, total) {
  $('interviewOutput').innerHTML = `
    <div class="separator"></div>
    <div class="notice">
      Question ${index + 1} of ${total}
    </div>

    <h3>${safe(question)}</h3>

    <textarea id="interviewAnswer"
              placeholder="Write your answer here..."></textarea>

    <br><br>

    <button class="primary" onclick="submitInterview()">
      Submit answer →
    </button>
  `;
}

async function submitInterview() {
  try {
    if (!interviewSession) return;

    let answer = $('interviewAnswer').value.trim();

    if (!answer) {
      toast('Please enter an answer');
      return;
    }

    let r = await api('/interview', 'POST', {
      role: interviewSession.role,
      session_id: interviewSession.id,
      question_index: interviewSession.index,
      answer
    });

    let feedback = `
      <div class="notice">
        <b>
          Question ${interviewSession.index + 1}
          feedback (${r.score}/100):
        </b>
        ${safe(r.feedback)}
      </div>
    `;

    if (r.completed) {
      interviewSession = null;
      let s = r.summary;

      $('interviewOutput').innerHTML = `
        <h3>Mock interview complete</h3>

        <div class="score">
          Overall practice score: ${s.overall_score}/100
        </div>

        <p class="mini">${safe(s.note)}</p>

        ${s.answers.map(a => `
          <div class="job">
            <h3>
              Question ${a.question_index + 1}:
              ${safe(a.question)}
            </h3>

            <p>
              <b>Your answer:</b> ${safe(a.answer)}
            </p>

            <p>
              <b>Feedback (${a.score}/100):</b>
              ${safe(a.feedback)}
            </p>
          </div>
        `).join('')}

        <button class="primary"
                onclick="navigate('interview')">
          Start another interview
        </button>
      `;
    } else {
      interviewSession.index = r.question_index;

      showInterviewQuestion(
        r.question,
        r.question_index,
        r.total
      );

      $('interviewOutput').insertAdjacentHTML(
        'afterbegin',
        feedback
      );
    }
  } catch (e) {
    toast(e.message);
  }
}

async function postListing() {
  try {
    await api('/recruiter/jobs', 'POST', {
      title: $('jobTitle').value,
      company: $('company').value,
      location: $('jobLocation').value,
      skills: $('jobSkills').value
        .split(',')
        .map(x => x.trim().toLowerCase())
        .filter(Boolean),
      description: $('jobDescription').value
    });

    toast('Listing published');
    navigate('recruiter');
  } catch (e) {
    toast(e.message);
  }
}

// SEMANTIC RAG API CALL
async function askSemanticRag() {
  let el = $('aiRagOutput');

  el.innerHTML =
    '<p>Contacting the embedding model and LLM...</p>';

  try {
    let r = await api('/ai/rag', 'POST', {
      text: $('aiRagQuestion').value
    });

    el.innerHTML = `
      <div class="separator"></div>

      <h3>Grounded AI answer</h3>

      <div class="output" style="white-space:pre-wrap">
        ${safe(r.answer)}
      </div>

      <h3>Retrieved knowledge passages</h3>

      ${r.sources.map((x, i) => `
        <div class="job">
          <b>[${i + 1}] ${safe(x.title)}</b>
          <small>
            ${safe(x.id)} · similarity ${x.relevance}
          </small>
          <p>${safe(x.text)}</p>
        </div>
      `).join('') ||
        '<p>No relevant evidence found. No answer was fabricated.</p>'}
    `;
  } catch (e) {
    el.innerHTML = `
      <div class="notice danger">
        ${safe(e.message)}
      </div>
    `;
  }
}

// LLM AGENT PLANNER API CALL
async function runLlmAgent() {
  let el = $('aiAgentOutput');

  el.innerHTML =
    '<p>LLM is planning and executing approved tools...</p>';

  try {
    let r = await api('/ai/agent/run', 'POST', {
      text: $('aiAgentGoal').value
    });

    el.innerHTML = `
      <div class="separator"></div>

      <h3>Model-selected plan</h3>
      <p>${safe(r.plan.reason)}</p>

      <div>${pills(r.plan.tools)}</div>

      <h3>Actual tool execution</h3>

      ${r.trace.map(t => `
        <div class="trace">
          <b>${safe(t.agent)}</b>
          <p>
            ${safe(t.tool)} — ${safe(t.result)}
          </p>
        </div>
      `).join('')}

      <h3>LLM career guidance</h3>

      <div class="output" style="white-space:pre-wrap">
        ${safe(r.answer)}
      </div>

      <div class="notice">
        ${safe(r.notice)}
      </div>
    `;
  } catch (e) {
    el.innerHTML = `
      <div class="notice danger">
        ${safe(e.message)}
      </div>
    `;
  }
}

if (token) {
  boot();
}
