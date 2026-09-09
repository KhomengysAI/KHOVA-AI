import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({ baseURL: API_BASE, withCredentials: true, timeout: 240000 });

// Auto-refresh the credits pill whenever a response carries economy info.
api.interceptors.response.use((resp) => {
  try {
    const d = resp && resp.data;
    if (d && (d._economy || d.public_url || d._applied)) {
      window.dispatchEvent(new Event('khova:economy'));
    }
  } catch (e) { /* noop */ }
  return resp;
}, (error) => {
  // Normalize structured error payloads. The backend returns a dict `detail`
  // for generation failures / anonymous limits: { message, code, refunded, balance, ... }.
  // Keep `detail` a string (so existing `e.response.data.detail` usage still works)
  // and expose the structured info under `_structured` / `_refund`.
  try {
    const d = error && error.response && error.response.data;
    if (d && d.detail && typeof d.detail === 'object') {
      const obj = d.detail;
      d._structured = obj;
      d.detail = obj.message || obj.detail || 'Something went wrong.';
      if (obj.refunded && Number(obj.refunded) > 0) {
        d._refund = { refunded: Number(obj.refunded), balance: obj.balance };
        window.dispatchEvent(new Event('khova:economy'));
      }
    }
  } catch (e) { /* noop */ }
  return Promise.reject(error);
});

export const apiRaw = api;

// --- auth ---
export const authMe = () => api.get('/auth/me').then(r => r.data);
export const exchangeSession = (session_id) => api.post('/auth/session', { session_id }).then(r => r.data);
export const devLogin = (email, name) => api.post('/auth/dev-login', { email, name }).then(r => r.data);
export const logoutApi = () => api.post('/auth/logout').then(r => r.data);

// --- config / settings ---
export const getSettings = () => api.get('/settings').then(r => r.data);
export const putSettings = (body) => api.put('/settings', body).then(r => r.data);

// --- economy (plan / credits / usage) ---
export const getEconomy = () => api.get('/me/economy').then(r => r.data);
export const getUsage = () => api.get('/me/usage').then(r => r.data);
export const redeemCode = (code) => api.post('/redeem', { code }).then(r => r.data);

// --- admin ---
export const adminOverview = () => api.get('/admin/overview').then(r => r.data);
export const adminListUsers = () => api.get('/admin/users').then(r => r.data);
export const adminListJobs = () => api.get('/admin/jobs').then(r => r.data);
export const adminListCodes = () => api.get('/admin/codes').then(r => r.data);
export const adminCreateCode = (body) => api.post('/admin/codes', body).then(r => r.data);
export const adminUpdateUser = (userId, body) => api.patch(`/admin/users/${userId}`, body).then(r => r.data);

// --- projects ---
export const createProject = (body) => api.post('/projects', body).then(r => r.data);
export const listProjects = () => api.get('/projects').then(r => r.data);
export const getProject = (id) => api.get(`/projects/${id}`).then(r => r.data);
export const patchProject = (id, body) => api.patch(`/projects/${id}`, body).then(r => r.data);
export const deleteProject = (id) => api.delete(`/projects/${id}`).then(r => r.data);
export const duplicateProject = (id) => api.post(`/projects/${id}/duplicate`).then(r => r.data);
export const createSample = () => api.post('/projects/sample').then(r => r.data);

// --- pipeline ---
export const saveDiscover = (id, body) => api.post(`/projects/${id}/discover`, body).then(r => r.data);
export const runResearch = (id) => api.post(`/projects/${id}/research`).then(r => r.data);
export const genOpportunities = (id) => api.post(`/projects/${id}/opportunities`).then(r => r.data);
export const toggleSaveOpp = (id, oid) => api.post(`/projects/${id}/opportunities/save/${oid}`).then(r => r.data);
export const selectOpportunity = (id, oid) => api.post(`/projects/${id}/select-opportunity`, { opportunity_id: oid }).then(r => r.data);
export const genPositioning = (id) => api.post(`/projects/${id}/positioning`).then(r => r.data);
export const genTransformation = (id) => api.post(`/projects/${id}/transformation`).then(r => r.data);
export const setPalette = (id, palette) => api.patch(`/projects/${id}/palette`, { palette }).then(r => r.data);
export const setFormat = (id, format) => api.post(`/projects/${id}/format`, { format }).then(r => r.data);

