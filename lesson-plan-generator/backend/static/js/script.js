// ========== CONFIG ==========
const API_BASE = window.location.origin + "/api";

window.isPremiumUser = false;

// DOM
const lessonForm = document.getElementById('lessonForm');
const lessonPlanContent = document.getElementById('lessonPlanContent');
const resultContainer = document.getElementById('resultContainer');

// Dropdowns
const levelSelect = document.getElementById('level');
const classSelect = document.getElementById('className');
const subjectSelect = document.getElementById('subject');
const unitSelect = document.getElementById('unitNo');
const lessonSelect = document.getElementById('lessonTitle');

// ========== CACHE ==========
const CACHE_NAME = 'cbc-lesson-cache-v1';
const STATIC_ASSETS = [
    '/',
    '/static/js/script.js',
    '/static/css/style.css',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png'
];

// Register Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/service-worker.js')
            .then(reg => console.log('Service Worker registered:', reg.scope))
            .catch(err => console.error('SW registration failed:', err));
    });
}

// ========== INIT ==========
document.addEventListener("DOMContentLoaded", () => {
    if (levelSelect) loadLevels();
    else loadClasses();
});

// ========== EVENT LISTENERS ==========
if (levelSelect) levelSelect.addEventListener('change', () => {
    resetBelow('level');
    if (levelSelect.value) loadClasses(levelSelect.value);
});

classSelect.addEventListener('change', () => {
    resetBelow('class');
    if (classSelect.value) loadSubjects(classSelect.value);
});

subjectSelect.addEventListener('change', () => {
    resetBelow('subject');
    if (subjectSelect.value) loadUnits(subjectSelect.value);
});

unitSelect.addEventListener('change', () => {
    resetBelow('unit');
    if (unitSelect.value) loadLessons(unitSelect.value);
});

lessonForm.addEventListener('submit', (e) => {
    e.preventDefault();
    generateLessonPlan();
});

// ========== FETCH WITH CACHE ==========
async function fetchData(endpoint, params = {}) {
    const url = new URL(`${API_BASE}/${endpoint}/`);
    Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, v));

    try {
        const cache = await caches.open(CACHE_NAME);
        const cachedResponse = await cache.match(url);
        if (cachedResponse) {
            const data = await cachedResponse.json();
            // Update cache in background
            fetch(url).then(r => cache.put(url, r.clone()));
            return data;
        } else {
            const res = await fetch(url);
            const data = await res.json();
            cache.put(url, new Response(JSON.stringify(data)));
            return data;
        }
    } catch (err) {
        console.warn('Fetch failed, trying cache...', err);
        const cache = await caches.open(CACHE_NAME);
        const cachedResponse = await cache.match(url);
        return cachedResponse ? await cachedResponse.json() : [];
    }
}

// ========== RESET HELPERS ==========
function resetBelow(level) {
    if (level === 'level') classSelect.innerHTML = `<option value="">Select Class</option>`;
    if (['level', 'class'].includes(level)) subjectSelect.innerHTML = `<option value="">Select Subject</option>`;
    if (['level', 'class', 'subject'].includes(level)) unitSelect.innerHTML = `<option value="">Select Unit</option>`;
    if (['level', 'class', 'subject', 'unit'].includes(level)) lessonSelect.innerHTML = `<option value="">Select Lesson</option>`;
}

// ========== LOADERS ==========
async function loadLevels() {
    const levels = await fetchData('levels');
    levelSelect.innerHTML = `<option value="">Select Level</option>`;
    levels.forEach(l => levelSelect.innerHTML += `<option value="${l.id}">${l.name}</option>`);
}

async function loadClasses(levelId = null) {
    const params = levelId ? { level_id: levelId } : {};
    const classes = await fetchData('classes', params);
    classSelect.innerHTML = `<option value="">Select Class</option>`;
    classes.forEach(c => classSelect.innerHTML += `<option value="${c.id}">${c.name}</option>`);
}

async function loadSubjects(classId) {
    const subjects = await fetchData('subjects', { class_id: classId });
    subjectSelect.innerHTML = `<option value="">Select Subject</option>`;
    subjects.forEach(s => subjectSelect.innerHTML += `<option value="${s.id}">${s.name}</option>`);
}

async function loadUnits(subjectId) {
    const units = await fetchData('units', { subject_id: subjectId });
    unitSelect.innerHTML = `<option value="">Select Unit</option>`;
    units.forEach(u => 
        unitSelect.innerHTML += `<option value="${u.id}" data-title="${u.title}" data-total="${u.total_lessons}">Unit ${u.number}</option>`);
}

unitSelect.addEventListener('change', () => {
    resetBelow('unit');
    if (unitSelect.value) {
        const selected = unitSelect.selectedOptions[0];
        document.getElementById('unitTitle').value = selected.dataset.title || '';
        document.getElementById('totalLessons').value = selected.dataset.total || '';
        loadLessons(unitSelect.value);
    }
});

async function loadLessons(unitId) {
    const lessons = await fetchData('lessons', { unit_id: unitId });
    lessonSelect.innerHTML = `<option value="">Select Lesson</option>`;
    lessons.forEach(l => lessonSelect.innerHTML += `<option value="${l.id}">${l.title}</option>`);
}

// ========== FORM & GENERATOR (unchanged) ==========
function getFormData() { /* same as before */ }
function calculateTiming(total) { /* same as before */ }
function generateLessonPlan() { /* same as before */ }
function buildHeader(d) { /* same as before */ }
function buildLessonInfoTable(d) { /* same as before */ }
function buildUnitTable(d) { /* same as before */ }
function buildSteps(d, t) { /* same as before */ }
function step(name, time, d) { /* same as before */ }

// ========== PREMIUM ==========
function copyToWord() { if (!window.isPremiumUser) return; /* same */ }
function downloadPDF() { if (!window.isPremiumUser) return; /* same */ }
async function downloadDOCX() { if (!window.isPremiumUser) return; /* same */ }
