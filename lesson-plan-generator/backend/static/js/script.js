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

if (lessonForm) {
  lessonForm.addEventListener('submit', (e) => {
    e.preventDefault();
    generateLessonPlan();
  });
}

// ========== FETCH  ==========
async function fetchData(endpoint, params = {}) {
  const url = new URL(`${API_BASE}/${endpoint}/`);
  Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, v));

  const res = await fetch(url, {
    headers: { 'Accept': 'application/json' }
  });

  if (!res.ok) throw new Error('API error');
  return await res.json();
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
async function requirePremium(action) {
  try {
    const deviceId = getDeviceId();
    const res = await fetch(`/api/check-subscription/?device_id=${deviceId}`);
    const data = await res.json();

    if (!data.active) {
      document.getElementById('subscribeModal').style.display = 'block';
      return;
    }

    action();
  } catch (err) {
    alert("Unable to verify subscription. Please check your connection.");
    console.error(err);
  }
}

// ------------------------
// Subscribe function
// ------------------------
async function subscribe(plan) {
  try {
    const deviceId = getDeviceId();
    const phone = prompt("Enter MTN MoMo number (e.g. 25078xxxxxxx)");

    const res = await fetch('/api/initiate-mtn-payment/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        device_id: deviceId,
        plan: plan,
        phone: phone
      })
    });

    const data = await res.json();

    if (data.reference_id) {
      alert("✅ Payment request sent. Approve on your phone.");
      console.log("Reference ID:", data.reference_id);

      // Optionally: start polling to check if subscription activated
      pollSubscription(deviceId, plan);
    } else {
      alert("❌ Payment initiation failed.");
    }
  } catch (err) {
    console.error(err);
    alert("❌ Unable to initiate payment. Check your connection.");
  }
}

async function pollSubscription(deviceId, plan) {
  const interval = setInterval(async () => {
    const res = await fetch(`/api/check-subscription/?device_id=${deviceId}`);
    const data = await res.json();

    if (data.active) {
      clearInterval(interval);
      alert(`✅ Subscription for ${plan} activated!`);
      window.isPremiumUser = true;
      document.getElementById('subscribeModal').style.display = 'none';
    }
  }, 5000); // check every 5 seconds
}


function copyToWord() {
  /* existing logic only */
}

function downloadPDF() {
  /* existing logic only */
}

async function downloadDOCX() {
  /* existing logic only */
}


function getDeviceId() {
  let id = localStorage.getItem('cbc_device_id');
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem('cbc_device_id', id);
  }
  return id;
}


