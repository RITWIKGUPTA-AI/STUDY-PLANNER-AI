// Function to load exams dynamically on page load
async function loadTargetExams() {
    try {
        const res = await fetch('/api/exam-hub/list');
        if (!res.ok) throw new Error("Failed to load exam list");
        const exams = await res.json();
        
        const select = document.getElementById('exam-select');
        if (select && Object.keys(exams).length > 0) {
            select.innerHTML = '';
            for (const [key, name] of Object.entries(exams)) {
                const opt = document.createElement('option');
                opt.value = key;
                opt.textContent = name;
                select.appendChild(opt);
            }
        }
    } catch (err) {
        console.warn('Could not auto-fetch exam list, using default HTML options:', err);
    }
}

// Main generation handler
async function startAutoMockTest() {
    console.log("Generate button clicked!");
    
    const examSelect = document.getElementById('exam-select');
    const container = document.getElementById('test-container');
    const generateBtn = document.getElementById('generate-btn');

    if (!examSelect || !container) {
        alert("Error: HTML containers (#exam-select or #test-container) are missing from the template!");
        return;
    }

    const examKey = examSelect.value;
    
    // UI Loading state
    if (generateBtn) generateBtn.disabled = true;
    container.innerHTML = `
        <div class="text-center my-4">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2 fw-bold">Generating ${examKey} pattern test with AI service...</p>
        </div>
    `;

    try {
        const response = await fetch('/api/exam-hub/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ exam_key: examKey })
        });

        if (!response.ok) {
            throw new Error(`Server returned status ${response.status}`);
        }

        const testData = await response.json();
        console.log("Test generated successfully:", testData);

        // Simple preview render to confirm test payload works
        renderTestInterface(testData);

    } catch (error) {
        console.error("Generation error:", error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <strong>Failed to generate test:</strong> ${error.message}. Please check your Flask app terminal for back-end logs.
            </div>
        `;
    } finally {
        if (generateBtn) generateBtn.disabled = false;
    }
}

function renderTestInterface(testData) {
    const container = document.getElementById('test-container');
    let questionsHtml = testData.questions.map((q, idx) => `
        <div class="card mb-3 p-3">
            <h5>Q${idx + 1}. ${q.question}</h5>
            ${q.options.map((opt, oIdx) => `
                <div class="form-check">
                    <input class="form-check-input" type="radio" name="q_${q.id}" value="${opt}">
                    <label class="form-check-label">${opt}</label>
                </div>
            `).join('')}
        </div>
    `).join('');

    container.innerHTML = `
        <div class="alert alert-info fw-bold">${testData.exam_name || 'CBT Exam'} Active</div>
        <form id="cbt-form">
            ${questionsHtml}
            <button type="button" class="btn btn-success mt-2" onclick="alert('Test submitted!')">Submit Test</button>
        </form>
    `;
}

// Auto-run when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    loadTargetExams();
});
<script src="{{ url_for('static', filename='js/ai.js') }}?v=2"></script>