// ===============================
// CONFIG & DOM ELEMENTS
// ===============================
const API_BASE = window.location.origin + "/api";

window.CSRF_TOKEN = document.querySelector('[name=csrfmiddlewaretoken]')?.value || null;
if (!window.CSRF_TOKEN) {
    console.warn("CSRF token not found on page. POST requests may fail!");
}

const lessonForm = document.getElementById('lessonForm');
const lessonPlanContent = document.getElementById('lessonPlanContent');
const resultContainer = document.getElementById('resultContainer');

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
    if (levelSelect) loadLevels();
    attachGenerateButton();
    attachPayButton();
    attachDownloadButtons();

    // Clear field errors as user fills them
    document.querySelectorAll('input, select').forEach(el => {
        el.addEventListener('change', () => el.classList.remove('field-error'));
        el.addEventListener('input',  () => el.classList.remove('field-error'));
    });

    // Use server-injected data instantly — no fetch needed on first load
    if (window.__DASHBOARD__) {
        renderDashboard(window.__DASHBOARD__);
    }

    // Fire remaining calls in parallel
    await Promise.all([
        prefillUserData(),
        updateGenerateButtonStatus()
    ]);
});

// ===============================
// FETCH HELPERS
// ===============================
async function fetchData(endpoint, params = {}) {
    const url = new URL(`${API_BASE}/${endpoint}/`);
    Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, v));
    const res = await fetch(url, { headers: { 'Accept': 'application/json' }, credentials: 'include' });
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return await res.json();
}

