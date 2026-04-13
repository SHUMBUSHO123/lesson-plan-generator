// ===============================
// CONFIG & DOM ELEMENTS
// ===============================
const API_BASE = window.location.origin + "/api";

window.CSRF_TOKEN = document.querySelector('[name=csrfmiddlewaretoken]')?.value || null;
if (!window.CSRF_TOKEN) {
    console.warn("CSRF token not found on page. POST requests may fail!");
}

const lessonForm        = document.getElementById('lessonForm');
const lessonPlanContent = document.getElementById('lessonPlanContent');
const resultContainer   = document.getElementById('resultContainer');

const levelSelect    = document.getElementById('level');
const classSelect    = document.getElementById('className');
const subjectSelect  = document.getElementById('subject');
const unitSelect     = document.getElementById('unitNo');
const lessonSelect   = document.getElementById('lessonTitle');
const languageSelect = document.getElementById('language');

// ===============================
// STATE & CACHE
// ===============================
let accessCache              = null;
let generateListenerAttached = false;

// ===============================
// LANGUAGE HELPER
// ===============================
function getLanguage() {
    return languageSelect?.value || 'en';
}

// ===============================
// INIT
// ===============================
document.addEventListener("DOMContentLoaded", async () => {
    if (levelSelect) loadLevels();
    attachLanguageSelector();
    attachGenerateButton();
    attachPayButton();
    attachDownloadButtons();

    document.querySelectorAll('input, select').forEach(el => {
        el.addEventListener('change', () => el.classList.remove('field-error'));
        el.addEventListener('input',  () => el.classList.remove('field-error'));
    });

    if (window.__DASHBOARD__) {
        renderDashboard(window.__DASHBOARD__);
    }

    await Promise.all([
        prefillUserData(),
        updateGenerateButtonStatus(),
    ]);
});

// ===============================
// LANGUAGE SELECTOR
// ===============================
function attachLanguageSelector() {
    if (!languageSelect) return;
    languageSelect.addEventListener('change', () => {
        resetBelow('level');
        loadLevels();
    });
}

// ===============================
// FETCH HELPERS
// ===============================
async function fetchData(endpoint, params = {}) {
    const url = new URL(`${API_BASE}/${endpoint}/`);
    Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, v));
    const res = await fetch(url, {
        headers:     { 'Accept': 'application/json' },
        credentials: 'include',
    });
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return await res.json();
}

async function postData(endpoint, payload = {}) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
                      || window.CSRF_TOKEN;
    if (!csrfToken) {
        console.error("CSRF token missing!");
        alert("CSRF token missing. Please refresh the page and try again.");
        return { ok: false, data: { error: "CSRF token missing" } };
    }
    try {
        const res = await fetch(`${API_BASE}/${endpoint}/`, {
            method:      'POST',
            headers:     { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body:        JSON.stringify(payload),
            credentials: 'include',
        });
        const data = await res.json();
        return { ok: res.ok, data };
    } catch (err) {
        console.error("POST request failed:", err);
        return { ok: false, data: { error: err.message } };
    }
}

// ===============================
// SEN & REFERENCES — AGGREGATION
// ── FIX BUG 1: aggregateSEN reads live checkboxes every call.
//    window.getSENValue / window.getRefsValue are aliases for
//    index.html inline scripts to call.
// ===============================
function aggregateSEN() {
    const parts = [];
    document.querySelectorAll('input[name="sen"]:checked').forEach(cb => {
        if (cb.value === 'none') {
            parts.push(window.uiT ? window.uiT('sen_none') : 'None identified');
        } else if (cb.value !== 'custom') {
            const keyMap = {
                visual:   'sen_visual',
                hearing:  'sen_hearing',
                physical: 'sen_physical',
                learning: 'sen_learning',
                speech:   'sen_speech',
                gifted:   'sen_gifted',
            };
            const label   = window.uiT ? window.uiT(keyMap[cb.value]) : cb.value;
            const countEl = document.getElementById('sen_' + cb.value + '_count');
            const n       = countEl?.value ? ' (' + countEl.value + ')' : '';
            parts.push(label + n);
        }
    });
    // Always append free-text SEN if filled
    const senFree = document.getElementById('specialNeeds')?.value.trim();
    if (senFree) parts.push(senFree);

    const result = parts.join('; ');
    const agg    = document.getElementById('specialNeedsAggregated');
    if (agg) agg.value = result;
    return result;
}

function aggregateRefs() {
    const parts = [];
    document.querySelectorAll('input[name="ref"]:checked').forEach(cb => {
        if (cb.value !== 'custom') parts.push(cb.value);
    });
    const refFree = document.getElementById('references')?.value.trim();
    if (refFree) parts.push(refFree);

    const result = parts.join('; ');
    const agg    = document.getElementById('referencesAggregated');
    if (agg) agg.value = result;
    return result;
}

