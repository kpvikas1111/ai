let chartsRendered = false;

// Initialize charts on window load if Analytics tab is active
window.onload = () => {
    if(document.getElementById('analyticsView').classList.contains('active-view')) {
        initCharts();
        chartsRendered = true;
    }
};

function switchTab(tabId, element) {
    document.querySelectorAll('.view-section').forEach(view => view.classList.remove('active-view'));
    document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));

    document.getElementById(tabId).classList.add('active-view');
    element.classList.add('active');

    // Only load charts if they are visible and haven't been loaded yet
    if(tabId === 'analyticsView' && !chartsRendered) {
        initCharts();
        chartsRendered = true;
    }
}

function initCharts() {
    const gridColor = 'rgba(0, 243, 255, 0.1)';
    const textColor = '#64748b';

    const ctxDoughnut = document.getElementById('complianceChart').getContext('2d');
    new Chart(ctxDoughnut, {
        type: 'doughnut',
        data: {
            labels: ['Compliant', 'Violations'],
            datasets: [{
                data: [352, 166],
                backgroundColor: ['rgba(0, 255, 102, 0.8)', 'rgba(255, 0, 60, 0.8)'],
                borderColor: ['#00ff66', '#ff003c'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom', labels: { color: textColor, font: { family: 'Fira Code' } } } },
            cutout: '75%'
        }
    });

    const ctxBar = document.getElementById('leakVectorChart').getContext('2d');
    new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: ['Failover Replica', 'Marketing Logs', 'Cache Server', 'Legacy Backup'],
            datasets: [{
                label: 'Ghost Records Detected',
                data: [82, 54, 18, 12],
                backgroundColor: 'rgba(0, 243, 255, 0.2)',
                borderColor: '#00f3ff',
                borderWidth: 2, borderRadius: 4
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: {
                y: { grid: { color: gridColor }, ticks: { color: textColor, font: { family: 'Fira Code' } } },
                x: { grid: { display: false }, ticks: { color: textColor, font: { family: 'Fira Code' } } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

async function executeScan() {
    const btn = document.getElementById('scanBtn');
    const loader = document.getElementById('scanLoader');
    const caseId = document.getElementById('caseId').value;
    const email = document.getElementById('userEmail').value;
    
    if (!caseId || !email) { alert("Provide Case ID and Target Email."); return; }

    btn.disabled = true;
    document.getElementById('btnText').innerText = "SCANNING...";
    loader.classList.remove('hidden');
    document.getElementById('standbyScreen').classList.remove('hidden');
    document.getElementById('resultsScreen').classList.add('hidden');
    
    try {
        const response = await fetch('http://localhost:5000/api/audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ case_id: caseId, email: email })
        });
        const data = await response.json();
        if (response.ok) renderDashboard(data);
        else alert("SYSTEM FAULT: " + data.error);
    } catch (error) {
        alert("UPLINK FAILED. Ensure python app.py is running.");
    } finally {
        btn.disabled = false;
        document.getElementById('btnText').innerText = "EXECUTE SCAN";
        loader.classList.add('hidden');
    }
}

function renderDashboard(data) {
    document.getElementById('standbyScreen').classList.add('hidden');
    document.getElementById('resultsScreen').classList.remove('hidden');

    document.getElementById('displayCaseId').innerText = data.case_id.toUpperCase();
    document.getElementById('displayEmail').innerText = data.target_email;

    const badge = document.getElementById('statusBadge');
    badge.innerText = data.status;
    badge.className = `status-badge glowing ${data.status}`;

    document.getElementById('diagnosticReason').innerText = data.reason;
    document.getElementById('correctionPlan').innerText = data.remediation_plan;

    const tbody = document.getElementById('stepsBody');
    tbody.innerHTML = '';
    data.steps.forEach(step => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="color: #64748b;">[${step.step_no}]</td>
            <td><span class="phase-badge phase-${step.phase}">${step.phase}</span></td>
            <td style="color: white;">${step.operation}</td>
            <td>${step.system_id}</td>
            <td style="color: #facc15;">${step.resource_id}</td>
            <td>${step.state}</td>
        `;
        tbody.appendChild(tr);
    });
}