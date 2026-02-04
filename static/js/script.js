/* static/js/script.js */

document.addEventListener('DOMContentLoaded', () => {
    
    // --- BOOKING PAGE LOGIC ---
    const bookingContainer = document.querySelector('.booking-container');
    
    // Only run this code if we are actually on the booking page
    if (bookingContainer) {
        const seats = document.querySelectorAll('.seat');
        
        seats.forEach(seat => {
            seat.addEventListener('click', () => {
                seat.classList.toggle('selected');
                updateBookingSummary();
            });
        });
    }
});

function updateBookingSummary() {
    const selectedSeats = document.querySelectorAll('.seat.selected');
    
    // Get the price from the HTML data-attribute (The "Professional" way)
    const bookingContainer = document.querySelector('.booking-container');
    const pricePerSeat = Number(bookingContainer.dataset.price); 
    
    const totalPrice = selectedSeats.length * pricePerSeat;
    
    // Update the UI
    document.getElementById('total-price').innerText = "₹" + totalPrice;
    
    // Update Hidden Form Inputs
    const seatLabels = Array.from(selectedSeats).map(s => s.innerText).join(',');
    document.getElementById('seats-input').value = seatLabels;
    document.getElementById('amount-input').value = totalPrice;
}