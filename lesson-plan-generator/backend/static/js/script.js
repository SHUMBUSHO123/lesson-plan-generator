// File: /lesson-plan-generator/backend/static/js/script.js

// ========== CONFIG ==========
const API_BASE = window.location.origin + "/api";

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

// ========== INIT ==========
document.addEventListener("DOMContentLoaded", () => {
    if (levelSelect) loadLevels();
    attachGenerateButton();
    attachPayButton();
});

// ========== ATTACH BUTTONS ==========
function attachGenerateButton() {
    const btn = document.getElementById('generateButton');
    if (btn) {
        btn.addEventListener('click', () => {
            requirePremium(() => generateLessonPlanFromForm());
        });
    }
}

function attachPayButton() {
    const payBtn = document.getElementById('payButton');
    if (payBtn) {
        payBtn.addEventListener('click', (e) => {
            e.preventDefault();
            subscribeFromPage();
        });
    }
}

// ========== EVENT LISTENERS ==========
if (levelSelect) levelSelect.addEventListener('change', () => {
    resetBelow('level');
    if (levelSelect.value) loadClasses(levelSelect.value);
});

if (classSelect) classSelect.addEventListener('change', () => {
    resetBelow('class');
    if (classSelect.value) loadSubjects(classSelect.value);
});

if (subjectSelect) subjectSelect.addEventListener('change', () => {
    resetBelow('subject');
    if (subjectSelect.value) loadUnits(subjectSelect.value);
});

if (unitSelect) unitSelect.addEventListener('change', () => {
    resetBelow('unit');
    if (unitSelect.value) {
        const selected = unitSelect.selectedOptions[0];
        document.getElementById('unitTitle').value = selected.dataset.title || '';
        document.getElementById('totalLessons').value = selected.dataset.total || '';
        loadLessons(unitSelect.value);
    }
});

// ========== FETCH HELPER ==========
async function fetchData(endpoint, params = {}) {
    const url = new URL(`${API_BASE}/${endpoint}/`);
    Object.entries(params).forEach(([k,v]) => url.searchParams.append(k,v));
    try {
        const res = await fetch(url, { headers: { 'Accept': 'application/json' }});
        if (!res.ok) throw new Error(`API error ${res.status}`);
        return await res.json();
    } catch (err) {
        console.error("Fetch failed:", url.toString(), err);
        throw err;
    }
}

// ========== RESET HELPERS ==========
function resetBelow(level) {
    if (level === 'level') classSelect.innerHTML = `<option value="">Select Class</option>`;
    if (['level','class'].includes(level)) subjectSelect.innerHTML = `<option value="">Select Subject</option>`;
    if (['level','class','subject'].includes(level)) unitSelect.innerHTML = `<option value="">Select Unit</option>`;
    if (['level','class','subject','unit'].includes(level)) lessonSelect.innerHTML = `<option value="">Select Lesson</option>`;
}

// ========== DROPDOWN LOADERS ==========
async function loadLevels() {
    const levels = await fetchData('levels');
    levelSelect.innerHTML = `<option value="">Select Level</option>`;
    levels.forEach(l => levelSelect.innerHTML += `<option value="${l.id}">${l.name}</option>`);
}

async function loadClasses(levelId) {
    const classes = await fetchData('classes', { level_id: levelId });
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

async function loadLessons(unitId) {
    const lessons = await fetchData('lessons', { unit_id: unitId });
    lessonSelect.innerHTML = `<option value="">Select Lesson</option>`;
    lessons.forEach(l => lessonSelect.innerHTML += `<option value="${l.id}">${l.title}</option>`);
}

// ========== FORM DATA ==========
function getFormData() {
    return {
        level: levelSelect.options[levelSelect.selectedIndex].text,
        className: classSelect.options[classSelect.selectedIndex].text,
        subject: subjectSelect.options[subjectSelect.selectedIndex].text,
        unitTitle: document.getElementById('unitTitle').value,
        totalLessons: parseInt(document.getElementById('totalLessons').value || '0'),
        lessonTitle: lessonSelect.options[lessonSelect.selectedIndex].text
    };
}

function calculateTiming(total) {
    const timePerLesson = 40;
    return Array.from({length: total}, (_, i) => {
        const start = i * timePerLesson;
        const hours = Math.floor(start / 60);
        const minutes = start % 60;
        return `${hours}:${minutes.toString().padStart(2,'0')} - ${hours}:${(minutes+timePerLesson).toString().padStart(2,'0')}`;
    });
}

// ========== LESSON PLAN GENERATION ==========
async function generateLessonPlanFromForm() {
    const data = getFormData();
    if (!data.level || !data.className || !data.subject || !data.unitTitle || !data.totalLessons) {
        alert("Please fill all required fields!");
        return;
    }

    try {
        const deviceId = getDeviceId();
        const res = await fetch('/api/generate_lesson_plan/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId })
        });
        const apiData = await res.json();

        if (!res.ok) {
            alert(apiData.error || "Unable to generate lesson plan. Please try again.");
            return;
        }

        // Build UI
        lessonPlanContent.innerHTML = '';
        lessonPlanContent.appendChild(buildHeader(data));
        lessonPlanContent.appendChild(buildLessonInfoTable(data));
        lessonPlanContent.appendChild(buildUnitTable(data));
        lessonPlanContent.appendChild(buildSteps(data, calculateTiming(data.totalLessons)));
        resultContainer.classList.add('show');

    } catch (err) {
        console.error(err);
        alert("Unable to generate lesson plan. Check your connection.");
    }
}

