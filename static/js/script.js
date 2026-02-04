/* static/js/script.js */

document.addEventListener('DOMContentLoaded', () => {
    
    const container = document.querySelector('.booking-layout');
    
    if (container) {
        const seats = document.querySelectorAll('.seat');
        const pricePerSeat = parseInt(container.dataset.price);
        
        // DOM Elements
        const totalEl = document.getElementById('total');
        const inputSeats = document.getElementById('input-seats');
        const inputAmount = document.getElementById('input-amount');

        seats.forEach(seat => {
            seat.addEventListener('click', () => {
                // Toggle selection
                seat.classList.toggle('selected');
                
                // Calculate and Update
                updateTotal();
            });
        });

        function updateTotal() {
            const selectedSeats = document.querySelectorAll('.seat.selected');
            const selectedCount = selectedSeats.length;
            const totalPrice = selectedCount * pricePerSeat;

            // 1. Update the Total Price on screen
            if (totalEl) {
                totalEl.innerText = totalPrice;
            }

            // 2. Update Hidden Form Inputs (for the backend)
            if (inputSeats) {
                const seatLabels = Array.from(selectedSeats).map(s => s.dataset.id).join(',');
                inputSeats.value = seatLabels;
            }
            
            if (inputAmount) {
                inputAmount.value = totalPrice;
            }
        }
    }
});