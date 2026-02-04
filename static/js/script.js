/* static/js/script.js */

document.addEventListener('DOMContentLoaded', () => {
    
    // --- Booking Logic ---
    const container = document.querySelector('.booking-layout');
    
    if (container) {
        const seats = document.querySelectorAll('.seat:not(.occupied)');
        const pricePerSeat = parseInt(container.dataset.price);
        
        // DOM Elements
        const countEl = document.getElementById('count');
        const totalEl = document.getElementById('total');
        const inputSeats = document.getElementById('input-seats');
        const inputAmount = document.getElementById('input-amount');

        // Click Event
        seats.forEach(seat => {
            seat.addEventListener('click', () => {
                seat.classList.toggle('selected');
                updateTotal();
            });
        });

        function updateTotal() {
            const selectedSeats = document.querySelectorAll('.seat.selected');
            const selectedCount = selectedSeats.length;

            // UI Updates
            countEl.innerText = selectedCount;
            totalEl.innerText = selectedCount * pricePerSeat;

            // Form Updates (Hidden Inputs)
            // We generate seat labels like "A1", "A2" based on grid position if needed, 
            // or just use the text inside the div if we added it.
            const seatLabels = Array.from(selectedSeats).map(s => s.innerText || s.dataset.id).join(',');
            
            inputSeats.value = seatLabels;
            inputAmount.value = selectedCount * pricePerSeat;
        }
    }
});