async function postData(endpoint, payload = {}) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.CSRF_TOKEN;
    if (!csrfToken) {
        console.error("CSRF token missing!");
        alert("CSRF token missing. Please refresh the page and try again.");
        return { ok: false, data: { error: "CSRF token missing" } };
    }
    try {
        const res = await fetch(`${API_BASE}/${endpoint}/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
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
    if (level === 'level') classSelect.innerHTML = `<option value="">Select Class</option>`;
    if (['level', 'class'].includes(level)) subjectSelect.innerHTML = `<option value="">Select Subject</option>`;
    if (['level', 'class', 'subject'].includes(level)) unitSelect.innerHTML = `<option value="">Select Unit</option>`;
    if (['level', 'class', 'subject', 'unit'].includes(level)) lessonSelect.innerHTML = `<option value="">Select Lesson</option>`;
}

async function loadLevels() {
    const levels = await fetchData('levels') || [];
    levelSelect.innerHTML = `<option value="">Select Level</option>`;
    levels.forEach(l => levelSelect.innerHTML += `<option value="${l.id}">${l.name}</option>`);
}

async function loadClasses(levelId) {
    classSelect.innerHTML = `<option value="">Loading...</option>`;
    const classes = await fetchData('classes', { level_id: levelId }) || [];
    classSelect.innerHTML = `<option value="">Select Class</option>`;
    classes.forEach(c => classSelect.innerHTML += `<option value="${c.id}">${c.name}</option>`);
}

async function loadSubjects(classId) {
    subjectSelect.innerHTML = `<option value="">Loading...</option>`;
    const subjects = await fetchData('subjects', { class_id: classId }) || [];
    subjectSelect.innerHTML = `<option value="">Select Subject</option>`;
    subjects.forEach(s => subjectSelect.innerHTML += `<option value="${s.id}">${s.name}</option>`);
}

async function loadUnits(subjectId) {
    unitSelect.innerHTML = `<option value="">Loading...</option>`;
    const units = await fetchData('units', { subject_id: subjectId }) || [];
    unitSelect.innerHTML = `<option value="">Select Unit</option>`;
    units.forEach(u => unitSelect.innerHTML += `<option value="${u.id}" data-title="${u.title}" data-total="${u.total_lessons}">Unit ${u.number} - ${u.title}</option>`);
}

async function loadLessons(unitId) {
    lessonSelect.innerHTML = `<option value="">Loading...</option>`;
    const lessons = await fetchData('lessons', { unit_id: unitId }) || [];
    lessonSelect.innerHTML = `<option value="">Select Lesson</option>`;
    lessons.forEach(l => lessonSelect.innerHTML += `<option value="${l.id}">${l.title}</option>`);
}

// ===============================
// EVENT LISTENERS
// ===============================
if (levelSelect) levelSelect.addEventListener('change', () => { resetBelow('level'); if (levelSelect.value) loadClasses(levelSelect.value); });
if (classSelect) classSelect.addEventListener('change', () => { resetBelow('class'); if (classSelect.value) loadSubjects(classSelect.value); });
if (subjectSelect) subjectSelect.addEventListener('change', () => { resetBelow('subject'); if (subjectSelect.value) loadUnits(subjectSelect.value); });
if (unitSelect) unitSelect.addEventListener('change', () => {
    resetBelow('unit');
    if (unitSelect.value) {
        const selected = unitSelect.selectedOptions[0];
        document.getElementById('unitTitle').value = selected.dataset.title || '';
        document.getElementById('totalLessons').value = selected.dataset.total || '';
        loadLessons(unitSelect.value);
    }
});

// ===============================
// FIELD VALIDATION & HIGHLIGHTING
// ===============================
function highlightEmptyFields() {
    const requiredFields = [
        'schoolName', 'teacherName', 'term', 'date',
        'level', 'className', 'subject', 'unitNo',
        'lessonNo', 'totalLessons', 'duration',
        'classSize', 'unitTitle', 'lessonTitle'
    ];

    let hasEmpty = false;
    requiredFields.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        if (!el.value || el.value === '') {
            el.classList.add('field-error');
            hasEmpty = true;
        } else {
            el.classList.remove('field-error');
        }
    });

    // Scroll to first error
    if (hasEmpty) {
        const first = document.querySelector('.field-error');
        if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    return hasEmpty;
}

// ===============================
// FORM DATA
// ===============================
function getFormData() {
    return {
        level: levelSelect.options[levelSelect.selectedIndex].text,
        className: classSelect.options[classSelect.selectedIndex].text,
        subject: subjectSelect.options[subjectSelect.selectedIndex].text,
        unitTitle: document.getElementById('unitTitle').value,
        totalLessons: parseInt(document.getElementById('totalLessons').value || '0'),
        lessonTitle: lessonSelect.options[lessonSelect.selectedIndex].text,
        lessonNumber: parseInt(document.getElementById('lessonNo')?.value || '1'),
        durationMinutes: parseInt(document.getElementById('duration')?.value || '40'),
        schoolName: document.getElementById('schoolName')?.value || '',
        teacherName: document.getElementById('teacherName')?.value || '',
        term: document.getElementById('term')?.value || '',
        classSize: document.getElementById('classSize')?.value || '',
        references: document.getElementById('references')?.value || '',
        specialNeeds: document.getElementById('specialNeeds')?.value || '',
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
// ACCESS CHECK
// ===============================
async function checkAccess(forceRefresh = false) {
    if (accessCache && !forceRefresh) return accessCache;
    try {
        const res = await fetch(`${API_BASE}/check-access/`, { credentials: 'include' });
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
// UPDATE GENERATE BUTTON STATUS
// ===============================
async function updateGenerateButtonStatus() {
    const btn = document.getElementById('generateButton');
    if (!btn) return;
    try {
        const data = await checkAccess(true);
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
// SHOW PAYWALL MODAL
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

// ===============================
// REQUIRE PREMIUM
// ===============================
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
    // Highlight empty fields first
    if (highlightEmptyFields()) {
        alert("Please fill in all highlighted fields!");
        return;
    }

    const btn = document.getElementById('generateButton');

    await requirePremium(async () => {
        if (btn) { btn.disabled = true; btn.textContent = '⏳ Generating...'; }

        try {
            lessonPlanContent.textContent = 'Generating lesson plan...';
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
                ).map(o => o.value).join(', ')
            };

            const { ok, data } = await postData('generate_lesson_plan', payload);

            if (!ok) {
                if (data.redirect || data.error) {
                    showPaywallModal();
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
    console.log('🔧 Attaching download buttons...');
    document.querySelectorAll('.download-btn').forEach(btn => {
        const action = btn.dataset.action;
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            console.log(`📥 Download button clicked: ${action}`);

            const element = document.getElementById("lessonPlanContent");
            if (!element || !element.innerHTML.trim()) {
                alert("Generate a lesson plan first.");
                return;
            }

            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = '⏳ Please wait...';

            try {
                const accessData = await checkAccess(true);
                console.log('Fresh access data:', accessData);

                if (accessData.is_premium) {
                    console.log('✅ Premium confirmed');
                    if (action === 'copy') copyToWord();
                    else if (action === 'pdf') await downloadPDF();
                    else if (action === 'word') await downloadWord();
                } else {
                    console.log('❌ Not premium, showing modal');
                    showPaywallModal();
                }
            } catch (err) {
                console.error('Error checking access:', err);
                alert("Unable to verify subscription. Please try again.");
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
            }
        });
    });
}

function attachPayButton() {
    const payBtn = document.getElementById('payButton');
    if (payBtn) payBtn.addEventListener('click', async (e) => { e.preventDefault(); subscribeFromPage?.(); });
}

// ===============================
// SUBSCRIBE — fallback only
// ===============================
function subscribe(plan) {
    sessionStorage.setItem('selected_plan', plan);
    window.location.href = `/payment/?plan=${plan}`;
}

// ===============================
// DOWNLOAD FUNCTIONS
// ===============================
async function downloadPDF() {
    console.log('📑 Starting PDF download...');
    const element = document.getElementById("lessonPlanContent");
    if (!element || !element.innerHTML.trim()) {
        alert("Generate a lesson plan first.");
        return;
    }

    try {
        const clone = element.cloneNode(true);
        clone.style.cssText = `
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.6;
            color: #000;
            background: #fff;
            padding: 10px;
            width: 100%;
            overflow: visible !important;
            max-height: none !important;
        `;
        clone.querySelectorAll('table').forEach(t => {
            t.style.borderCollapse = 'collapse';
            t.style.width = '100%';
        });
        clone.querySelectorAll('td, th').forEach(cell => {
            cell.style.border = '1px solid #333';
            cell.style.padding = '6px 8px';
            cell.style.verticalAlign = 'top';
        });

        const opt = {
            margin:      [0.5, 0.5, 0.5, 0.5],
            filename:    'CBC_Lesson_Plan.pdf',
            image:       { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2, useCORS: true, logging: false, scrollY: 0 },
            jsPDF:       { unit: 'in', format: 'a4', orientation: 'portrait' },
            pagebreak:   { mode: ['avoid-all', 'css', 'legacy'] }
        };

        await html2pdf().set(opt).from(clone).save();
        console.log('✅ PDF download complete');
    } catch (err) {
        console.error('PDF download error:', err);
        alert('Failed to download PDF. Please try again.\n\nError: ' + err.message);
    }
}

function copyToWord() {
    console.log('📄 Copying to clipboard...');
    const element = document.getElementById("lessonPlanContent");
    if (!element || !element.innerHTML.trim()) {
        alert("Generate a lesson plan first.");
        return;
    }

    const htmlContent = element.innerHTML;
    const plainText   = element.innerText;

    if (window.ClipboardItem && navigator.clipboard.write) {
        const htmlBlob = new Blob([htmlContent], { type: 'text/html' });
        const textBlob = new Blob([plainText],   { type: 'text/plain' });
        const item     = new ClipboardItem({ 'text/html': htmlBlob, 'text/plain': textBlob });

        navigator.clipboard.write([item])
            .then(() => {
                console.log('✅ Rich HTML copied');
                alert("Lesson plan copied with formatting!\nOpen Microsoft Word and press Ctrl+V (or Cmd+V on Mac) to paste.");
            })
            .catch(err => {
                console.warn('Rich copy failed, falling back to plain text:', err);
                fallbackCopyPlainText(plainText);
            });
    } else {
        fallbackCopyPlainText(plainText);
    }
}

function fallbackCopyPlainText(text) {
    navigator.clipboard.writeText(text)
        .then(() => {
            console.log('✅ Plain text copied');
            alert("Lesson plan copied (plain text).\nPaste into Microsoft Word — formatting may be limited.");
        })
        .catch(err => {
            console.error('Copy failed entirely:', err);
            alert("Copy failed. Please select the lesson plan text manually and use Ctrl+C.");
        });
}

async function downloadWord() {
    console.log('📝 Starting DOCX download...');
    const element = document.getElementById("lessonPlanContent");
    if (!element || !element.innerHTML.trim()) {
        alert("Generate a lesson plan first.");
        return;
    }

    try {
        let styleContent = '';
        try {
            Array.from(document.styleSheets).forEach(sheet => {
                try {
                    Array.from(sheet.cssRules || []).forEach(rule => {
                        styleContent += rule.cssText + '\n';
                    });
                } catch (_) {}
            });
        } catch (_) {}

        const printStyles = `
            body { font-family: Arial, sans-serif; font-size: 12pt; color: #000; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 12pt; }
            td, th { border: 1px solid #333; padding: 6px 8px; vertical-align: top; font-size: 11pt; }
            th { background-color: #f0f0f0; font-weight: bold; }
            h1 { font-size: 16pt; margin: 12pt 0 6pt; }
            h2 { font-size: 14pt; margin: 10pt 0 4pt; }
            h3 { font-size: 12pt; margin: 8pt 0 4pt; }
            p  { margin: 4pt 0; }
        `;

        const fullHtml = `
            <html xmlns:o="urn:schemas-microsoft-com:office:office"
                  xmlns:w="urn:schemas-microsoft-com:office:word"
                  xmlns="http://www.w3.org/TR/REC-html40">
            <head>
                <meta charset="UTF-8">
                <meta name="ProgId" content="Word.Document">
                <meta name="Generator" content="Microsoft Word 15">
                <!--[if gte mso 9]>
                <xml>
                    <w:WordDocument>
                        <w:View>Print</w:View>
                        <w:Zoom>100</w:Zoom>
                        <w:DoNotOptimizeForBrowser/>
                    </w:WordDocument>
                </xml>
                <![endif]-->
                <style>${styleContent}${printStyles}</style>
            </head>
            <body>${element.innerHTML}</body>
            </html>
        `.trim();

        const blob = new Blob(['\ufeff', fullHtml], { type: 'application/msword' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = 'CBC_Lesson_Plan.doc';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 1000);

        console.log('✅ Word document download complete');
    } catch (err) {
        console.error('Word download error:', err);
        alert('Failed to create Word document. Please try again.\n\nError: ' + err.message);
    }
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
            headers: { 'Accept': 'application/json' }
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

    if (!data.is_authenticated) {
        renderGuestBanner(data);
    } else {
        renderFullDashboard(data);
    }
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
            text.innerHTML = `
                <strong style="color:#f44336">Free limit reached (3 of 3 used).</strong>
                <a href="/register/"
                   style="color:#4CAF50;font-weight:700;margin-left:6px;text-decoration:underline;">
                    Create a free account
                </a>
                to get more lessons, or
                <a href="/pricing/"
                   style="color:#2D9CDB;font-weight:700;margin-left:2px;text-decoration:underline;">
                    subscribe for unlimited access.
                </a>
            `;
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
    const limitLabel = (data.remaining === null || data.remaining === undefined)
        ? 'Unlimited plan'
        : `of ${limit} total`;
    setInner('dashLimit', limitLabel);

    if (data.remaining === null || data.remaining === undefined) {
        setInner('dashRemaining', '∞');
        setInner('dashRemainingLabel', 'unlimited');
    } else {
        setInner('dashRemaining', data.remaining);
        setInner('dashRemainingLabel', data.remaining === 1 ? 'lesson left' : 'lessons left');
    }

    const fill = document.getElementById('dashProgressFill');
    if (fill) {
        const pct = data.is_premium
            ? 100
            : Math.min(100, limit > 0 ? Math.round((used / limit) * 100) : 0);
        fill.style.width      = `${pct}%`;
        fill.style.background = pct >= 90
            ? 'linear-gradient(90deg,#f44336,#EF9A9A)'
            : 'linear-gradient(90deg,#4CAF50,#81C784)';
    }

    const planEl = document.getElementById('dashPlan');
    if (planEl) {
        if (data.is_premium && data.subscription_plan) {
            planEl.textContent = data.subscription_plan.charAt(0).toUpperCase() + data.subscription_plan.slice(1);
            planEl.style.color = '#81C784';
        } else if (data.is_premium) {
            planEl.textContent = 'Premium';
            planEl.style.color = '#81C784';
        } else {
            planEl.textContent = 'Free';
            planEl.style.color = '#FF9800';
        }
    }

    const expiryEl = document.getElementById('dashExpiry');
    if (expiryEl) {
        if (data.subscription_expiry) {
            const d = new Date(data.subscription_expiry);
            expiryEl.textContent = `Expires: ${d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}`;
        } else if (data.is_premium) {
            expiryEl.textContent = 'No expiry set';
        } else {
            expiryEl.textContent = 'Upgrade for more';
        }
    }

    togglePerm('permPdf',  data.can_download_pdf);
    togglePerm('permDocx', data.can_download_docx);
    togglePerm('permCopy', data.can_copy_word);

    const hint = document.getElementById('dashUpgradeHint');
    if (hint && !data.is_premium) {
        hint.innerHTML = `<a href="/pricing/" style="color:#4CAF50;font-size:11px;">Upgrade to unlock all →</a>`;
    }

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
            <td>
                <input type="checkbox" class="dash-plan-check" data-id="${p.id}"
                       aria-label="Select ${escHtml(p.lesson_title)}">
            </td>
            <td><span class="dash-subject-badge">${escHtml(p.subject)}</span></td>
            <td class="dash-lesson-title-cell" title="${escHtml(p.lesson_title)}">${escHtml(p.lesson_title)}</td>
            <td>${escHtml(p.class_name)}</td>
            <td>${escHtml(p.term ? 'Term ' + p.term : '–')}</td>
            <td class="dash-date-cell">${escHtml(p.created_at)}</td>
        </tr>
    `).join('');

    tbody.querySelectorAll('.dash-plan-check').forEach(cb => {
        cb.addEventListener('change', handlePlanCheckChange);
    });
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
                const id   = parseInt(cb.dataset.id, 10);
                if (e.target.checked) selectedPlanIds.add(id);
                else selectedPlanIds.delete(id);
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
                const id   = parseInt(cb.dataset.id, 10);
                if (!allChecked) selectedPlanIds.add(id);
                else selectedPlanIds.delete(id);
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
    if (e.target.checked) selectedPlanIds.add(id);
    else selectedPlanIds.delete(id);

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
    const count     = selectedPlanIds.size;
    btn.disabled    = count === 0;
    btn.textContent = count > 0 ? `🗜 Download ZIP (${count})` : '🗜 Download ZIP';
}

async function handleBulkZip() {
    const btn = document.getElementById('dashZipBtn');
    if (!btn || selectedPlanIds.size === 0) return;

    const originalText = btn.textContent;
    btn.disabled       = true;
    btn.textContent    = '⏳ Zipping…';

    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.CSRF_TOKEN;
        const res = await fetch(`${API_BASE}/plans/zip/`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            credentials: 'include',
            body: JSON.stringify({ plan_ids: [...selectedPlanIds] }),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `Server error ${res.status}`);
        }

        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = 'CBC_Lesson_Plans.zip';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 1500);

        selectedPlanIds.clear();
        document.querySelectorAll('.dash-plan-check').forEach(cb => cb.checked = false);
        const hc = document.getElementById('dashHeaderCheck');
        if (hc) { hc.checked = false; hc.indeterminate = false; }
        updateZipButton();

    } catch (err) {
        console.error('ZIP download failed:', err);
        alert(`ZIP download failed: ${err.message}`);
    } finally {
        btn.disabled    = false;
        btn.textContent = originalText;
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
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}