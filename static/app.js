const STORAGE_KEYS = {
  evidence: 'growth_mini_evidence',
  sprint: 'growth_mini_sprint',
  checkins: 'growth_mini_checkins',
};

const readStored = (key, fallback) => {
  try {
    return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback));
  } catch {
    return fallback;
  }
};

const state = {
  family: 'all',
  matrix: [],
  priorities: [],
  sprint: readStored(STORAGE_KEYS.sprint, null),
  evidence: readStored(STORAGE_KEYS.evidence, {}),
  checkins: readStored(STORAGE_KEYS.checkins, {}),
  report: null,
};

const $ = id => document.getElementById(id);
const escapeHtml = (value = '') => String(value).replace(
  /[&<>'"]/g,
  character => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[character]),
);

async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: {'Content-Type': 'application/json'},
    ...options,
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

const familyLabel = key => ({application: '应用/平台', algorithm: '算法', product: '产品'})[key] || key;

async function loadMatrix() {
  state.family = $('roleFamily').value;
  const data = await api(`/matrix?role_family=${encodeURIComponent(state.family)}`);
  state.matrix = data.matrix;
  const summary = data.summary;
  $('datasetStats').innerHTML = `<div class="stat"><strong>${summary.jd_count}</strong><small>份JD</small></div>`
    + Object.entries(summary.families).map(([key, count]) => (
      `<div class="stat"><strong>${count}</strong><small>${familyLabel(key)}</small></div>`
    )).join('');
  renderMatrix();
  renderEvidence();
  $('step-priority').classList.add('hidden');

  if (state.sprint) {
    $('step-sprint').classList.remove('hidden');
    renderSprint();
  } else {
    $('step-sprint').classList.add('hidden');
  }
}

function renderMatrix() {
  const body = $('matrixBody');
  if (!state.matrix.length) {
    body.innerHTML = '<tr><td colspan="8" class="loading">当前筛选没有岗位数据。</td></tr>';
    return;
  }
  body.innerHTML = state.matrix.map(row => `
    <tr>
      <td><strong>${escapeHtml(row.skill)}</strong><div class="meter"><i style="width:${row.frequency * 100}%"></i></div></td>
      <td>${escapeHtml(row.category)}</td><td>${row.jd_count}/${row.total_jds}</td>
      <td>${row.required_count}</td><td>${row.responsibility_count}</td><td>${row.preferred_count}</td>
      <td>${row.role_weight.toFixed(3)}</td>
      <td><details><summary>${row.sources.length}条来源</summary>${row.sources.map(source => `
        <div class="source"><b>${escapeHtml(source.company)} · ${escapeHtml(source.title)}</b>
        <span>${escapeHtml(source.excerpt)}</span><br><code>${escapeHtml(source.source_path)}</code><br>
        <small>${escapeHtml(source.source_type || '来源未标注')}</small></div>`).join('')}</details></td>
    </tr>`).join('');
}

function renderEvidence() {
  const rows = state.matrix.slice(0, 14);
  $('evidenceList').innerHTML = rows.map(row => {
    const saved = state.evidence[row.skill] || {status: 'none', title: '', url: ''};
    return `<div class="evidence-row" data-skill="${escapeHtml(row.skill)}">
      <div class="evidence-skill"><strong>${escapeHtml(row.skill)}</strong><small>${row.jd_count}/${row.total_jds}份JD出现 · 权重${row.role_weight.toFixed(3)}</small></div>
      <label>证据状态<select class="ev-status">
        <option value="none" ${saved.status === 'none' ? 'selected' : ''}>暂无证据</option>
        <option value="claimed" ${saved.status === 'claimed' ? 'selected' : ''}>只有自述/笔记</option>
        <option value="verified" ${saved.status === 'verified' ? 'selected' : ''}>有可验证作品</option>
      </select></label>
      <label>证据名称<input class="ev-title" value="${escapeHtml(saved.title)}" placeholder="例如：Growth后端"></label>
      <label>作品链接（可选）<input class="ev-url" value="${escapeHtml(saved.url)}" placeholder="GitHub / Demo / 报告"></label>
    </div>`;
  }).join('');
}

function collectEvidence() {
  document.querySelectorAll('.evidence-row').forEach(row => {
    const skill = row.dataset.skill;
    state.evidence[skill] = {
      skill,
      status: row.querySelector('.ev-status').value,
      title: row.querySelector('.ev-title').value.trim(),
      url: row.querySelector('.ev-url').value.trim(),
      note: '',
    };
  });
  localStorage.setItem(STORAGE_KEYS.evidence, JSON.stringify(state.evidence));
  return Object.values(state.evidence);
}

