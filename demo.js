// demo.js
// Load the precomputed recommendations and render them when the user selects
// a model. This script runs on the demo page and requires the
// recommendations.json file to be present in the same directory.

document.addEventListener('DOMContentLoaded', () => {
  const modelSelect = document.getElementById('model-select');
  const container = document.getElementById('recommendations-container');

  // Fetch recommendations from JSON file
  fetch('recommendations.json')
    .then((response) => response.json())
    .then((data) => {
      // Render recommendations for the initially selected model
      renderRecommendations(modelSelect.value, data);
      // Update recommendations when the model changes
      modelSelect.addEventListener('change', () => {
        renderRecommendations(modelSelect.value, data);
      });
    })
    .catch((error) => {
      console.error('Failed to load recommendations:', error);
      container.innerHTML =
        '<p style="color: var(--color-muted)">Error loading recommendations.</p>';
    });

  /**
   * Render recommendation cards for a given model.
   *
   * @param {string} model - The model key in the data object
   * @param {object} data - Parsed JSON containing recommendation lists
   */
  function renderRecommendations(model, data) {
    container.innerHTML = '';
    const modelData = data[model];
    if (!modelData || !modelData.recommendations) {
      container.innerHTML =
        '<p style="color: var(--color-muted)">No data for selected model.</p>';
      return;
    }
    modelData.recommendations.forEach((item) => {
      const card = document.createElement('div');
      card.className = 'card';
      const title = document.createElement('h3');
      title.textContent = item.movie;
      const explanation = document.createElement('p');
      explanation.textContent = item.explanation;
      card.appendChild(title);
      card.appendChild(explanation);
      container.appendChild(card);
    });
  }
});