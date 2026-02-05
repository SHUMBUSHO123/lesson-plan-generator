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
    prefillUserData(); // <-- this triggers the auto-fill
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
        // Existing dropdown selections
        level: levelSelect.options[levelSelect.selectedIndex].text,
        className: classSelect.options[classSelect.selectedIndex].text,
        subject: subjectSelect.options[subjectSelect.selectedIndex].text,
        unitTitle: document.getElementById('unitTitle').value,
        totalLessons: parseInt(document.getElementById('totalLessons').value || '0'),
        lessonTitle: lessonSelect.options[lessonSelect.selectedIndex].text,
        lessonNumber: parseInt(document.getElementById('lessonNo')?.value || '1'),
        durationMinutes: parseInt(document.getElementById('duration')?.value || '40'),

        // Prefill fields
        schoolName: document.getElementById('schoolName')?.value || '',
        teacherName: document.getElementById('teacherName')?.value || '',
        term: document.getElementById('term')?.value || '',
        classSize: document.getElementById('classSize')?.value || '',
        references: document.getElementById('references')?.value || '',
        specialNeeds: document.getElementById('specialNeeds')?.value || ''
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

// ===============================
// Prefill User Data
// ===============================
async function prefillUserData() {
    try {
        const deviceId = getDeviceId(); // uses existing function
        const url = `/api/get_user_prefill/?device_id=${deviceId}`;
        const res = await fetch(url, { headers: { 'Accept': 'application/json' }});
        if (!res.ok) throw new Error(`Failed to fetch prefill data: ${res.status}`);
        const data = await res.json();

        // Fill form inputs
        const schoolInput = document.getElementById('schoolName');
        const teacherInput = document.getElementById('teacherName');
        const termInput = document.getElementById('term');
        const classSizeInput = document.getElementById('classSize');
        const referencesInput = document.getElementById('references');

        if (schoolInput) schoolInput.value = data.schoolName || '';
        if (teacherInput) teacherInput.value = data.teacherName || '';
        if (termInput) termInput.value = data.term || '';
        if (classSizeInput) classSizeInput.value = data.classSize || '';
        if (referencesInput) referencesInput.value = data.references || '';

    } catch (err) {
        console.error("Prefill failed:", err);
    }
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
        if (!deviceId) {
            alert("Device ID missing. Cannot verify subscription.");
            return;
        }

        const maxFreePlans = 3;

        // 1️⃣ Check subscription status
        const subRes = await fetch(`/api/check-subscription/?device_id=${deviceId}`);
        const subData = await subRes.json();

        if (subData.active) {
            action(); // premium active → proceed
            return;
        }

        // 2️⃣ Increment free plan usage
        const planRes = await fetch("/api/increment_free_plan/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ device_id: deviceId })
        });

        const planData = await planRes.json();

        // 3️⃣ Decide if user can generate lesson plan
        if (planData.free_plans_used < maxFreePlans) {
            action(); // still under free plan limit → proceed
        } else {
            alert("Free lesson plan limit reached. Please subscribe.");
            window.location.href = "/payment/";
        }

    } catch (err) {
        console.error("requirePremium error:", err);
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

async function generateLessonPlanFromForm() {
    const formData = getFormData();
    if (!formData.level || !formData.className || !formData.subject || !formData.unitTitle || !formData.totalLessons || !lessonSelect.value) {
        alert("Please fill all required fields!");
        return;
    }

    try {
        const deviceId = getDeviceId();

        // Build payload for backend
const payload = {
    device_id: deviceId,
    level: formData.level,
    class: formData.className,
    subject: formData.subject,
    unit_id: unitSelect.value,
    lesson_id: lessonSelect.value,
    school_name: formData.schoolName,
    teacher_name: formData.teacherName,
    term: formData.term,
    class_size: formData.classSize,
    lesson_no: document.getElementById('lessonNo').value || 1,          // <-- matches view
    total_lessons: document.getElementById('totalLessons').value || 1,   // <-- same
    duration: document.getElementById('duration').value || 40,           // <-- matches view
    specialNeeds: document.getElementById('specialNeeds').value || '',   // <-- matches view
    references: document.getElementById('references').value || ''
};


        const res = await fetch('/api/generate_lesson_plan/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const apiData = await res.json();

        if (!res.ok) {
            alert(apiData.error || "Unable to generate lesson plan. Please try again.");
            return;
        }
        console.log("HTML from backend:", apiData.html.substring(0, 200));

        // Use API response to render
        lessonPlanContent.textContent = '';
        lessonPlanContent.innerHTML = apiData.html;
        console.log(apiData.html);

        resultContainer.classList.add('show');

    } catch (err) {
        console.error(err);
        alert("Unable to generate lesson plan. Check your connection.");
    }
}