async function calculatePriorities() {
  const data = await api('/priorities', {
    method: 'POST',
    body: JSON.stringify({evidence: collectEvidence(), role_family: state.family}),
  });
  state.priorities = data.priorities;
  $('step-priority').classList.remove('hidden');
  $('priorityList').innerHTML = state.priorities.slice(0, 6).map((row, index) => `
    <article class="card priority-card"><div class="score">${row.priority.toFixed(1)}</div>
      <p class="muted">补强优先级 · #${index + 1}</p><h3>${escapeHtml(row.skill)}</h3>
      <p class="muted">${row.jd_count}/${row.total_jds}份JD出现 · ${row.evidence_status === 'verified' ? '已有作品' : row.evidence_status === 'claimed' ? '只有自述' : '暂无证据'}</p>
      <div class="formula">${escapeHtml(row.formula)}</div></article>`).join('');
  $('sprintSkill').innerHTML = state.priorities.filter(row => row.priority > 0).slice(0, 12).map(row => (
    `<option value="${escapeHtml(row.skill)}">${escapeHtml(row.skill)} · ${row.priority.toFixed(1)}</option>`
  )).join('');
  $('step-sprint').classList.remove('hidden');
  $('step-priority').scrollIntoView({behavior: 'smooth'});
}

async function generateSprint() {
  const skill = $('sprintSkill').value;
  const dailyMinutes = Number($('dailyMinutes').value || 90);
  state.sprint = await api('/sprint', {
    method: 'POST',
    body: JSON.stringify({skill, daily_minutes: dailyMinutes}),
  });
  state.checkins = {};
  state.report = null;
  localStorage.setItem(STORAGE_KEYS.sprint, JSON.stringify(state.sprint));
  localStorage.setItem(STORAGE_KEYS.checkins, '{}');
  renderSprint();
}

function renderSprint() {
  const sprint = state.sprint;
  $('sprintResult').innerHTML = `
    <div class="sprint-title"><h3>${escapeHtml(sprint.title)}</h3>
      <p><strong>最终产物：</strong>${escapeHtml(sprint.deliverable)} · 预计${sprint.estimated_total_minutes}分钟</p>
      <small class="muted">冲刺和每日记录已保存在当前浏览器。重新打开页面仍可继续。</small></div>
    <div class="days">${sprint.days.map(day => {
      const check = state.checkins[day.day] || {};
      return `<article class="card day-card" data-day="${day.day}">
        <div class="day-number">D${day.day}</div><div>
          <h3>${escapeHtml(day.theme)}</h3><p>${escapeHtml(day.task)}</p>
          <p class="acceptance"><strong>今日产出：</strong>${escapeHtml(day.acceptance)}</p>
          <div class="checkin-summary">
            <label class="done-field"><input class="ci-done" type="checkbox" ${check.completed ? 'checked' : ''}>今天已完成</label>
            <label>实际学习分钟<input class="ci-minutes" type="number" min="0" max="1440" value="${check.actual_minutes || ''}" placeholder="例如 75"></label>
            <label>今日产物链接<input class="ci-url" value="${escapeHtml(check.artifact_url || '')}" placeholder="GitHub commit / Demo / 文档（可选）"></label>
          </div>
          <label class="journal-field">Markdown 学习记录<textarea class="ci-note" rows="7" placeholder="# 今天理解了什么\n\n## 今天实际做了什么\n\n## 关键结论">${escapeHtml(check.note || '')}</textarea></label>
          <div class="reflection-grid">
            <label>当前阻塞<textarea class="ci-blocker" rows="3" placeholder="哪里还没想通或没做完？">${escapeHtml(check.blocker || '')}</textarea></label>
            <label>明天第一步<textarea class="ci-next" rows="3" placeholder="写一个足够小、可以直接开始的动作">${escapeHtml(check.next_step || '')}</textarea></label>
          </div>
          <small class="muted">预计 ${day.estimated_minutes} 分钟 · 输入内容会自动保存在本机</small>
        </div></article>`;
    }).join('')}</div>`;

  document.querySelectorAll('.day-card input, .day-card textarea').forEach(input => {
    input.addEventListener('input', saveCheckins);
    input.addEventListener('change', saveCheckins);
  });
  $('reportButton').classList.remove('hidden');
  if (state.report) $('exportButton').classList.remove('hidden');
}

function saveCheckins() {
  document.querySelectorAll('.day-card').forEach(card => {
    const day = Number(card.dataset.day);
    state.checkins[day] = {
      day,
      completed: card.querySelector('.ci-done').checked,
      actual_minutes: Number(card.querySelector('.ci-minutes').value || 0),
      artifact_url: card.querySelector('.ci-url').value.trim(),
      note: card.querySelector('.ci-note').value.trim(),
      blocker: card.querySelector('.ci-blocker').value.trim(),
      next_step: card.querySelector('.ci-next').value.trim(),
    };
  });
  localStorage.setItem(STORAGE_KEYS.checkins, JSON.stringify(state.checkins));
}

