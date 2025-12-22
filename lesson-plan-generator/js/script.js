// File: /lesson-plan-generator/js/script.js

// ========== CONFIGURATION ==========
let isPremiumUser = false; // <-- change to true after payment verification

// DOM references
const lessonForm = document.getElementById('lessonForm');
const lessonPlanContent = document.getElementById('lessonPlanContent');
const resultContainer = document.getElementById('resultContainer');

// Event listeners
lessonForm.addEventListener('submit', (e) => {
    e.preventDefault();
    generateLessonPlan();
});

// ======= LESSON PLAN GENERATION =======
function generateLessonPlan() {
    const data = getFormData();

    const timing = calculateTiming(data.duration);

    // Build lesson plan HTML
    lessonPlanContent.innerHTML = `
        <div class="text-center bold" style="font-size:12pt;margin-bottom:10px;">LESSON PLAN</div>
        ${buildHeader(data)}
        ${buildLessonInfoTable(data)}
        ${buildUnitTable(data)}
        ${buildStepByStepTable(data, timing)}
    `;

    resultContainer.classList.add('show');
    resultContainer.scrollIntoView({ behavior: 'smooth' });
}

// Collect form inputs
function getFormData() {
    return {
        schoolName: document.getElementById('schoolName').value,
        teacherName: document.getElementById('teacherName').value,
        term: document.getElementById('term').value,
        date: document.getElementById('date').value,
        subject: document.getElementById('subject').value,
        className: document.getElementById('className').value,
        unitNo: document.getElementById('unitNo').value,
        lessonNo: document.getElementById('lessonNo').value,
        totalLessons: document.getElementById('totalLessons').value,
        duration: Number(document.getElementById('duration').value),
        classSize: document.getElementById('classSize').value,
        unitTitle: document.getElementById('unitTitle').value,
        lessonTitle: document.getElementById('lessonTitle').value,
        specialNeeds: document.getElementById('specialNeeds').value,
        references: document.getElementById('references').value
    };
}

// Calculate lesson timing
function calculateTiming(totalDuration) {
    return {
        intro: 5,
        development: Math.floor(totalDuration * 0.6),
        conclusion: Math.floor(totalDuration * 0.25)
    };
}

// ======= BUILD HTML PARTS =======
function buildHeader(data) {
    return `
        <div style="margin-bottom:5px;font-size:10pt;">
            <span class="bold">School Name:</span> ${data.schoolName}
            <span style="margin-left:80px;" class="bold">Teacher's name:</span> ${data.teacherName}
        </div>
    `;
}

function buildLessonInfoTable(data) {
    return `
        <table>
            <tr>
                <td class="bold">Term</td>
                <td class="bold">Date</td>
                <td class="bold">Subject</td>
                <td class="bold">Class</td>
                <td class="bold">Unit N°</td>
                <td class="bold">Lesson N°</td>
                <td class="bold">Duration</td>
                <td class="bold">Class size</td>
            </tr>
            <tr>
                <td>${data.term}</td>
                <td>${data.date}</td>
                <td>${data.subject}</td>
                <td>${data.className}</td>
                <td>${data.unitNo}</td>
                <td>${data.lessonNo} of ${data.totalLessons}</td>
                <td>${data.duration} min</td>
                <td>${data.classSize}</td>
            </tr>
        </table>
    `;
}

function buildUnitTable(data) {
    return `
        <table>
            <tr>
                <td class="bold" style="width:33%;">Type of Special Educational Needs</td>
                <td>${data.specialNeeds || 'No specific special educational needs identified'}</td>
            </tr>
            <tr><td class="bold">Unit title</td><td>${data.unitTitle}</td></tr>
            <tr><td class="bold">Key Unit Competence</td><td>Be able to understand and apply ${data.lessonTitle} concepts accurately in ${data.subject}</td></tr>
            <tr><td class="bold">Title of the lesson</td><td>${data.lessonTitle}</td></tr>
            <tr><td class="bold">Instructional Objective</td><td>By the end of this lesson, learners should be able to explain and demonstrate ${data.lessonTitle} with accuracy and confidence</td></tr>
            <tr><td class="bold">Plan for this Class</td><td>Inside the classroom - learners arranged in groups of 5</td></tr>
            <tr><td class="bold">Learning Materials</td><td>${data.subject} textbook, charts, markers, exercise books, chalk/whiteboard, demonstration materials</td></tr>
            <tr><td class="bold">References</td><td>${data.references || `${data.subject} book for ${data.className}, Rwanda Education Board curriculum`}</td></tr>
        </table>
    `;
}

