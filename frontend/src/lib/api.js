import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({ baseURL: API_BASE, withCredentials: true, timeout: 240000 });

export const apiRaw = api;

// --- auth ---
export const authMe = () => api.get('/auth/me').then(r => r.data);
export const exchangeSession = (session_id) => api.post('/auth/session', { session_id }).then(r => r.data);
export const devLogin = (email, name) => api.post('/auth/dev-login', { email, name }).then(r => r.data);
export const logoutApi = () => api.post('/auth/logout').then(r => r.data);

// --- config / settings ---
export const getModelConfig = () => api.get('/config/models').then(r => r.data);
export const getSettings = () => api.get('/settings').then(r => r.data);
export const putSettings = (body) => api.put('/settings', body).then(r => r.data);

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
export const siteUrl = (id) => `${API_BASE}/sites/${id}`;

// --- qa / branding / bonuses ---
export const runQA = (id) => api.post(`/projects/${id}/qa`, {}).then(r => r.data);
export const applyQA = (id) => api.post(`/projects/${id}/qa/apply`).then(r => r.data);
export const genBranding = (id, style) => api.post(`/projects/${id}/branding`, { style }).then(r => r.data);
export const genBonuses = (id) => api.post(`/projects/${id}/bonuses`).then(r => r.data);
export const ebookBonusGenerate = (id, index) => api.post(`/projects/${id}/ebook/bonus/${index}/generate`).then(r => r.data);

// --- assets ---
export const downloadUrl = (id, assetId) => `${API_BASE}/projects/${id}/assets/${assetId}/download`;