// Expose globally for index.html inline event wiring
window.getSENValue  = aggregateSEN;
window.getRefsValue = aggregateRefs;

// ===============================
// SHARED DOWNLOAD PAYLOAD
// ── FIX BUG 1: special_needs always fresh from live checkboxes
// ── FIX BUG 2: unit_title reads .value directly (saveInlineEdit keeps it current)
// ── FIX BUG 4: restored unit_number_display key for backend template
// ── FIX BUG 5: prefillUserData restores references prefill
// ===============================
function buildDownloadPayload() {

    // Helper: display override beats select visible text
    // Used for class, subject, level display labels
    function displayOf(el) {
        return el?.dataset?.displayOverride
            || el?.options?.[el?.selectedIndex]?.text
            || el?.value
            || '';
    }

    // Always aggregate fresh — never rely on hidden inputs alone
    const specialNeedsValue = aggregateSEN();
    const referencesValue   = aggregateRefs();

    return {
        language:      getLanguage(),
        device_id:     getDeviceId(),

        // ── Curriculum DB ids (used by backend for lesson lookup) ─────────
        unit_id:       unitSelect?.value   || '',
        lesson_id:     lessonSelect?.value || '',

        // ── Display values for the printed plan ───────────────────────────
        level:         displayOf(levelSelect),
        class:         displayOf(classSelect),
        subject:       displayOf(subjectSelect),

        // FIX BUG 4: unit_number_display was missing — backend needs this
        // to print the unit number in the plan header row.
        unit_number_display: displayOf(unitSelect),

        // FIX BUG 2: read .value directly — saveInlineEdit() keeps it current.
        // displayOverride is only set when teacher uses the edit badge, so
        // reading it first would miss the default value set by loadUnits().
        unit_title:    document.getElementById('unitTitle')?.value || '',

        // lesson_title: prefer override (teacher renamed it), else visible option text
        lesson_title:  document.getElementById('lessonTitle')?.dataset?.displayOverride
                       || lessonSelect?.options?.[lessonSelect?.selectedIndex]?.text
                       || '',

        // ── Numeric & scalar fields ───────────────────────────────────────
        lesson_no:     parseInt(document.getElementById('lessonNo')?.value     || '1'),
        total_lessons: parseInt(document.getElementById('totalLessons')?.value || '1'),
        duration:      parseInt(document.getElementById('duration')?.value     || '40'),
        class_size:    document.getElementById('classSize')?.value             || '',
        school_name:   document.getElementById('schoolName')?.value            || '',
        teacher_name:  document.getElementById('teacherName')?.value           || '',
        term:          document.getElementById('term')?.value                  || '',
        date:          document.getElementById('date')?.value                  || '',

        // ── FIX BUG 1: always-fresh SEN & References ─────────────────────
        special_needs: specialNeedsValue,
        references:    referencesValue,

        // ── Optional fields ───────────────────────────────────────────────
        strategy:      document.getElementById('strategy')?.value              || '',
        location_plan: document.getElementById('locationPlan')?.value          || '',

        // Multi-select: join all selected values with comma
        materials:     Array.from(
            document.getElementById('materials')?.selectedOptions || []
        ).map(o => o.value).join(', '),
    };
}

// ===============================
// DROPDOWN RESET & LOADERS
// ===============================
function resetBelow(level) {
    if (level === 'level')
        classSelect.innerHTML = `<option value="">Select Class</option>`;
    if (['level', 'class'].includes(level))
        subjectSelect.innerHTML = `<option value="">Select Subject</option>`;
    if (['level', 'class', 'subject'].includes(level))
        unitSelect.innerHTML = `<option value="">Select Unit</option>`;
    if (['level', 'class', 'subject', 'unit'].includes(level))
        lessonSelect.innerHTML = `<option value="">Select Lesson</option>`;
}

async function loadLevels() {
    const lang = getLanguage();
    const levels = await fetchData('levels', { lang }) || [];
    levelSelect.innerHTML = `<option value="">Select Level</option>`;
    levels.forEach(l => levelSelect.innerHTML +=
        `<option value="${l.id}">${l.name}</option>`);
}

async function loadClasses(levelId) {
    classSelect.innerHTML = `<option value="">Loading...</option>`;
    const classes = await fetchData('classes', { level_id: levelId }) || [];
    classSelect.innerHTML = `<option value="">Select Class</option>`;
    classes.forEach(c => classSelect.innerHTML +=
        `<option value="${c.id}">${c.name}</option>`);
}

