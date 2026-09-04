document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const resultsGrid = document.getElementById('results-grid');
    const modal = document.getElementById('trip-modal');
    const closeBtn = document.querySelector('.close-btn');
    const saveTripBtn = document.getElementById('save-trip-btn');
    
    let currentTrip = null;

    // Load Filters and Initial Data
    fetchFilterOptions();
    fetchData();

    // Fetch dynamic options for the dropdowns
    function fetchFilterOptions() {
        fetch('/api/options')
            .then(res => res.json())
            .then(data => {
                const landscapeSelect = document.getElementById('landscape');
                const stateSelect = document.getElementById('state');
                
                data.landscapes.forEach(l => {
                    let opt = document.createElement('option');
                    opt.value = l; opt.textContent = l;
                    landscapeSelect.appendChild(opt);
                });
                
                data.states.forEach(s => {
                    let opt = document.createElement('option');
                    opt.value = s; opt.textContent = s;
                    stateSelect.appendChild(opt);
                });
            })
            .catch(err => console.error('Error loading options:', err));
    }

    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        fetchData();
    });

    // Fetch search results based on user input
    function fetchData() {
        const landscape = document.getElementById('landscape').value;
        const state = document.getElementById('state').value;
        const budget = document.getElementById('budget').value;

        let url = `/api/search?landscape=${encodeURIComponent(landscape)}&state=${encodeURIComponent(state)}`;
        if (budget) url += `&budget=${encodeURIComponent(budget)}`;

        fetch(url)
            .then(res => res.json())
            .then(data => renderCards(data))
            .catch(err => console.error('Error fetching data:', err));
    }

    // FIX: Added 'targetContainer' parameter so this function can render cards on both the home page AND inside the My Trips modal
    function renderCards(places, targetContainer = resultsGrid) {
        targetContainer.innerHTML = '';
        
        if (places.length === 0) {
            targetContainer.innerHTML = '<h3 style="grid-column: 1/-1; text-align: center; color: #7f8c8d;">No trips found. Try adjusting your filters.</h3>';
            return;
        }

        places.forEach(place => {
            const card = document.createElement('div');
            card.className = 'card';
            card.innerHTML = `
                <div class="card-header">
                    <span class="badge">${place.landscape}</span>
                    <span class="state-tag">📍 ${place.state}</span>
                </div>
                <h3>${place.name}</h3>
                <p>${place.description}</p>
                <div class="card-footer">
                    <span>⏱️ ${place.duration}</span>
                    <span class="price-tag">Est. ₹${place.budget}</span>
                </div>
            `;
            // Only open the details modal if we are on the main page, not inside My Trips
            if (targetContainer === resultsGrid) {
                card.addEventListener('click', () => openModal(place));
            }
            targetContainer.appendChild(card);
        });
    }

    // Modal display logic for Trip Finalization
    function openModal(place) {
        currentTrip = place;
        document.getElementById('modal-title').textContent = `${place.name}, ${place.state}`;
        
        // Dynamic price calculation based on base budget
        const trainCost = Math.round(place.budget * 0.15);
        const flightCost = Math.round(place.budget * 0.40);
        
        document.getElementById('modal-transport').innerHTML = `
            <li>🚆 Train (Sleeper/3AC): ~₹${trainCost}</li>
            <li>✈️ Flight (Economy): ~₹${flightCost}</li>
            <li>🚌 Local State Transport Bus: ~₹400/day</li>
        `;
        
        document.getElementById('modal-hospital').textContent = `Govt. District Hospital, ${place.state} (Ambulance: 108)`;
        modal.classList.remove('hidden');
    }

    /// Modal Close Controls
    closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
    window.addEventListener('click', (e) => { 
        if (e.target === modal) modal.classList.add('hidden'); 
    });

    // --- AUTHENTICATION & DATABASE TRIPS LOGIC ---
    const authBtn = document.getElementById('auth-btn');
    const welcomeMsg = document.getElementById('welcome-msg');
    const myTripsBtn = document.getElementById('my-trips-btn');
    const loginModal = document.getElementById('login-modal');
    const tripsModal = document.getElementById('trips-modal');
    let isLoggedIn = false;

    function checkAuthStatus() {
        fetch('/api/user_status')
            .then(res => res.json())
            .then(data => {
                isLoggedIn = data.logged_in;
                if (isLoggedIn) {
                    authBtn.textContent = 'Logout';
                    welcomeMsg.textContent = `Hi, ${data.username}`;
                    welcomeMsg.style.display = 'inline';
                    myTripsBtn.style.display = 'inline';
                } else {
                    authBtn.textContent = 'Login';
                    welcomeMsg.style.display = 'none';
                    myTripsBtn.style.display = 'none';
                }
            });
    }

    authBtn.addEventListener('click', () => {
        if (isLoggedIn) {
            fetch('/api/logout', { method: 'POST' }).then(() => {
                alert('Logged out successfully');
                checkAuthStatus();
            });
        } else {
            loginModal.style.display = 'flex';
        }
    });

    document.getElementById('submit-login').addEventListener('click', () => {
        const username = document.getElementById('username-input').value;
        if (!username) return alert('Enter a username');

        fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        }).then(res => res.json()).then(data => {
            loginModal.style.display = 'none';
            checkAuthStatus();
        });
    });

    document.getElementById('close-login').onclick = () => loginModal.style.display = 'none';
    document.getElementById('close-trips').onclick = () => tripsModal.style.display = 'none';

    // FIX: Attach click listener to the big save button inside the modal!
    saveTripBtn.addEventListener('click', () => {
        if (currentTrip) {
            window.saveTrip(currentTrip.id);
        }
    });

    window.saveTrip = function(destinationId) {
        if (!isLoggedIn) {
            alert('Please login to save a trip!');
            modal.classList.add('hidden'); // hide the trip details
            loginModal.style.display = 'flex'; // show login box
            return;
        }

        fetch('/api/save_trip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ destination_id: destinationId })
        })
        .then(res => res.json())
        .then(data => alert(data.message));
    };

    myTripsBtn.addEventListener('click', () => {
        fetch('/api/my_trips')
            .then(res => res.json())
            .then(data => {
                const tripsContainer = document.getElementById('saved-trips-container');
                // FIX: Send the saved data to the 'My Trips' container instead of the home page
                renderCards(data, tripsContainer);
                tripsModal.style.display = 'flex';
            });
    });

    // Initialize Auth Check
    checkAuthStatus();

});