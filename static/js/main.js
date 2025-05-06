/**
 * Main JavaScript functionality for the OCR application
 */
document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const webcamContainer = document.getElementById('webcam-container');
    const captureBtn = document.getElementById('capture-btn');
    const restartBtn = document.getElementById('restart-btn');
    const manualEntryBtn = document.getElementById('manual-entry-btn');
    const manualAddressForm = document.getElementById('manual-address-form');
    const submitManualBtn = document.getElementById('submit-manual-btn');
    const manualAddressInput = document.getElementById('manual-address-input');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultContainer = document.getElementById('result-container');
    const statusMessage = document.getElementById('status-message');
    const extractedAddressEl = document.getElementById('extracted-address');
    const subscriberInfoEl = document.getElementById('subscriber-info');
    
    // State variables
    let processingImage = false;
    
    // Initialize webcam
    function initializeWebcam() {
        Webcam.attach('webcam-container');
        
        // Reset UI
        showElement(webcamContainer);
        showElement(captureBtn);
        hideElement(restartBtn);
        hideElement(loadingIndicator);
        hideElement(resultContainer);
        hideElement(manualAddressForm);
    }
    
    // Handle webcam errors
    window.addEventListener('webcamError', function(event) {
        console.log("Webcam error caught by event listener:", event.detail.message);
        // Show manual entry form automatically when webcam fails
        setTimeout(function() {
            toggleManualEntry();
            // Add message to status message element
            statusMessage.innerHTML = '<div class="alert alert-warning">No se pudo acceder a la cámara. Por favor, utilice la entrada manual.</div>';
            showElement(statusMessage);
        }, 500);
    });
    
    // Capture image from webcam
    function captureImage() {
        if (processingImage) return;
        
        processingImage = true;
        showElement(loadingIndicator);
        hideElement(captureBtn);
        
        Webcam.snap(function(dataUrl) {
            // Stop webcam after capturing image
            Webcam.stop();
            
            // Process the image with OCR
            processImage(dataUrl);
        });
    }
    
    // Process the captured image
    function processImage(imageData) {
        statusMessage.innerHTML = 'Procesando imagen...';
        showElement(statusMessage);
        
        fetch('/process-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: imageData })
        })
        .then(response => response.json())
        .then(data => {
            displayResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            statusMessage.innerHTML = `Error: ${error.message || 'Ha ocurrido un error al procesar la imagen.'}`;
            showElement(restartBtn);
        })
        .finally(() => {
            hideElement(loadingIndicator);
            processingImage = false;
        });
    }
    
    // Process manually entered address
    function processManualAddress() {
        const addressText = manualAddressInput.value.trim();
        
        if (!addressText) {
            statusMessage.innerHTML = 'Por favor, introduce una dirección.';
            showElement(statusMessage);
            return;
        }
        
        showElement(loadingIndicator);
        hideElement(manualAddressForm);
        statusMessage.innerHTML = 'Procesando dirección...';
        showElement(statusMessage);
        
        fetch('/manual-entry', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ address: addressText })
        })
        .then(response => response.json())
        .then(data => {
            displayResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            statusMessage.innerHTML = `Error: ${error.message || 'Ha ocurrido un error al procesar la dirección.'}`;
            showElement(restartBtn);
        })
        .finally(() => {
            hideElement(loadingIndicator);
        });
    }
    
    // Display processing results
    function displayResults(data) {
        hideElement(webcamContainer);
        showElement(resultContainer);
        showElement(restartBtn);
        
        if (data.error) {
            statusMessage.innerHTML = `Error: ${data.error}`;
            return;
        }
        
        if (data.status === 'not_found') {
            statusMessage.innerHTML = 'No se ha encontrado ningún suscriptor que coincida con esta dirección.';
            extractedAddressEl.innerHTML = `<strong>Dirección extraída:</strong> ${data.extracted_address || data.provided_address || 'No se pudo extraer la dirección'}`;
            hideElement(subscriberInfoEl);
            return;
        }
        
        if (data.status === 'email_error') {
            statusMessage.innerHTML = 'Se ha encontrado un suscriptor, pero ha fallado el envío del email.';
        } else if (data.status === 'success') {
            statusMessage.innerHTML = '¡Email enviado con éxito!';
        }
        
        // Display extracted address if available
        if (data.extracted_address) {
            extractedAddressEl.innerHTML = `<strong>Dirección extraída:</strong> ${data.extracted_address}`;
            showElement(extractedAddressEl);
        } else {
            hideElement(extractedAddressEl);
        }
        
        // Display subscriber info if available
        if (data.subscriber) {
            const subscriber = data.subscriber;
            subscriberInfoEl.innerHTML = `
                <strong>Suscriptor:</strong> ${subscriber.name || 'N/A'}<br>
                <strong>Email:</strong> ${subscriber.email || 'N/A'}<br>
                <strong>Dirección registrada:</strong> ${subscriber.address || 'N/A'}
            `;
            showElement(subscriberInfoEl);
        } else {
            hideElement(subscriberInfoEl);
        }
    }
    
    // Toggle between webcam and manual entry
    function toggleManualEntry() {
        if (Webcam.streaming) {
            Webcam.stop();
        }
        
        hideElement(webcamContainer);
        hideElement(captureBtn);
        hideElement(resultContainer);
        showElement(manualAddressForm);
        hideElement(manualEntryBtn);
        showElement(restartBtn);
    }
    
    // Restart the application
    function restartApp() {
        // Clear previous results
        statusMessage.innerHTML = '';
        extractedAddressEl.innerHTML = '';
        subscriberInfoEl.innerHTML = '';
        manualAddressInput.value = '';
        
        // Hide result container and show webcam
        hideElement(resultContainer);
        hideElement(manualAddressForm);
        showElement(manualEntryBtn);
        
        // Initialize webcam again
        initializeWebcam();
    }
    
    // Helper functions to show/hide elements
    function showElement(element) {
        if (element) element.classList.remove('d-none');
    }
    
    function hideElement(element) {
        if (element) element.classList.add('d-none');
    }
    
    // Handle demo address selection
    function setupDemoAddressListeners() {
        const demoAddressLinks = document.querySelectorAll('.demo-address');
        
        demoAddressLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const address = this.getAttribute('data-address');
                if (address) {
                    manualAddressInput.value = address;
                    // Focus on the textarea
                    manualAddressInput.focus();
                }
            });
        });
    }
    
    // Event listeners
    captureBtn.addEventListener('click', captureImage);
    restartBtn.addEventListener('click', restartApp);
    manualEntryBtn.addEventListener('click', toggleManualEntry);
    submitManualBtn.addEventListener('click', processManualAddress);
    
    // Setup demo address listeners
    setupDemoAddressListeners();
    
    // Initialize webcam on page load
    initializeWebcam();
});