async function loadSubjects(classId) {
    subjectSelect.innerHTML = `<option value="">Loading...</option>`;
    const lang     = getLanguage();
    const subjects = await fetchData('subjects', { class_id: classId, lang }) || [];
    subjectSelect.innerHTML = `<option value="">Select Subject</option>`;
    subjects.forEach(s => subjectSelect.innerHTML +=
        `<option value="${s.id}">${s.name}</option>`);
}

async function loadUnits(subjectId) {
    unitSelect.innerHTML = `<option value="">Loading...</option>`;
    const lang  = getLanguage();
    const units = await fetchData('units', { subject_id: subjectId, lang }) || [];
    unitSelect.innerHTML = `<option value="">Select Unit</option>`;
    units.forEach(u => unitSelect.innerHTML +=
        `<option value="${u.id}" data-title="${u.title}" data-total="${u.total_lessons}">Unit ${u.number} - ${u.title}</option>`);
}

async function loadLessons(unitId) {
    lessonSelect.innerHTML = `<option value="">Loading...</option>`;
    const lang    = getLanguage();
    const lessons = await fetchData('lessons', { unit_id: unitId, lang }) || [];
    lessonSelect.innerHTML = `<option value="">Select Lesson</option>`;
    lessons.forEach(l => lessonSelect.innerHTML +=
        `<option value="${l.id}">${l.title}</option>`);
}

// ===============================
// EVENT LISTENERS — DROPDOWNS
// ===============================
if (levelSelect) levelSelect.addEventListener('change', () => {
    resetBelow('level');
    if (classSelect) delete classSelect.dataset.displayOverride;
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
    // Clear lesson title override when unit changes
    const lt = document.getElementById('lessonTitle');
    if (lt) delete lt.dataset.displayOverride;

    if (unitSelect.value) {
        const selected = unitSelect.selectedOptions[0];
        document.getElementById('unitTitle').value    = selected.dataset.title || '';
        document.getElementById('totalLessons').value = selected.dataset.total || '';
        loadLessons(unitSelect.value);
    }
});

// ===============================
// EDITABLE FIELD HELPERS
// ── Single source of truth — NOT redefined in index.html.
//
// toggleEditField / saveEditField  → <select> fields (className, unitNo)
// toggleInlineEdit / saveInlineEdit → unitTitle <input> + lessonTitle <select>
//
// Contract: sel.value / main.value = DB id, NEVER changed.
//           dataset.displayOverride = teacher's printed label.
//           Visible option text is also renamed on save for immediate feedback.
// ===============================

window.toggleEditField = function(selectId, inputId, rowId, toggleId) {
    const sel    = document.getElementById(selectId);
    const row    = document.getElementById(rowId);
    const inp    = document.getElementById(inputId);
    const toggle = document.getElementById(toggleId);
    if (!sel || !row || !inp) return;

    const isHidden = row.style.display === 'none';
    if (isHidden) {
        row.style.display       = 'flex';
        inp.value               = sel.dataset.displayOverride
                                  || sel.options[sel.selectedIndex]?.text
                                  || '';
        sel.style.opacity       = '0.4';
        sel.style.pointerEvents = 'none';
        inp.focus();
        if (toggle) toggle.textContent = window.uiT
            ? '✖ ' + window.uiT('lbl_edit_hint').replace('✏ ', '')
            : '✖ cancel edit';
    } else {
        row.style.display       = 'none';
        sel.style.opacity       = '';
        sel.style.pointerEvents = '';
        if (toggle) toggle.textContent = window.uiT
            ? window.uiT('lbl_edit_hint')
            : '✏ editable';
    }
};

window.saveEditField = function(selectId, inputId, rowId, toggleId) {
    const sel    = document.getElementById(selectId);
    const row    = document.getElementById(rowId);
    const inp    = document.getElementById(inputId);
    const toggle = document.getElementById(toggleId);
    if (!sel || !inp) return;

    const newVal = inp.value.trim();
    if (newVal) {
        sel.dataset.displayOverride = newVal;
        // Visually rename the option so the dropdown shows the saved label
        const selectedOpt = sel.options[sel.selectedIndex];
        if (selectedOpt) {
            if (!selectedOpt.dataset.originalText)
                selectedOpt.dataset.originalText = selectedOpt.text;
            selectedOpt.text = newVal;
        }
    }

    if (row)  row.style.display  = 'none';
    sel.style.opacity       = '';
    sel.style.pointerEvents = '';
    if (toggle) toggle.textContent = window.uiT
        ? window.uiT('lbl_edit_hint')
        : '✏ editable';
};

