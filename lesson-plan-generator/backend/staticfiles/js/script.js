// File: /lesson-plan-generator/backend/static/js/script.js

// ========== CONFIG ==========
const API_BASE = "http://192.168.235.108:8000/api";

window.isPremiumUser = false;

// DOM
const lessonForm = document.getElementById('lessonForm');
const lessonPlanContent = document.getElementById('lessonPlanContent');
const resultContainer = document.getElementById('resultContainer');

// Dropdowns
const levelSelect = document.getElementById('level'); // optional
const classSelect = document.getElementById('className');
const subjectSelect = document.getElementById('subject');
const unitSelect = document.getElementById('unitNo');
const lessonSelect = document.getElementById('lessonTitle');

// ========== INIT ==========
document.addEventListener("DOMContentLoaded", () => {
    if (levelSelect) {
        loadLevels();
    } else {
        loadClasses();
    }
});

// Attach listeners ONCE
if (levelSelect) {
    levelSelect.addEventListener('change', () => {
        resetBelow('level');
        if (levelSelect.value) loadClasses(levelSelect.value);
    });
}

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

// ========== API ==========
async function fetchData(endpoint, params = {}) {
    const url = new URL(`${API_BASE}/${endpoint}/`);
    Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, v));
    const res = await fetch(url);
    return await res.json();
}

// ========== RESET HELPERS ==========
function resetBelow(level) {
    if (level === 'level') {
        classSelect.innerHTML = `<option value="">Select Class</option>`;
    }
    if (['level', 'class'].includes(level)) {
        subjectSelect.innerHTML = `<option value="">Select Subject</option>`;
    }
    if (['level', 'class', 'subject'].includes(level)) {
        unitSelect.innerHTML = `<option value="">Select Unit</option>`;
    }
    if (['level', 'class', 'subject', 'unit'].includes(level)) {
        lessonSelect.innerHTML = `<option value="">Select Lesson</option>`;
    }
}

// ========== LOADERS ==========
async function loadLevels() {
    const levels = await fetchData('levels');
    levelSelect.innerHTML = `<option value="">Select Level</option>`;
    levels.forEach(l =>
        levelSelect.innerHTML += `<option value="${l.id}">${l.name}</option>`
    );
}

async function loadClasses(levelId = null) {
    const params = levelId ? { level_id: levelId } : {};
    const classes = await fetchData('classes', params);
    classSelect.innerHTML = `<option value="">Select Class</option>`;
    classes.forEach(c =>
        classSelect.innerHTML += `<option value="${c.id}">${c.name}</option>`
    );
}

async function loadSubjects(classId) {
    const subjects = await fetchData('subjects', { class_id: classId });
    subjectSelect.innerHTML = `<option value="">Select Subject</option>`;
    subjects.forEach(s =>
        subjectSelect.innerHTML += `<option value="${s.id}">${s.name}</option>`
    );
}

async function loadUnits(subjectId) {
    const units = await fetchData('units', { subject_id: subjectId });
    unitSelect.innerHTML = `<option value="">Select Unit</option>`;
    units.forEach(u =>
        unitSelect.innerHTML += `<option value="${u.id}" data-title="${u.title}" data-total="${u.total_lessons}">Unit ${u.number}</option>`
    );
}

// --- Minimal change for auto-fill Unit Title and Total Lessons ---
unitSelect.addEventListener('change', () => {
    resetBelow('unit');
    if (unitSelect.value) {
        // Auto-fill title and total lessons
        const selected = unitSelect.selectedOptions[0];
        document.getElementById('unitTitle').value = selected.dataset.title || '';
        document.getElementById('totalLessons').value = selected.dataset.total || '';
        // Load lessons for this unit
        loadLessons(unitSelect.value);
    }
});


async function loadLessons(unitId) {
    const lessons = await fetchData('lessons', { unit_id: unitId });
    lessonSelect.innerHTML = `<option value="">Select Lesson</option>`;
    lessons.forEach(l =>
        lessonSelect.innerHTML += `<option value="${l.id}">${l.title}</option>`
    );
}

