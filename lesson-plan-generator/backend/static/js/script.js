// ===============================
// CONFIG & DOM ELEMENTS
// ===============================
const API_BASE = window.location.origin + "/api";

// ✅ Store CSRF token once at page load to prevent repeated DOM queries
window.CSRF_TOKEN = document.querySelector('[name=csrfmiddlewaretoken]')?.value || null;
if (!window.CSRF_TOKEN) {
    console.warn("CSRF token not found on page. POST requests may fail!");
}

const lessonForm = document.getElementById('lessonForm');
const lessonPlanContent = document.getElementById('lessonPlanContent');
document.getElementById('lessonPlanContent')


const levelSelect = document.getElementById('level');
const classSelect = document.getElementById('className');
const subjectSelect = document.getElementById('subject');
const unitSelect = document.getElementById('unitNo');
const lessonSelect = document.getElementById('lessonTitle');

// ===============================
// STATE & CACHE
// ===============================
let accessCache = null;
let generateListenerAttached = false;

// ===============================
// INIT
// ===============================
document.addEventListener("DOMContentLoaded", async () => {
    if(levelSelect) loadLevels();
    attachGenerateButton();
    attachPayButton();
    prefillUserData();
    updateGenerateButtonStatus();
});

// ===============================
// FETCH HELPERS
// ===============================
async function fetchData(endpoint, params={}) {
    const url = new URL(`${API_BASE}/${endpoint}/`);
    Object.entries(params).forEach(([k,v]) => url.searchParams.append(k,v));
    const res = await fetch(url, { headers: {'Accept':'application/json'}, credentials: 'include' });
    if(!res.ok) throw new Error(`API error ${res.status}`);
    return await res.json();
}