// --- ebook ---
export const ebookPlan = (id) => api.post(`/projects/${id}/ebook/plan`).then(r => r.data);
export const ebookSection = (id, chapter_num, tone) => api.post(`/projects/${id}/ebook/section`, { chapter_num, tone }).then(r => r.data);
export const ebookIntro = (id) => api.post(`/projects/${id}/ebook/intro`).then(r => r.data);
export const ebookRewrite = (id, chapter_num, instruction) => api.post(`/projects/${id}/ebook/section/rewrite`, { chapter_num, instruction }).then(r => r.data);
export const ebookDesign = (id, design_system) => api.patch(`/projects/${id}/ebook/design`, { design_system }).then(r => r.data);
export const ebookCover = (id) => api.post(`/projects/${id}/ebook/cover`).then(r => r.data);
export const ebookIllustration = (id, chapter_num, prompt) => api.post(`/projects/${id}/ebook/illustration`, { chapter_num, prompt }).then(r => r.data);
export const ebookExport = (id) => api.post(`/projects/${id}/ebook/export`).then(r => r.data);
export const ebookPreviewUrl = (id) => `${API_BASE}/projects/${id}/ebook/preview-html`;
export const ebookDesignCheck = (id) => api.get(`/projects/${id}/ebook/design-check`).then(r => r.data);

// --- spreadsheet ---
export const spreadsheetSpec = (id) => api.post(`/projects/${id}/spreadsheet/spec`).then(r => r.data);
export const spreadsheetBuild = (id) => api.post(`/projects/${id}/spreadsheet/build`).then(r => r.data);

// --- website ---
export const websiteSpec = (id, style) => api.post(`/projects/${id}/website/spec`, { style }).then(r => r.data);
export const websiteBuild = (id) => api.post(`/projects/${id}/website/build`).then(r => r.data);
export const websiteEdit = (id, spec) => api.patch(`/projects/${id}/website/spec`, { spec }).then(r => r.data);
export const websiteRegenSection = (id, section, instruction) => api.post(`/projects/${id}/website/section/regenerate`, { section, instruction }).then(r => r.data);
export const websitePublish = (id) => api.post(`/projects/${id}/website/publish`).then(r => r.data);
export const websiteUnpublish = (id) => api.post(`/projects/${id}/website/unpublish`).then(r => r.data);
export const websiteSetStyle = (id, style) => api.patch(`/projects/${id}/website/style`, { style }).then(r => r.data);
export const siteUrl = (id) => `${API_BASE}/sites/${id}`;
export const sitePreviewUrl = (id) => `${API_BASE}/sites/${id}?preview=1`;

// --- qa / branding / bonuses ---
export const runQA = (id) => api.post(`/projects/${id}/qa`, {}).then(r => r.data);
export const applyQA = (id) => api.post(`/projects/${id}/qa/apply`).then(r => r.data);
export const applyQAIssue = (id, issueId) => api.post(`/projects/${id}/qa/apply-issue/${issueId}`).then(r => r.data);
export const genBranding = (id, style) => api.post(`/projects/${id}/branding`, { style }).then(r => r.data);
export const genBonuses = (id) => api.post(`/projects/${id}/bonuses`).then(r => r.data);
export const ebookBonusGenerate = (id, index) => api.post(`/projects/${id}/ebook/bonus/${index}/generate`).then(r => r.data);

// --- assets ---
export const downloadUrl = (id, assetId) => `${API_BASE}/projects/${id}/assets/${assetId}/download`;
export const bundleDownloadUrl = (id) => `${API_BASE}/projects/${id}/bundle`;
export const fetchBundle = (id) => apiRaw.get(`/projects/${id}/bundle`, { responseType: 'blob' });