// ========== FORM DATA ==========
function getFormData() {
    return {
        schoolName: schoolName.value,
        teacherName: teacherName.value,
        term: term.value,
        date: date.value,
        subject: subjectSelect.selectedOptions[0]?.text || '',
        className: classSelect.selectedOptions[0]?.text || '',
        unitNo: unitSelect.selectedOptions[0]?.text || '',
        lessonNo: lessonNo.value,
        totalLessons: totalLessons.value,
        duration: Number(duration.value),
        classSize: classSize.value,
        unitTitle: unitTitle.value,
        lessonTitle: lessonSelect.selectedOptions[0]?.text || '',
        specialNeeds: specialNeeds.value,
        references: references.value
    };
}

// ========== TIMING ==========
function calculateTiming(total) {
    const dev = Math.floor(total * 0.6);
    return { intro: 5, development: dev, conclusion: total - 5 - dev };
}

// ========== GENERATOR ==========
function generateLessonPlan() {
    const d = getFormData();
    const t = calculateTiming(d.duration);

    lessonPlanContent.innerHTML = `
        <h2 style="text-align:center">LESSON PLAN</h2>
        ${buildHeader(d)}
        ${buildLessonInfoTable(d)}
        ${buildUnitTable(d)}
        ${buildSteps(d, t)}
    `;

    resultContainer.classList.add('show');
    resultContainer.scrollIntoView({ behavior: 'smooth' });
}

// ========== BUILDERS ==========
function buildHeader(d) {
    return `<p><strong>School:</strong> ${d.schoolName}
    <span style="margin-left:50px"><strong>Teacher:</strong> ${d.teacherName}</span></p>`;
}

function buildLessonInfoTable(d) {
    return `
    <table>
        <tr>
            <th>Term</th><th>Date</th><th>Subject</th><th>Class</th>
            <th>Unit</th><th>Lesson</th><th>Duration</th><th>Class Size</th>
        </tr>
        <tr>
            <td>${d.term}</td><td>${d.date}</td><td>${d.subject}</td>
            <td>${d.className}</td><td>${d.unitNo}</td>
            <td>${d.lessonNo}/${d.totalLessons}</td>
            <td>${d.duration} min</td><td>${d.classSize}</td>
        </tr>
    </table>`;
}

function buildUnitTable(d) {
    return `
    <table>
        <tr><td><strong>Special Needs</strong></td><td>${d.specialNeeds || 'None'}</td></tr>
        <tr><td><strong>Unit Title</strong></td><td>${d.unitTitle}</td></tr>
        <tr><td><strong>Lesson Title</strong></td><td>${d.lessonTitle}</td></tr>
        <tr><td><strong>Objective</strong></td>
        <td>Explain and apply ${d.lessonTitle}</td></tr>
        <tr><td><strong>References</strong></td>
        <td>${d.references || 'REB Curriculum'}</td></tr>
    </table>`;
}

function buildSteps(d, t) {
    return `
    <table>
        ${step("Introduction", t.intro, d)}
        ${step("Development", t.development, d)}
        ${step("Conclusion", t.conclusion, d)}
    </table>`;
}

function step(name, time, d) {
    return `
    <tr>
        <td>${name} (${time} min)</td>
        <td>Teacher guides ${d.lessonTitle}</td>
        <td>Learners participate actively</td>
    </tr>`;
}

// ========== PREMIUM ==========
function copyToWord() {
    if (!window.isPremiumUser) return;
    navigator.clipboard.writeText(lessonPlanContent.innerText);
}

function downloadPDF() {
    if (!window.isPremiumUser) return;
    html2pdf().from(lessonPlanContent).save();
}

async function downloadDOCX() {
    if (!window.isPremiumUser) return;
    const doc = new docx.Document({
        sections: [{ children: [new docx.Paragraph(lessonPlanContent.innerText)] }]
    });
    const blob = await docx.Packer.toBlob(doc);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "lesson-plan.docx";
    a.click();
}