window.toggleInlineEdit = function(mainId, editId, rowId, badgeId) {
    const main  = document.getElementById(mainId);
    const row   = document.getElementById(rowId);
    const edit  = document.getElementById(editId);
    const badge = document.getElementById(badgeId);
    if (!main || !row || !edit) return;

    const isHidden = row.style.display === 'none';
    if (isHidden) {
        row.style.display       = 'flex';
        edit.value = main.dataset.displayOverride
            || (main.tagName === 'SELECT'
                ? main.options[main.selectedIndex]?.text
                : main.value)
            || '';
        main.style.opacity       = '0.4';
        main.style.pointerEvents = 'none';
        edit.focus();
        if (badge) badge.textContent = window.uiT
            ? '✖ ' + window.uiT('lbl_edit_hint').replace('✏ ', '')
            : '✖ cancel';
    } else {
        row.style.display        = 'none';
        main.style.opacity       = '';
        main.style.pointerEvents = '';
        if (badge) badge.textContent = window.uiT
            ? window.uiT('lbl_edit_hint')
            : '✏ editable';
    }
};

window.saveInlineEdit = function(mainId, editId, rowId, badgeId) {
    const main  = document.getElementById(mainId);
    const row   = document.getElementById(rowId);
    const edit  = document.getElementById(editId);
    const badge = document.getElementById(badgeId);
    if (!main || !edit) return;

    const newVal = edit.value.trim();
    if (newVal) {
        main.dataset.displayOverride = newVal;

        if (main.tagName === 'SELECT') {
            const selectedOpt = main.options[main.selectedIndex];
            if (selectedOpt) {
                if (!selectedOpt.dataset.originalText)
                    selectedOpt.dataset.originalText = selectedOpt.text;
                selectedOpt.text = newVal;
            }
        } else {
            // FIX BUG 2: for plain <input> (unitTitle), update .value directly.
            // buildDownloadPayload() reads .value so this keeps it in sync.
            main.value = newVal;
        }
    }

    if (row)  row.style.display  = 'none';
    main.style.opacity       = '';
    main.style.pointerEvents = '';
    if (badge) badge.textContent = window.uiT
        ? window.uiT('lbl_edit_hint')
        : '✏ editable';
};

window.getFieldValue = function(selectId, inputId) {
    const sel = document.getElementById(selectId);
    if (sel?.dataset?.displayOverride) return sel.dataset.displayOverride;
    const inp = document.getElementById(inputId);
    if (inp && inp.closest('.edit-input-row')?.style.display !== 'none' && inp.value.trim())
        return inp.value.trim();
    return sel ? sel.value : '';
};

// ===============================
// FIELD VALIDATION
// ===============================
function highlightEmptyFields() {
    const required = [
        'schoolName', 'teacherName', 'term', 'date',
        'level', 'className', 'subject', 'unitNo',
        'lessonNo', 'totalLessons', 'duration',
        'classSize', 'unitTitle', 'lessonTitle',
    ];

    let hasEmpty = false;
    required.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        if (!el.value || el.value === '') {
            el.classList.add('field-error');
            hasEmpty = true;
        } else {
            el.classList.remove('field-error');
        }
    });

    if (hasEmpty) {
        const first = document.querySelector('.field-error');
        if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    return hasEmpty;
}

// ===============================
// PREFILL USER DATA
// ── FIX BUG 5: restored 'references' in prefill list (was dropped in dev)
// ===============================
async function prefillUserData() {
    try {
        const res = await fetch(`${API_BASE}/get_user_prefill/`, { credentials: 'include' });
        if (!res.ok) throw new Error(`Prefill failed: ${res.status}`);
        const data = await res.json();
        // Restored 'references' — was accidentally removed from dev version
        ['schoolName', 'teacherName', 'term', 'classSize', 'references'].forEach(f => {
            const el = document.getElementById(f);
            if (el) el.value = data[f] || '';
        });
        if (data.unitTitle)    document.getElementById('unitTitle').value    = data.unitTitle;
        if (data.totalLessons) document.getElementById('totalLessons').value = data.totalLessons;
        if (data.lessonTitle)  lessonSelect.value = data.lessonTitle;
    } catch (err) {
        console.error("Prefill failed:", err);
    }
}

