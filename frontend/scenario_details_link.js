// Scenario Details Button Handler
// Add this to handle the "Detaylı Rapor" button

document.addEventListener('DOMContentLoaded', () => {
    const viewDetailsBtn = document.getElementById('viewDetailsBtn');

    if (viewDetailsBtn) {
        viewDetailsBtn.addEventListener('click', () => {
            const scenarioId = window.currentScenarioId;
            if (scenarioId) {
                window.location.href = `scenario_details.html?id=${scenarioId}`;
            } else {
                alert('Önce bir senaryo oluşturun!');
            }
        });
    }

    // Override showResults to store scenario_id
    const originalShowResults = window.showResults;
    if (originalShowResults) {
        window.showResults = function (data) {
            // Store scenario ID
            window.currentScenarioId = data.scenario_id;

            // Update scenario ID in results
            const scenarioIdEl = document.getElementById('scenarioIdResult');
            if (scenarioIdEl) {
                scenarioIdEl.textContent = data.scenario_id;
            }

            // Call original
            originalShowResults(data);
        };
    }
});