async function postData(endpoint, payload = {}) {
    // ✅ Use stored CSRF token to avoid repeated DOM lookups
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.CSRF_TOKEN;

    if (!csrfToken) {
        console.error("CSRF token missing! POST request may fail.");
        alert("CSRF token missing. Please refresh the page and try again.");
        return { ok: false, data: { error: "CSRF token missing" } };
    }

    try {
        const res = await fetch(`${API_BASE}/${endpoint}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(payload),
            credentials: 'include'
        });

        const data = await res.json();
        return { ok: res.ok, data };
    } catch (err) {
        console.error("POST request failed:", err);
        return { ok: false, data: { error: err.message } };
    }
}

// ===============================
// DROPDOWN RESET & LOADERS
// ===============================
function resetBelow(level) {
    if(level==='level') classSelect.innerHTML = `<option value="">Select Class</option>`;
    if(['level','class'].includes(level)) subjectSelect.innerHTML = `<option value="">Select Subject</option>`;
    if(['level','class','subject'].includes(level)) unitSelect.innerHTML = `<option value="">Select Unit</option>`;
    if(['level','class','subject','unit'].includes(level)) lessonSelect.innerHTML = `<option value="">Select Lesson</option>`;
}

async function loadLevels() {
    const levels = await fetchData('levels') || [];
    levelSelect.innerHTML = `<option value="">Select Level</option>`;
    levels.forEach(l => levelSelect.innerHTML += `<option value="${l.id}">${l.name}</option>`);
}

async function loadClasses(levelId) {
    classSelect.innerHTML = `<option value="">Loading...</option>`;
    const classes = await fetchData('classes',{level_id: levelId}) || [];
    classSelect.innerHTML = `<option value="">Select Class</option>`;
    classes.forEach(c => classSelect.innerHTML += `<option value="${c.id}">${c.name}</option>`);
}

async function loadSubjects(classId) {
    subjectSelect.innerHTML = `<option value="">Loading...</option>`;
    const subjects = await fetchData('subjects',{class_id: classId}) || [];
    subjectSelect.innerHTML = `<option value="">Select Subject</option>`;
    subjects.forEach(s => subjectSelect.innerHTML += `<option value="${s.id}">${s.name}</option>`);
}

async function loadUnits(subjectId) {
    unitSelect.innerHTML = `<option value="">Loading...</option>`;
    const units = await fetchData('units',{subject_id: subjectId}) || [];
    unitSelect.innerHTML = `<option value="">Select Unit</option>`;
    units.forEach(u => unitSelect.innerHTML += `<option value="${u.id}" data-title="${u.title}" data-total="${u.total_lessons}">Unit ${u.number} - ${u.title}</option>`);
}

async function loadLessons(unitId) {
    lessonSelect.innerHTML = `<option value="">Loading...</option>`;
    const lessons = await fetchData('lessons',{unit_id: unitId}) || [];
    lessonSelect.innerHTML = `<option value="">Select Lesson</option>`;
    lessons.forEach(l => lessonSelect.innerHTML += `<option value="${l.id}">${l.title}</option>`);
}

// ===============================
// EVENT LISTENERS
// ===============================
if(levelSelect) levelSelect.addEventListener('change',()=>{ resetBelow('level'); if(levelSelect.value) loadClasses(levelSelect.value); });
if(classSelect) classSelect.addEventListener('change',()=>{ resetBelow('class'); if(classSelect.value) loadSubjects(classSelect.value); });
if(subjectSelect) subjectSelect.addEventListener('change',()=>{ resetBelow('subject'); if(subjectSelect.value) loadUnits(subjectSelect.value); });
if(unitSelect) unitSelect.addEventListener('change',()=>{
    resetBelow('unit');
    if(unitSelect.value){
        const selected = unitSelect.selectedOptions[0];
        document.getElementById('unitTitle').value = selected.dataset.title || '';
        document.getElementById('totalLessons').value = selected.dataset.total || '';
        loadLessons(unitSelect.value);
    }
});

// ===============================
// FORM DATA
// ===============================
function getFormData(){
    return {
        level: levelSelect.options[levelSelect.selectedIndex].text,
        className: classSelect.options[classSelect.selectedIndex].text,
        subject: subjectSelect.options[subjectSelect.selectedIndex].text,
        unitTitle: document.getElementById('unitTitle').value,
        totalLessons: parseInt(document.getElementById('totalLessons').value||'0'),
        lessonTitle: lessonSelect.options[lessonSelect.selectedIndex].text,
        lessonNumber: parseInt(document.getElementById('lessonNo')?.value||'1'),
        durationMinutes: parseInt(document.getElementById('duration')?.value||'40'),
        schoolName: document.getElementById('schoolName')?.value||'',
        teacherName: document.getElementById('teacherName')?.value||'',
        term: document.getElementById('term')?.value||'',
        classSize: document.getElementById('classSize')?.value||'',
        references: document.getElementById('references')?.value||'',
        specialNeeds: document.getElementById('specialNeeds')?.value||'',
        strategy: document.getElementById('strategy')?.value || ''
    };
}

// ===============================
// PREFILL USER DATA
// ===============================
async function prefillUserData() {
    try {
        const res = await fetch(`${API_BASE}/get_user_prefill/`, { credentials: 'include' });
        if (!res.ok) throw new Error(`Failed to fetch prefill data: ${res.status}`);
        const data = await res.json();

        ['schoolName', 'teacherName', 'term', 'classSize', 'references'].forEach(f => {
            const el = document.getElementById(f);
            if (el) el.value = data[f] || '';
        });

        if (data.unitTitle) document.getElementById('unitTitle').value = data.unitTitle;
        if (data.totalLessons) document.getElementById('totalLessons').value = data.totalLessons;
        if (data.lessonTitle) lessonSelect.value = data.lessonTitle;

    } catch (err) {
        console.error("Prefill failed:", err);
    }
}

// ===============================
// ACCESS CHECK / PREMIUM
// ===============================
async function checkAccess() {
    if(accessCache) return accessCache;
    try {
        const res = await fetch(`${API_BASE}/check-access/`, { credentials: 'include' });
        const data = await res.json();
        if(!res.ok) throw new Error(data.message || "Access check failed");
        accessCache = data;
        return data;
    } catch(err){
        console.error("Access check error:", err);
        return {is_premium:false, can_generate:true};
    }
}

// ===============================
// UPDATE GENERATE BUTTON STATUS
// ===============================
async function updateGenerateButtonStatus() {
    const btn = document.getElementById('generateButton');
    if (!btn) return;

    btn.disabled = true; // temporarily disable during check
    btn.title = "Checking access...";

    try {
        const data = await checkAccess();
        btn.disabled = !(data.is_premium || data.can_generate);
        btn.title = btn.disabled ? "Subscribe to unlock more lesson plans" : "";
    } catch (err) {
        console.error("Failed to update button status:", err);
        btn.disabled = true;
        btn.title = "Error checking access";
    }
}

// ===============================
// REQUIRE PREMIUM / ACCESS CHECK
// ===============================
// ===============================
// REQUIRE PREMIUM / ACCESS CHECK
// ===============================
async function requirePremium(action, allowFree = false) {
    try {
        const data = await checkAccess();

        if (data.is_premium) {
            // ✅ Premium → allow all actions
            action();
        } else if (allowFree && data.can_generate) {
            // ✅ Free user → allow generate action, increment free plan
            action();
            await fetch("/increment_free_plan/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": window.CSRF_TOKEN
                },
                body: JSON.stringify({ device_id: getDeviceId() })
            });
        } else {
            // ❌ Exceeded free limit → show paywall modal instead of redirect
            const modal = document.getElementById("subscribeModal");
            if (modal) modal.style.display = "flex";
        }

    } catch (err) {
        console.error("Access check failed:", err);
        alert("Unable to verify subscription. Please try again.");
    }
}


function closeModal() {
    const modal = document.getElementById('subscribeModal');
    if(modal) modal.style.display = 'none';
}



// ===============================
// GENERATE LESSON PLAN
// ===============================
async function generateLessonPlanFromForm() {
    const formData = getFormData();
    if (!unitSelect.value || !lessonSelect.value) {
        alert("Please fill all required fields!");
        return;
    }

    const btn = document.getElementById('generateButton');
    if (btn) btn.disabled = true; // Disable button during fetch

    // ✅ Wrap the main action in requirePremium
    await requirePremium(async () => {
        try {
            lessonPlanContent.textContent = 'Generating lesson plan...'; // Loading feedback

            const payload = {
                device_id: getDeviceId(),

                level: levelSelect.options[levelSelect.selectedIndex].text,
                class: classSelect.options[classSelect.selectedIndex].text,
                subject: subjectSelect.options[subjectSelect.selectedIndex].text,

                unit_id: unitSelect.value,
                lesson_id: lessonSelect.value,

                lesson_no: parseInt(document.getElementById('lessonNo')?.value || '1'),
                duration: parseInt(document.getElementById('duration')?.value || '40'),
                class_size: document.getElementById('classSize')?.value || '',

                school_name: document.getElementById('schoolName')?.value || '',
                teacher_name: document.getElementById('teacherName')?.value || '',
                term: document.getElementById('term')?.value || '',
                references: document.getElementById('references')?.value || '',
                special_needs: document.getElementById('specialNeeds')?.value || '',
                strategy: document.getElementById('strategy')?.value || '',
                location_plan: document.getElementById('locationPlan')?.value || '',
                materials: Array.from(
                    document.getElementById('materials')?.selectedOptions || []
                ).map(option => option.value).join(', ')
            };

            const { ok, data } = await postData('generate_lesson_plan', payload);

            if (!ok) {
                // ❌ Instead of redirect, show paywall modal if access denied
                if (data.redirect || data.error) {
                    const modal = document.getElementById("subscribeModal");
                    if (modal) modal.style.display = "flex";
                    lessonPlanContent.textContent = '';
                    return;
                }
            }

            // ✅ Success — render lesson plan
            lessonPlanContent.innerHTML = data.html;
            resultContainer.classList.add('show');

        } catch (err) {
            console.error(err);
            alert("Unable to generate lesson plan. Check connection.");
            lessonPlanContent.textContent = '';
        } finally {
            if (btn) btn.disabled = false;
        }
    }, true); // <-- allowFree = true for generate button
}

// ===============================
// DEVICE ID UTILITY
// ===============================
function getDeviceId(){
    if(window.userDeviceId) return window.userDeviceId;
    let id = localStorage.getItem('cbc_device_id');
    if(!id){ id = crypto.randomUUID(); localStorage.setItem('cbc_device_id', id); }
    window.userDeviceId = id;
    return id;
}

// ===============================
// BUTTON ATTACHERS
// ===============================
// Generate button → allow free users until limit
function attachGenerateButton(){
    const btn = document.getElementById('generateButton');
    if(btn && !generateListenerAttached){
        btn.addEventListener('click',()=>requirePremium(generateLessonPlanFromForm, true));
        generateListenerAttached = true;
    }
}

// Download/Copy buttons → only premium users
document.querySelectorAll('.download-buttons button').forEach(btn=>{
    const fnMap = {
        '📄 Copy to Word': copyToWord,
        '📑 Download PDF': downloadPDF,
        '📝 Download DOCX': downloadDOCX
    };
    const action = fnMap[btn.textContent.trim()];
    if(action) btn.addEventListener('click', ()=>requirePremium(action, false));
});

function attachPayButton(){
    const payBtn = document.getElementById('payButton');
    if(payBtn) payBtn.addEventListener('click', async (e)=>{ e.preventDefault(); subscribeFromPage?.(); });
}

// ===============================
// SUBSCRIPTION HANDLERS (ADD ONLY)
// ===============================
function subscribe(plan) {
    if(sessionStorage.getItem('submitting_plan')) return; // prevent double click
    sessionStorage.setItem('submitting_plan', 'true');
    sessionStorage.setItem('selected_plan', plan);
    window.location.href = "/pricing/";
}

function downloadPDF() {
    requirePremium(() => {
        const element = document.getElementById("lessonPlanContent");
        if (!element.innerHTML.trim()) {
            alert("Generate a lesson plan first.");
            return;
        }

        const opt = {
            margin: 0.5,
            filename: "CBC_Lesson_Plan.pdf",
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
        };

        html2pdf().set(opt).from(element).save();
    }, false); // allowFree = false → only premium can download
}

function copyToWord() {
    requirePremium(() => {
        const element = document.getElementById("lessonPlanContent");
        if (!element.innerHTML.trim()) {
            alert("Generate a lesson plan first.");
            return;
        }

        navigator.clipboard.writeText(element.innerText)
            .then(() => alert("Lesson copied! Paste into Microsoft Word."))
            .catch(() => alert("Copy failed."));
    }, false); // allowFree = false → only premium can copy
}

async function downloadWord() {
    await requirePremium(async () => {
        const element = document.getElementById("lessonPlanContent");
        if (!element.innerHTML.trim()) {
            alert("Generate a lesson plan first.");
            return;
        }

        const content = element.innerText;
        const blob = new Blob(
            ["\uFEFF" + content], 
            { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" }
        );

        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "CBC_Lesson_Plan.docx";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    }, false);
}
