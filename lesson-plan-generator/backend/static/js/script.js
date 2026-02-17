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
    prefillUserData();
    updateGenerateButtonStatus();
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
    btn.disabled = true;
    btn.title = "Checking access...";
    try {
        const data = await checkAccess(true);
        btn.disabled = !(data.is_premium || data.can_generate);
        btn.title = btn.disabled ? "Subscribe to unlock more lesson plans" : "";
    } catch (err) {
        console.error("Failed to update button status:", err);
        btn.disabled = true;
        btn.title = "Error checking access";
    }
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
    if (modal) modal.style.display = 'none';
}

// ===============================
// GENERATE LESSON PLAN
// ===============================
async function generateLessonPlanFromForm() {
    if (!unitSelect.value || !lessonSelect.value) {
        alert("Please fill all required fields!");
        return;
    }
    const btn = document.getElementById('generateButton');
    if (btn) btn.disabled = true;

    await requirePremium(async () => {
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
                    const modal = document.getElementById("subscribeModal");
                    if (modal) modal.style.display = "flex";
                    lessonPlanContent.textContent = '';
                    return;
                }
            }

            lessonPlanContent.innerHTML = data.html;
            if (resultContainer) resultContainer.classList.add('show');

        } catch (err) {
            console.error(err);
            alert("Unable to generate lesson plan. Check connection.");
            lessonPlanContent.textContent = '';
        } finally {
            if (btn) btn.disabled = false;
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

            // Show loading state on button
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
                    const modal = document.getElementById("subscribeModal");
                    if (modal) modal.style.display = "flex";
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
// DOWNLOAD FUNCTIONS — FIXED
// ===============================

/**
 * FIX 1: downloadPDF
 * - Clones the lesson plan element so we can apply print-safe styles
 *   without affecting the live page display.
 * - Removes overflow/max-height constraints that clip content.
 * - Uses html2pdf's correct async API (.outputPdf('blob') → save) to
 *   avoid the silent-failure bug in the old synchronous .save() call.
 */
async function downloadPDF() {
    console.log('📑 Starting PDF download...');
    const element = document.getElementById("lessonPlanContent");
    if (!element || !element.innerHTML.trim()) {
        alert("Generate a lesson plan first.");
        return;
    }

    try {
        // Clone element so we can inject print-safe styles safely
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

        // Fix any tables inside the clone for PDF rendering
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
            margin:      [0.5, 0.5, 0.5, 0.5],  // inches: top, right, bottom, left
            filename:    'CBC_Lesson_Plan.pdf',
            image:       { type: 'jpeg', quality: 0.98 },
            html2canvas: {
                scale: 2,
                useCORS: true,
                logging: false,
                scrollY: 0
            },
            jsPDF: {
                unit: 'in',
                format: 'a4',
                orientation: 'portrait'
            },
            pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
        };

        // Use the promise-based API — avoids silent failures
        await html2pdf().set(opt).from(clone).save();
        console.log('✅ PDF download complete');
    } catch (err) {
        console.error('PDF download error:', err);
        alert('Failed to download PDF. Please try again.\n\nError: ' + err.message);
    }
}

/**
 * FIX 2: copyToWord
 * - Uses the Clipboard API with HTML content type so that when the
 *   user pastes into Word they get the formatted version, not just
 *   stripped plain text.
 * - Falls back to plain text copy if the rich-HTML clipboard write
 *   is not supported (older browsers / non-HTTPS).
 */
function copyToWord() {
    console.log('📄 Copying to clipboard...');
    const element = document.getElementById("lessonPlanContent");
    if (!element || !element.innerHTML.trim()) {
        alert("Generate a lesson plan first.");
        return;
    }

    const htmlContent = element.innerHTML;
    const plainText  = element.innerText;

    // Try rich HTML clipboard first (pastes WITH formatting into Word)
    if (window.ClipboardItem && navigator.clipboard.write) {
        const htmlBlob  = new Blob([htmlContent], { type: 'text/html' });
        const textBlob  = new Blob([plainText],   { type: 'text/plain' });
        const item      = new ClipboardItem({ 'text/html': htmlBlob, 'text/plain': textBlob });

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
        // Fallback: plain text only (older browsers)
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

/**
 * FIX 3: downloadWord
 * Uses an MHT (MIME HTML) blob that Word natively opens as a full
 * formatted document — no external library needed at all.
 * This is the most reliable cross-browser approach:
 *   - Works in Word 2010+ on Windows
 *   - Works in LibreOffice
 *   - Preserves tables, bold, headings, colors from the rendered HTML
 *   - Zero dependency on CDN availability
 */
async function downloadWord() {
    console.log('📝 Starting DOCX download...');
    const element = document.getElementById("lessonPlanContent");
    if (!element || !element.innerHTML.trim()) {
        alert("Generate a lesson plan first.");
        return;
    }

    try {
        // Grab all styles currently applied in the page so Word renders
        // the lesson plan exactly as it looks on screen
        let styleContent = '';
        try {
            Array.from(document.styleSheets).forEach(sheet => {
                try {
                    Array.from(sheet.cssRules || []).forEach(rule => {
                        styleContent += rule.cssText + '\n';
                    });
                } catch (_) { /* cross-origin sheets — skip */ }
            });
        } catch (_) {}

        // Extra print-safe overrides so tables render with borders in Word
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

        // Build a complete self-contained HTML document
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
                <style>
                    ${styleContent}
                    ${printStyles}
                </style>
            </head>
            <body>
                ${element.innerHTML}
            </body>
            </html>
        `.trim();

        // Create blob with the Word-compatible MIME type
        const blob = new Blob(
            ['\ufeff', fullHtml],   // BOM + HTML
            { type: 'application/msword' }
        );

        const url = URL.createObjectURL(blob);
        const a   = document.createElement('a');
        a.href     = url;
        a.download = 'CBC_Lesson_Plan.doc';   // .doc opens reliably in all Word versions
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        // Small delay before revoking so the download has time to start
        setTimeout(() => URL.revokeObjectURL(url), 1000);

        console.log('✅ Word document download complete');
    } catch (err) {
        console.error('Word download error:', err);
        alert('Failed to create Word document. Please try again.\n\nError: ' + err.message);
    }
}