// ========== UI BUILDERS ==========
function buildHeader(d) {
    const div = document.createElement('div');
    div.className = 'lesson-plan-header text-center';
    div.innerHTML = `<h2>${d.subject} - ${d.unitTitle}</h2><p>${d.level} | ${d.className}</p>`;
    return div;
}

function buildLessonInfoTable(d) {
    const table = document.createElement('table');
    table.className = 'lesson-plan';
    table.innerHTML = `
        <tr><td class="bold">Lesson Title</td><td>${d.lessonTitle}</td></tr>
        <tr><td class="bold">Unit</td><td>${d.unitTitle}</td></tr>
        <tr><td class="bold">Class / Level</td><td>${d.className} / ${d.level}</td></tr>
        <tr><td class="bold">Total Lessons</td><td>${d.totalLessons}</td></tr>
    `;
    return table;
}

function buildUnitTable(d) {
    const table = document.createElement('table');
    table.className = 'lesson-plan';
    table.innerHTML = `
        <tr><td class="bold">Unit Title</td><td>${d.unitTitle}</td></tr>
        <tr><td class="bold">Number of Lessons</td><td>${d.totalLessons}</td></tr>
    `;
    return table;
}

function buildSteps(d, timings) {
    const container = document.createElement('div');
    container.className = 'lesson-steps';
    const ul = document.createElement('ul');
    for (let i=1;i<=d.totalLessons;i++) ul.appendChild(step(`Lesson ${i}`, timings[i-1]));
    container.appendChild(ul);
    return container;
}

function step(name,time) {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${name}</strong> — <em>${time}</em>`;
    return li;
}

// ========== DEVICE / USER TRACKING ==========
function getDeviceId() {
    let id = localStorage.getItem('cbc_device_id');
    if (!id) {
        id = crypto.randomUUID();
        localStorage.setItem('cbc_device_id', id);
    }
    return id;
}

// ========== PREMIUM / SUBSCRIPTION ==========
async function requirePremium(action) {
    try {
        const deviceId = getDeviceId();
        const maxFreePlans = 3;

        const subRes = await fetch(`/api/check-subscription/?device_id=${deviceId}`);
        const subData = await subRes.json();

        if (subData.active) {
            action();
            return;
        }

        // Increment free plan usage
        const planRes = await fetch("/api/increment_free_plan/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ device_id: deviceId })
        });
        const planData = await planRes.json();

        if (planData.free_plans_used < maxFreePlans) {
            action();
        } else {
            alert("Free lesson plan limit reached. Please subscribe.");
            window.location.href = "/payment/";
        }

    } catch (err) {
        console.error(err);
        alert("Unable to verify subscription. Check your connection.");
    }
}

// ========== MTN PAYMENT ==========
async function subscribeFromPage() {
    const deviceId = getDeviceId();
    const plan = document.getElementById('planSelect').value;
    const phone = document.getElementById('phoneInput').value.trim();
    const termsChecked = document.getElementById('termsCheck').checked;
    const statusEl = document.getElementById('paymentStatus');
    statusEl.textContent = '';
    statusEl.className = 'status-message text-muted';

    if (!plan) { statusEl.textContent='❌ Select a plan'; statusEl.classList.add('text-danger'); return; }
    if (!phone.match(/^2507\d{8}$/)) { statusEl.textContent='❌ Invalid MTN MoMo number'; statusEl.classList.add('text-danger'); return; }
    if (!termsChecked) { statusEl.textContent='❌ Accept Terms & Conditions'; statusEl.classList.add('text-danger'); return; }

    try {
        statusEl.textContent = '⏳ Sending payment request...';
        statusEl.className = 'status-message text-info';
        const res = await fetch('/api/initiate-mtn-payment/', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ device_id: deviceId, plan: plan, phone: phone })
        });
        const data = await res.json();
        if (res.ok && data.reference_id) {
            statusEl.textContent='✅ Payment request sent. Approve on MTN MoMo app';
            statusEl.className='status-message text-success';
            pollSubscriptionFromPage(deviceId, plan);
        } else {
            statusEl.textContent=`❌ Payment failed: ${data.error||'Unknown'}`;
            statusEl.className='status-message text-danger';
        }
    } catch(e) {
        console.error(e);
        statusEl.textContent='❌ Unable to initiate payment';
        statusEl.className='status-message text-danger';
    }
}

async function pollSubscriptionFromPage(deviceId, plan) {
    const statusEl = document.getElementById('paymentStatus');
    const interval = setInterval(async () => {
        try {
            const res = await fetch(`/api/check-subscription/?device_id=${deviceId}`);
            const data = await res.json();
            if (data.active) {
                clearInterval(interval);
                statusEl.textContent=`✅ Subscription "${plan}" activated! Enjoy premium features.`;
                statusEl.className='status-message text-success';
                window.isPremiumUser = true;
            } else {
                statusEl.textContent='⏳ Waiting for payment confirmation...';
                statusEl.className='status-message text-info';
            }
        } catch(err) {
            console.error(err);
            statusEl.textContent='❌ Error checking subscription. Retrying...';
            statusEl.className='status-message text-warning';
        }
    },5000);
}