// ===============================
// ACCESS CHECK
// ===============================
async function checkAccess(forceRefresh = false) {
    if (accessCache && !forceRefresh) return accessCache;
    try {
        const res  = await fetch(`${API_BASE}/check-access/`, { credentials: 'include' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.message || "Access check failed");
        accessCache = data;
        return data;
    } catch (err) {
        console.error("Access check error:", err);
        return { is_premium: false, can_generate: true };
    }
}

// ===============================
// GENERATE BUTTON STATUS
// ===============================
async function updateGenerateButtonStatus() {
    const btn = document.getElementById('generateButton');
    if (!btn) return;
    try {
        const data  = await checkAccess(true);
        const canGo = data.is_premium || data.can_generate;
        btn.disabled = false;
        if (!canGo) {
            btn.classList.add('btn-limit-reached');
            btn.title       = 'Limit reached — click to subscribe';
            btn.textContent = '🔒 Limit Reached — Subscribe to Continue';
        } else {
            btn.classList.remove('btn-limit-reached');
            btn.title       = '';
            btn.textContent = '✨ Generate Lesson Plan';
        }
    } catch (err) {
        console.error("Failed to update button status:", err);
        btn.disabled = false;
    }
}

// ===============================
// PAYWALL MODAL
// ===============================
function showPaywallModal() {
    const modal = document.getElementById('subscribeModal');
    if (!modal) return;

    const headerEl = modal.querySelector('.pricing-header');
    if (headerEl) {
        if (window.isAuthenticated) {
            headerEl.innerHTML = `
                <h1>🔒 Upgrade to Continue</h1>
                <h2>Upgrade to Keep Generating</h2>
                <p>Choose a plan below to unlock unlimited lesson plans and download features.</p>
            `;
        } else {
            headerEl.innerHTML = `
                <h1>🎓 Free Limit Reached (3 of 3 Used)</h1>
                <h2>Create a Free Account to Continue</h2>
                <p>
                    <a href="/register/" style="color:#4CAF50;font-weight:700;text-decoration:underline;">
                        Register for free
                    </a>
                    to get more lessons, or subscribe below to unlock unlimited access.
                </p>
            `;
        }
    }
    modal.style.display = 'flex';
}

async function requirePremium(action, allowFree = false) {
    try {
        const data = await checkAccess(true);
        if (data.is_premium) {
            action();
        } else if (allowFree && data.can_generate) {
            action();
        } else {
            showPaywallModal();
        }
    } catch (err) {
        console.error("Access check failed:", err);
        alert("Unable to verify subscription. Please try again.");
    }
}

function closeModal() {
    const modal = document.getElementById('subscribeModal');
    if (modal) modal.style.display = 'none';
}

// ===============================
// GENERATE LESSON PLAN
// ===============================
async function generateLessonPlanFromForm() {
    if (highlightEmptyFields()) {
        alert("Please fill in all highlighted fields!");
        return;
    }

    // Force-aggregate before payload build — belt and braces
    aggregateSEN();
    aggregateRefs();

    const btn = document.getElementById('generateButton');

    await requirePremium(async () => {
        if (btn) { btn.disabled = true; btn.textContent = '⏳ Generating...'; }

        try {
            lessonPlanContent.textContent = 'Generating lesson plan...';

            const { ok, data } = await postData('generate_lesson_plan', buildDownloadPayload());

            if (!ok) {
                if (data.redirect) {
                    showPaywallModal();
                    lessonPlanContent.textContent = '';
                    return;
                }
                if (data.error) {
                    alert("Server error: " + data.error);
                    lessonPlanContent.textContent = '';
                    return;
                }
            }

            lessonPlanContent.innerHTML = data.html;
            if (resultContainer) resultContainer.classList.add('show');
            loadDashboard();

        } catch (err) {
            console.error(err);
            alert("Unable to generate lesson plan. Check connection.");
            lessonPlanContent.textContent = '';
        } finally {
            if (btn) {
                btn.disabled = false;
                updateGenerateButtonStatus();
            }
        }
    }, true);
}

// ===============================
// DEVICE ID
// ===============================
function getDeviceId() {
    if (window.userDeviceId) return window.userDeviceId;
    let id = localStorage.getItem('cbc_device_id');
    if (!id) { id = crypto.randomUUID(); localStorage.setItem('cbc_device_id', id); }
    window.userDeviceId = id;
    return id;
}

// ===============================
// BUTTON ATTACHERS
// ===============================
function attachGenerateButton() {
    const btn = document.getElementById('generateButton');
    if (btn && !generateListenerAttached) {
        btn.addEventListener('click', generateLessonPlanFromForm);
        generateListenerAttached = true;
    }
}

function attachDownloadButtons() {
    document.querySelectorAll('.download-btn').forEach(btn => {
        const action = btn.dataset.action;
        btn.addEventListener('click', async (e) => {
            e.preventDefault();

            const element = document.getElementById("lessonPlanContent");
            if (!element || !element.innerHTML.trim()) {
                alert("Generate a lesson plan first.");
                return;
            }

            const originalText = btn.textContent;
            btn.disabled       = true;
            btn.textContent    = '⏳ Please wait...';

            try {
                const accessData = await checkAccess(true);
                if (accessData.is_premium) {
                    if (action === 'copy')       copyToWord();
                    else if (action === 'pdf')   await downloadPDF();
                    else if (action === 'word')  await downloadWord();
                } else {
                    showPaywallModal();
                }
            } catch (err) {
                console.error('Error checking access:', err);
                alert("Unable to verify subscription. Please try again.");
            } finally {
                btn.disabled    = false;
                btn.textContent = originalText;
            }
        });
    });
}

function attachPayButton() {
    const payBtn = document.getElementById('payButton');
    if (payBtn) payBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        subscribeFromPage?.();
    });
}