function buildStepByStepTable(data, timing) {
    return `
        <table>
            <tr>
                <td class="bold" style="width:15%;">Timing for each step</td>
                <td colspan="2" class="bold text-center">Description of teaching and learning activity</td>
                <td class="bold" style="width:30%;">Generic competences + Cross cutting issues</td>
            </tr>
            <tr>
                <td></td>
                <td class="bold" style="width:27.5%;">Teacher activities</td>
                <td class="bold" style="width:27.5%;">Learner activities</td>
                <td></td>
            </tr>
            ${buildLessonStep('Introduction', timing.intro, data)}
            ${buildLessonStep('Development', timing.development, data)}
            ${buildLessonStep('Conclusion', timing.conclusion, data)}
            <tr>
                <td class="bold">Teacher self-evaluation</td>
                <td colspan="3">
                    <em>To be completed after lesson delivery:</em><br/>
                    • Did all learners achieve the lesson objective?<br/>
                    • Which activities worked well and which need improvement?<br/>
                    • Were the learning materials adequate and effective?<br/>
                    • How many learners need additional support?<br/>
                    • What adjustments are needed for the next lesson?
                </td>
            </tr>
        </table>
    `;
}

function buildLessonStep(stepName, stepDuration, data) {
    return `
        <tr>
            <td class="bold">${stepName}<br/>${stepDuration} min</td>
            <td>
                <ul>
                    <li>Teacher performs ${stepName.toLowerCase()} activities for ${data.lessonTitle}</li>
                    <li>Monitors and guides learners</li>
                    <li>Explains key concepts clearly</li>
                </ul>
            </td>
            <td>
                <ul>
                    <li>Engage in ${stepName.toLowerCase()} activities</li>
                    <li>Participate actively</li>
                    <li>Take notes and ask questions</li>
                </ul>
            </td>
            <td>
                <strong>Competences:</strong> Communication, cooperation, critical thinking, creativity<br/>
                <strong>Cross-cutting issues:</strong> Values, inclusion, lifelong learning
            </td>
        </tr>
    `;
}

// ======= COPY & DOWNLOAD FUNCTIONS =======
function copyToWord() {
    if (!isPremiumUser) return alert('💡 Subscribe to unlock download and copy features!');

    const range = document.createRange();
    range.selectNode(lessonPlanContent);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);

    try {
        document.execCommand('copy');
        alert('✅ Lesson plan copied! Open Word and press Ctrl+V to paste.');
    } catch (err) {
        alert('Manual copy required. Select content and press Ctrl+C.');
    }
    window.getSelection().removeAllRanges();
}

// ======= PDF DOWNLOAD (requires html2pdf.js) =======
function downloadPDF() {
    if (!isPremiumUser) return alert('💡 Subscribe to unlock PDF download!');
    if (typeof html2pdf === 'undefined') return alert('html2pdf.js library not loaded!');

    html2pdf()
        .set({ margin: 0.5, filename: `${document.getElementById('lessonTitle').value}.pdf` })
        .from(lessonPlanContent)
        .save();
}

// ======= DOCX DOWNLOAD (requires docx.js) =======
async function downloadDOCX() {
    if (!isPremiumUser) return alert('💡 Subscribe to unlock DOCX download!');
    if (typeof docx === 'undefined') return alert('docx.js library not loaded!');

    const { Document, Packer, Paragraph, Table, TableRow, TableCell, TextRun } = docx;

    const doc = new Document();
    doc.addSection({
        children: [
            new Paragraph({ text: document.getElementById('lessonTitle').value, bold: true }),
            new Paragraph({ text: lessonPlanContent.innerText })
        ]
    });

    const blob = await Packer.toBlob(doc);
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${document.getElementById('lessonTitle').value}.docx`;
    link.click();
}
