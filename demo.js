// Updated demo.js
// This script powers the interactive demo. It loads movie options and
// recommendations, allows the user to build a short viewing history,
// select a model and then displays the associated architecture graphic
// and recommendation results. The demo uses static data to illustrate
// the pipeline and does not perform any inference in the browser.

document.addEventListener('DOMContentLoaded', () => {
  const modelSelect = document.getElementById('model-select');
  const movieSelectsContainer = document.getElementById('movie-selects');
  const addMovieBtn = document.getElementById('add-movie');
  const generateBtn = document.getElementById('generate');
  const architectureContainer = document.getElementById('architecture-container');
  const recommendationsContainer = document.getElementById('recommendations-container');

  // Embedded data. We embed both the recommendations and the movie list to
  // avoid fetch restrictions when running from a file:// scheme. Replace
  // these objects if you generate your own recommendations and movie list.
  const recommendationsData = {
    "TwoTower+XGBoost": {
      "recommendations": [
        {
          "movie": "The Shawshank Redemption (1994)",
          "explanation": "Based on the user's past ratings for similar drama and crime films."
        },
        {
          "movie": "Forrest Gump (1994)",
          "explanation": "Recommended due to high overlap with the user's favorite genres and sentiment."
        },
        {
          "movie": "Pulp Fiction (1994)",
          "explanation": "Ranked highly because the user enjoys non‑linear storytelling and crime themes."
        },
        {
          "movie": "The Godfather (1972)",
          "explanation": "Chosen for its classic status and similarity to movies the user has rated highly."
        },
        {
          "movie": "Fight Club (1999)",
          "explanation": "Suggested because of the user's interest in psychological thrillers."
        }
      ]
    },
    MBTR: {
      "recommendations": [
        {
          "movie": "The Matrix (1999)",
          "explanation": "Sequential patterns indicate the user enjoys mind‑bending science fiction with action."
        },
        {
          "movie": "Inception (2010)",
          "explanation": "Recommended due to similar temporal narrative and high user engagement."
        },
        {
          "movie": "Interstellar (2014)",
          "explanation": "Selected because the user's recent watch history shows interest in epic space dramas."
        },
        {
          "movie": "Memento (2000)",
          "explanation": "The model captured the user's affinity for complex storylines and suspense."
        },
        {
          "movie": "2001: A Space Odyssey (1968)",
          "explanation": "Chosen for its influential sci‑fi themes and alignment with the user's long‑term preferences."
        }
      ]
    },
    LiGR: {
      "recommendations": [
        {
          "movie": "Spirited Away (2001)",
          "explanation": "The set‑wise model selected a diverse set of animated films to broaden the user's horizons."
        },
        {
          "movie": "Toy Story (1995)",
          "explanation": "Included to complement other animation choices and appeal to nostalgia."
        },
        {
          "movie": "The Lion King (1994)",
          "explanation": "Recommended as a timeless classic that matches the user's appreciation for storytelling."
        },
        {
          "movie": "Up (2009)",
          "explanation": "Selected to introduce heartfelt adventure and widen genre diversity."
        },
        {
          "movie": "Coco (2017)",
          "explanation": "Added for its cultural richness and strong emotional narrative."
        }
      ]
    },
    "Rank Transformer": {
      "recommendations": [
        {
          "movie": "Schindler's List (1993)",
          "explanation": "Captures global context across all candidate items and recognises the user's interest in historical dramas."
        },
        {
          "movie": "Parasite (2019)",
          "explanation": "Ranked highly due to its critical acclaim and overlap with suspenseful thrillers the user enjoys."
        },
        {
          "movie": "City of God (2002)",
          "explanation": "Selected because of its raw storytelling and the user's affinity for international cinema."
        },
        {
          "movie": "Pan's Labyrinth (2006)",
          "explanation": "Recommended for its blend of fantasy and historical themes, resonating with the user's tastes."
        },
        {
          "movie": "Amélie (2001)",
          "explanation": "Added as a light‑hearted choice to balance the slate with romance and whimsy."
        }
      ]
    },
    "Graph Transformer": {
      "recommendations": [
        {
          "movie": "The Lord of the Rings: The Fellowship of the Ring (2001)",
          "explanation": "Graph‑based relations suggest the user belongs to communities that enjoy epic fantasy."
        },
        {
          "movie": "The Hobbit: An Unexpected Journey (2012)",
          "explanation": "Recommended due to connections in the user graph pointing to adventure prequels."
        },
        {
          "movie": "Harry Potter and the Sorcerer's Stone (2001)",
          "explanation": "Selected based on cross‑community links indicating an interest in magical worlds."
        },
        {
          "movie": "Star Wars: Episode IV – A New Hope (1977)",
          "explanation": "Chosen for its iconic status and shared fanbase with the user's communities."
        },
        {
          "movie": "The Avengers (2012)",
          "explanation": "Added to reflect the user's enjoyment of ensemble action and superhero narratives."
        }
      ]
    }
  };

  // List of movies the user can select. Keep this list concise for demonstration.
  const movieOptions = [
    "The Shawshank Redemption (1994)",
    "Forrest Gump (1994)",
    "Pulp Fiction (1994)",
    "The Godfather (1972)",
    "Fight Club (1999)",
    "The Matrix (1999)",
    "Inception (2010)",
    "Interstellar (2014)",
    "Memento (2000)",
    "2001: A Space Odyssey (1968)",
    "Spirited Away (2001)",
    "Toy Story (1995)",
    "The Lion King (1994)",
    "Up (2009)",
    "Coco (2017)",
    "Schindler's List (1993)",
    "Parasite (2019)",
    "City of God (2002)",
    "Pan's Labyrinth (2006)",
    "Amélie (2001)",
    "The Lord of the Rings: The Fellowship of the Ring (2001)",
    "The Hobbit: An Unexpected Journey (2012)",
    "Harry Potter and the Sorcerer's Stone (2001)",
    "Star Wars: Episode IV – A New Hope (1977)",
    "The Avengers (2012)"
  ];

  // Map model names to their corresponding architecture images.
  const modelImages = {
    'TwoTower+XGBoost': 'images/pipeline.png',
    MBTR: 'images/sequential.png',
    LiGR: 'images/setwise.png',
    'Rank Transformer': 'images/setwise.png',
    'Graph Transformer': 'images/graph.png'
  };

  // Create the first movie select on page load
  createMovieSelect();

  // Creates a new select element for movie selection and appends it to the container
  function createMovieSelect() {
    const select = document.createElement('select');
    movieOptions.forEach((title) => {
      const option = document.createElement('option');
      option.value = title;
      option.textContent = title;
      select.appendChild(option);
    });
    movieSelectsContainer.appendChild(select);
  }

  // Add another movie field, up to a maximum of 4 fields
  addMovieBtn.addEventListener('click', () => {
    const currentSelects = movieSelectsContainer.querySelectorAll('select');
    if (currentSelects.length >= 4) return;
    createMovieSelect();
  });

  // Generate recommendations when the user clicks the button
  generateBtn.addEventListener('click', () => {
    // Clear previous content
    architectureContainer.innerHTML = '';
    recommendationsContainer.innerHTML = '';

    const model = modelSelect.value;
    const selectedMovies = Array.from(
      movieSelectsContainer.querySelectorAll('select')
    ).map((sel) => sel.value);

    // Display selected movies summary
    const historySummary = document.createElement('p');
    historySummary.textContent = `Viewing history: ${selectedMovies.join(', ')}`;
    historySummary.style.color = 'var(--color-muted)';

    // Display the architecture image
    const img = document.createElement('img');
    img.src = modelImages[model] || '';
    img.alt = `${model} architecture`;
    img.style.maxWidth = '100%';
    img.style.display = 'block';
    img.style.marginBottom = '1rem';

    architectureContainer.appendChild(img);
    architectureContainer.appendChild(historySummary);

    // Render recommendations using the stored data
    renderRecommendations(model);
  });

  /**
   * Render recommendation cards for a given model using the global recommendationsData.
   *
   * @param {string} model - The model key in the recommendationsData object
   */
  function renderRecommendations(model) {
    const modelData = recommendationsData[model];
    if (!modelData || !modelData.recommendations) {
      recommendationsContainer.innerHTML =
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
      recommendationsContainer.appendChild(card);
    });
  }
});