// ===============================
// SUBSCRIBE — fallback only
// ===============================
function subscribe(plan) {
    sessionStorage.setItem('selected_plan', plan);
    window.location.href = `/payment/?plan=${plan}`;
}

// ===============================
// DOWNLOAD — PDF
// ===============================
async function downloadPDF() {
    const element = document.getElementById("lessonPlanContent");
    if (!element || !element.innerHTML.trim()) { alert("Generate a lesson plan first."); return; }
    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.CSRF_TOKEN;
        const res = await fetch(`${API_BASE}/download_pdf/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            credentials: 'include',
            body: JSON.stringify(buildDownloadPayload()),
        });
        if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.error || `Server error ${res.status}`); }
        await triggerBlobDownload(await res.blob(), 'CBC_Lesson_Plan.pdf');
    } catch (err) {
        console.error('PDF download error:', err);
        alert('Failed to download PDF.\n\nError: ' + err.message);
    }
}

// ===============================
// DOWNLOAD — Word
// ===============================
async function downloadWord() {
    const element = document.getElementById("lessonPlanContent");
    if (!element || !element.innerHTML.trim()) { alert("Generate a lesson plan first."); return; }
    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.CSRF_TOKEN;
        const res = await fetch(`${API_BASE}/download_word/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            credentials: 'include',
            body: JSON.stringify(buildDownloadPayload()),
        });
        if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.error || `Server error ${res.status}`); }
        await triggerBlobDownload(await res.blob(), 'CBC_Lesson_Plan.docx');
    } catch (err) {
        console.error('Word download error:', err);
        alert('Failed to download Word document.\n\nError: ' + err.message);
    }
}

// ===============================
// DOWNLOAD — Copy to Word
// ===============================
function copyToWord() {
    const element = document.getElementById("lessonPlanContent");
    if (!element || !element.innerHTML.trim()) { alert("Generate a lesson plan first."); return; }
    const htmlContent = element.innerHTML;
    const plainText   = element.innerText;
    if (window.ClipboardItem && navigator.clipboard.write) {
        const item = new ClipboardItem({
            'text/html':  new Blob([htmlContent], { type: 'text/html' }),
            'text/plain': new Blob([plainText],   { type: 'text/plain' }),
        });
        navigator.clipboard.write([item])
            .then(() => alert("Lesson plan copied with formatting!\nOpen Microsoft Word and press Ctrl+V to paste."))
            .catch(() => fallbackCopyPlainText(plainText));
    } else {
        fallbackCopyPlainText(plainText);
    }
}

function fallbackCopyPlainText(text) {
    navigator.clipboard.writeText(text)
        .then(() => alert("Lesson plan copied (plain text).\nPaste into Microsoft Word — formatting may be limited."))
        .catch(() => alert("Copy failed. Please select the lesson plan text manually and use Ctrl+C."));
}

// ===============================
// SHARED BLOB DOWNLOAD HELPER
// ===============================
async function triggerBlobDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a   = document.createElement('a');
    a.href     = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1500);
}

// ===============================
// DASHBOARD
// ===============================
let dashboardData     = null;
let selectedPlanIds   = new Set();
let dashboardExpanded = true;

