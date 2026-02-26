// Tab switching functionality
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked tab
            this.classList.add('active');
        });
    });

    // Search button functionality
    const searchButton = document.querySelector('.search-button');
    const fromInput = document.getElementById('from-input');
    const toInput = document.getElementById('to-input');
    const recentJourneysList = document.getElementById('recent-journeys');
    
    searchButton.addEventListener('click', function() {
        const from = fromInput.value.trim();
        const to = toInput.value.trim();
        
        if (from && to) {
            // Get selected route type
            const routeType = document.querySelector('input[name="route-type"]:checked').value;
            const timeType = document.querySelector('input[name="time-type"]:checked').value;
            
            // Create journey item
            const journeyItem = document.createElement('div');
            journeyItem.className = 'journey-item';
            journeyItem.textContent = `${from} → ${to} (${routeType})`;
            
            // Add click handler to reload journey
            journeyItem.addEventListener('click', function() {
                fromInput.value = from;
                toInput.value = to;
            });
            
            // Add to recent journeys (at the top)
            recentJourneysList.insertBefore(journeyItem, recentJourneysList.firstChild);
            
            // Keep only last 5 journeys
            while (recentJourneysList.children.length > 5) {
                recentJourneysList.removeChild(recentJourneysList.lastChild);
            }
            
            // Show confirmation
            alert(`Searching for route from ${from} to ${to}`);
        } else {
            alert('Please enter both From and To locations');
        }
    });

    // Populate time dropdown with 15-minute intervals
    const timeSelect = document.getElementById('time-select');
    for (let hour = 0; hour < 24; hour++) {
        for (let minute = 0; minute < 60; minute += 15) {
            const hourStr = hour.toString().padStart(2, '0');
            const minuteStr = minute.toString().padStart(2, '0');
            const timeValue = `${hourStr}:${minuteStr}`;
            const option = document.createElement('option');
            option.value = timeValue;
            option.textContent = timeValue;
            timeSelect.appendChild(option);
        }
    }
    
    // Set default time to current time rounded up to next 15 minutes
    const now = new Date();
    const currentMinutes = now.getMinutes();
    const roundedMinutes = Math.ceil(currentMinutes / 15) * 15;
    let defaultHour = now.getHours();
    let defaultMinute = roundedMinutes;
    
    // Handle case where rounding up goes to next hour
    if (defaultMinute >= 60) {
        defaultMinute = 0;
        defaultHour = (defaultHour + 1) % 24;
    }
    
    const defaultTime = `${defaultHour.toString().padStart(2, '0')}:${defaultMinute.toString().padStart(2, '0')}`;
    timeSelect.value = defaultTime;

    // Date button
    const dateButton = document.querySelector('.time-button');
    dateButton.addEventListener('click', function() {
        const date = prompt('Enter date (DD/MM/YYYY):', new Date().toLocaleDateString('en-GB'));
        if (date) this.textContent = date;
    });

    // Sign in/out button
    const signButton = document.querySelector('.sign-button');
    let isSignedIn = false;
    
    signButton.addEventListener('click', function() {
        isSignedIn = !isSignedIn;
        if (isSignedIn) {
            alert('Signed in successfully!');
            this.textContent = 'Sign out';
        } else {
            alert('Signed out successfully!');
            this.textContent = 'Sign in';
        }
    });

    // Add double-click to save journey from recent to saved
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('journey-item') && e.target.parentElement.id === 'recent-journeys') {
            if (e.detail === 2) { // Double click
                const savedJourneysList = document.getElementById('saved-journeys');
                const journeyClone = e.target.cloneNode(true);
                
                // Add click handler to saved journey
                journeyClone.addEventListener('click', function() {
                    const journeyText = this.textContent;
                    const parts = journeyText.split(' → ');
                    if (parts.length >= 2) {
                        fromInput.value = parts[0];
                        toInput.value = parts[1].split(' (')[0];
                    }
                });
                
                savedJourneysList.appendChild(journeyClone);
                alert('Journey saved!');
            }
        }
    });
});