async function generateReport() {
  saveCheckins();
  state.report = await api('/report', {
    method: 'POST',
    body: JSON.stringify({
      estimated_minutes: state.sprint.estimated_total_minutes,
      checkins: Object.values(state.checkins),
    }),
  });
  const report = state.report;
  const error = report.estimation_error_percent == null
    ? '—'
    : `${report.estimation_error_percent > 0 ? '+' : ''}${report.estimation_error_percent}%`;
  $('reportResult').innerHTML = `<section class="card report">
    <p class="eyebrow">Seven-day learning archive</p><h3>结项学习档案</h3>
    <p class="muted">这里只汇总你留下的记录，不判断掌握程度，也不把完成天数包装成能力分数。</p>
    <div class="report-grid">
      <div class="report-metric"><strong>${report.recorded_days}/7</strong><span>有记录天数</span></div>
      <div class="report-metric"><strong>${report.actual_minutes}</strong><span>实际分钟</span></div>
      <div class="report-metric"><strong>${error}</strong><span>时间预测偏差</span></div>
      <div class="report-metric"><strong>${report.artifact_count}</strong><span>产物链接</span></div>
    </div>
    <p>已保存 ${report.note_count} 篇学习记录。下载 Markdown 后，可以继续整理到 GitHub、笔记软件或未来的个人知识档案中。</p>
  </section>`;
  $('exportButton').classList.remove('hidden');
  $('reportResult').scrollIntoView({behavior: 'smooth'});
}

function markdownValue(value) {
  return String(value || '').trim() || '未记录';
}

function buildMarkdownArchive() {
  const report = state.report;
  const matrixRow = state.matrix.find(row => row.skill === state.sprint.skill);
  const sourceSummary = matrixRow
    ? `该能力在当前筛选的 ${matrixRow.jd_count}/${matrixRow.total_jds} 份 JD 中出现。`
    : '岗位来源统计未保存在本次导出中。';
  const error = report.estimation_error_percent == null
    ? '无法计算'
    : `${report.estimation_error_percent > 0 ? '+' : ''}${report.estimation_error_percent}%`;
  const sections = state.sprint.days.map(day => {
    const check = report.checkins.find(item => item.day === day.day) || {};
    return `## Day ${day.day} · ${day.theme}\n\n`
      + `- 计划任务：${day.task}\n`
      + `- 今日产出：${day.acceptance}\n`
      + `- 完成状态：${check.completed ? '已完成' : '未完成'}\n`
      + `- 预计时间：${day.estimated_minutes} 分钟\n`
      + `- 实际时间：${check.actual_minutes || 0} 分钟\n`
      + `- 产物链接：${markdownValue(check.artifact_url)}\n\n`
      + `### 学习记录\n\n${markdownValue(check.note)}\n\n`
      + `### 当前阻塞\n\n${markdownValue(check.blocker)}\n\n`
      + `### 明天第一步\n\n${markdownValue(check.next_step)}\n`;
  }).join('\n---\n\n');

  return `# ${state.sprint.skill} · 7天学习证据档案\n\n`
    + `> 由 Growth Mini 在 ${new Date().toLocaleDateString('zh-CN')} 导出。本文档只记录学习过程和产物，不代表能力等级或录用概率。\n\n`
    + `## 选择依据\n\n${sourceSummary}\n\n`
    + `## 目标产物\n\n${state.sprint.deliverable}\n\n`
    + `## 时间与记录\n\n`
    + `- 有记录天数：${report.recorded_days}/7\n`
    + `- 完成天数：${report.completed_days}/7\n`
    + `- 预计总时间：${report.estimated_minutes} 分钟\n`
    + `- 实际总时间：${report.actual_minutes} 分钟\n`
    + `- 时间预测偏差：${error}\n`
    + `- 学习记录：${report.note_count} 篇\n`
    + `- 产物链接：${report.artifact_count} 个\n\n---\n\n${sections}\n`;
}

function exportMarkdown() {
  if (!state.report) return;
  const blob = new Blob([buildMarkdownArchive()], {type: 'text/markdown;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const safeSkill = state.sprint.skill.replace(/[\\/:*?"<>|]/g, '-');
  link.href = url;
  link.download = `growth-mini-${safeSkill}-7day-log.md`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

$('roleFamily').addEventListener('change', loadMatrix);
$('rankButton').addEventListener('click', calculatePriorities);
$('sprintButton').addEventListener('click', generateSprint);
$('reportButton').addEventListener('click', generateReport);
$('exportButton').addEventListener('click', exportMarkdown);

loadMatrix().catch(error => {
  $('matrixBody').innerHTML = `<tr><td colspan="8" class="loading">读取失败：${escapeHtml(error.message)}</td></tr>`;
});