async function loadDashboard() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/`, {
            credentials: 'include',
            headers:     { 'Accept': 'application/json' },
        });
        if (!res.ok) return;
        dashboardData = await res.json();
        renderDashboard(dashboardData);
    } catch (err) {
        console.warn("Dashboard load skipped:", err.message);
    }
}

function renderDashboard(data) {
    const panel = document.getElementById('dashboardPanel');
    if (!panel) return;
    panel.style.display = 'block';
    if (!data.is_authenticated) { renderGuestBanner(data); } else { renderFullDashboard(data); }
    attachDashboardEvents();
}

function renderGuestBanner(data) {
    const banner = document.getElementById('guestBanner');
    if (!banner) return;
    banner.style.display = 'flex';
    const remaining = data.remaining ?? (data.lesson_limit - data.lessons_used);
    const text      = document.getElementById('guestBannerText');
    if (text) {
        if (remaining <= 0) {
            text.innerHTML = `<strong style="color:#f44336">Free limit reached (3 of 3 used).</strong>
                <a href="/register/" style="color:#4CAF50;font-weight:700;margin-left:6px;text-decoration:underline;">Create a free account</a>
                to get more lessons, or
                <a href="/pricing/" style="color:#2D9CDB;font-weight:700;margin-left:2px;text-decoration:underline;">subscribe for unlimited access.</a>`;
        } else {
            text.innerHTML = `You have <strong style="color:#4CAF50">${remaining}</strong> free lesson${remaining === 1 ? '' : 's'} remaining (${data.lessons_used} of ${data.lesson_limit} used).`;
        }
    }
}

function renderFullDashboard(data) {
    const fd = document.getElementById('fullDashboard');
    if (!fd) return;
    fd.style.display = 'block';

    const used  = data.lessons_used ?? 0;
    const limit = data.lesson_limit ?? 0;

    setInner('dashUsed', used);
    setInner('dashLimit', (data.remaining === null || data.remaining === undefined) ? 'Unlimited plan' : `of ${limit} total`);

    if (data.remaining === null || data.remaining === undefined) {
        setInner('dashRemaining', '∞'); setInner('dashRemainingLabel', 'unlimited');
    } else {
        setInner('dashRemaining', data.remaining);
        setInner('dashRemainingLabel', data.remaining === 1 ? 'lesson left' : 'lessons left');
    }

    const fill = document.getElementById('dashProgressFill');
    if (fill) {
        const pct = data.is_premium ? 100 : Math.min(100, limit > 0 ? Math.round((used / limit) * 100) : 0);
        fill.style.width      = `${pct}%`;
        fill.style.background = pct >= 90 ? 'linear-gradient(90deg,#f44336,#EF9A9A)' : 'linear-gradient(90deg,#4CAF50,#81C784)';
    }

    const planEl = document.getElementById('dashPlan');
    if (planEl) {
        if (data.is_premium && data.subscription_plan) { planEl.textContent = data.subscription_plan.charAt(0).toUpperCase() + data.subscription_plan.slice(1); planEl.style.color = '#81C784'; }
        else if (data.is_premium) { planEl.textContent = 'Premium'; planEl.style.color = '#81C784'; }
        else { planEl.textContent = 'Free'; planEl.style.color = '#FF9800'; }
    }

    const expiryEl = document.getElementById('dashExpiry');
    if (expiryEl) {
        if (data.subscription_expiry) { const d = new Date(data.subscription_expiry); expiryEl.textContent = `Expires: ${d.toLocaleDateString('en-GB', { day:'2-digit', month:'short', year:'numeric' })}`; }
        else if (data.is_premium) { expiryEl.textContent = 'No expiry set'; }
        else { expiryEl.textContent = 'Upgrade for more'; }
    }

    togglePerm('permPdf',  data.can_download_pdf);
    togglePerm('permDocx', data.can_download_docx);
    togglePerm('permCopy', data.can_copy_word);

    const hint = document.getElementById('dashUpgradeHint');
    if (hint && !data.is_premium) hint.innerHTML = `<a href="/pricing/" style="color:#4CAF50;font-size:11px;">Upgrade to unlock all →</a>`;

    renderPlansTable(data.recent_plans || []);
}

function renderPlansTable(plans) {
    const loading  = document.getElementById('dashLoading');
    const empty    = document.getElementById('dashEmpty');
    const tableWrp = document.getElementById('dashTableWrapper');
    const tbody    = document.getElementById('dashPlansBody');

    if (loading) loading.style.display = 'none';
    if (!plans || plans.length === 0) {
        if (empty)    empty.style.display    = 'block';
        if (tableWrp) tableWrp.style.display = 'none';
        return;
    }
    if (empty)    empty.style.display    = 'none';
    if (tableWrp) tableWrp.style.display = 'block';
    if (!tbody) return;

    tbody.innerHTML = plans.map(p => `
        <tr data-plan-id="${p.id}">
            <td><input type="checkbox" class="dash-plan-check" data-id="${p.id}" aria-label="Select ${escHtml(p.lesson_title)}"></td>
            <td><span class="dash-subject-badge">${escHtml(p.subject)}</span></td>
            <td class="dash-lesson-title-cell" title="${escHtml(p.lesson_title)}">${escHtml(p.lesson_title)}</td>
            <td>${escHtml(p.class_name)}</td>
            <td>${escHtml(p.term ? 'Term ' + p.term : '–')}</td>
            <td class="dash-date-cell">${escHtml(p.created_at)}</td>
        </tr>
    `).join('');

    tbody.querySelectorAll('.dash-plan-check').forEach(cb => cb.addEventListener('change', handlePlanCheckChange));
}

function attachDashboardEvents() {
    const collapseBtn = document.getElementById('dashCollapseBtn');
    if (collapseBtn) {
        collapseBtn.replaceWith(collapseBtn.cloneNode(true));
        document.getElementById('dashCollapseBtn').addEventListener('click', () => {
            dashboardExpanded = !dashboardExpanded;
            const body = document.getElementById('dashBody');
            if (body) body.classList.toggle('collapsed', !dashboardExpanded);
            const btn  = document.getElementById('dashCollapseBtn');
            btn.textContent = dashboardExpanded ? '▲' : '▼';
            btn.title       = dashboardExpanded ? 'Collapse dashboard' : 'Expand dashboard';
        });
    }

    const headerCheck = document.getElementById('dashHeaderCheck');
    if (headerCheck) {
        headerCheck.replaceWith(headerCheck.cloneNode(true));
        document.getElementById('dashHeaderCheck').addEventListener('change', (e) => {
            document.querySelectorAll('.dash-plan-check').forEach(cb => {
                cb.checked = e.target.checked;
                const id = parseInt(cb.dataset.id, 10);
                if (e.target.checked) selectedPlanIds.add(id); else selectedPlanIds.delete(id);
            });
            updateZipButton();
        });
    }

    const selectAllBtn = document.getElementById('dashSelectAll');
    if (selectAllBtn) {
        selectAllBtn.replaceWith(selectAllBtn.cloneNode(true));
        document.getElementById('dashSelectAll').addEventListener('click', () => {
            const checks     = document.querySelectorAll('.dash-plan-check');
            const allChecked = [...checks].every(cb => cb.checked);
            checks.forEach(cb => {
                cb.checked = !allChecked;
                const id = parseInt(cb.dataset.id, 10);
                if (!allChecked) selectedPlanIds.add(id); else selectedPlanIds.delete(id);
            });
            const hc = document.getElementById('dashHeaderCheck');
            if (hc) hc.checked = !allChecked;
            updateZipButton();
        });
    }

    const zipBtn = document.getElementById('dashZipBtn');
    if (zipBtn) {
        zipBtn.replaceWith(zipBtn.cloneNode(true));
        document.getElementById('dashZipBtn').addEventListener('click', handleBulkZip);
    }
}

function handlePlanCheckChange(e) {
    const id = parseInt(e.target.dataset.id, 10);
    if (e.target.checked) selectedPlanIds.add(id); else selectedPlanIds.delete(id);
    const allChecks   = document.querySelectorAll('.dash-plan-check');
    const headerCheck = document.getElementById('dashHeaderCheck');
    if (headerCheck) {
        headerCheck.checked       = allChecks.length > 0 && [...allChecks].every(cb => cb.checked);
        headerCheck.indeterminate = selectedPlanIds.size > 0 && selectedPlanIds.size < allChecks.length;
    }
    updateZipButton();
}

function updateZipButton() {
    const btn = document.getElementById('dashZipBtn');
    if (!btn) return;
    const count = selectedPlanIds.size;
    btn.disabled    = count === 0;
    btn.textContent = count > 0 ? `🗜 Download ZIP (${count})` : '🗜 Download ZIP';
}

async function handleBulkZip() {
    const btn = document.getElementById('dashZipBtn');
    if (!btn || selectedPlanIds.size === 0) return;
    const originalText = btn.textContent;
    btn.disabled = true; btn.textContent = '⏳ Zipping…';
    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.CSRF_TOKEN;
        const res = await fetch(`${API_BASE}/plans/zip/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            credentials: 'include',
            body: JSON.stringify({ plan_ids: [...selectedPlanIds] }),
        });
        if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.error || `Server error ${res.status}`); }
        await triggerBlobDownload(await res.blob(), 'CBC_Lesson_Plans.zip');
        selectedPlanIds.clear();
        document.querySelectorAll('.dash-plan-check').forEach(cb => cb.checked = false);
        const hc = document.getElementById('dashHeaderCheck');
        if (hc) { hc.checked = false; hc.indeterminate = false; }
        updateZipButton();
    } catch (err) {
        console.error('ZIP download failed:', err);
        alert(`ZIP download failed: ${err.message}`);
    } finally {
        btn.disabled = false; btn.textContent = originalText;
    }
}

// ── Utilities ──────────────────────────────────────────────────────────────
function setInner(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value ?? '–';
}
function togglePerm(id, active) {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('active', !!active);
}
function escHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}