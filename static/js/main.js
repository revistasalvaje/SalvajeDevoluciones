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
            if (data.status === 'match_found') {
                showConfirmationScreen(data);
            } else {
                displayResults(data);
            }
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
    
    // Show confirmation screen with preview
    function showConfirmationScreen(data) {
        // Hide webcam container and other elements
        hideElement(webcamContainer);
        hideElement(captureBtn);
        hideElement(manualEntryBtn);
        hideElement(manualAddressForm);
        
        // Show confirmation container
        showElement(document.getElementById('confirmation-container'));
        
        // Fill in the data
        const confirmationAddress = document.getElementById('confirmation-address');
        const confirmationSubscriber = document.getElementById('confirmation-subscriber');
        const emailPreview = document.getElementById('email-preview');
        
        // Display extracted address with more details
        confirmationAddress.innerHTML = `
            <div class="mb-3">
                <h6>Texto completo extraído por OCR:</h6>
                <div class="border p-2 bg-light text-dark" style="overflow-x: auto;">
                    <code>${data.extracted_address}</code>
                </div>
            </div>
            <div>
                <h6>Dirección formateada:</h6>
                <strong>${data.extracted_address}</strong>
            </div>
        `;
        
        // Display subscriber information
        const subscriber = data.subscriber;
        confirmationSubscriber.innerHTML = `
            <strong>Nombre:</strong> ${subscriber.name || 'N/A'}<br>
            <strong>Email:</strong> ${subscriber.email || 'N/A'}<br>
            <strong>Dirección registrada:</strong> ${subscriber.address || 'N/A'}
        `;
        
        // Load email preview
        loadEmailPreview(subscriber);
        
        // Setup event listeners for confirmation buttons
        setupConfirmationButtons(data);
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
            if (data.status === 'match_found') {
                showConfirmationScreen(data);
            } else {
                displayResults(data);
            }
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
            extractedAddressEl.innerHTML = `
                <h5>Detalles del OCR:</h5>
                <div class="mb-3">
                    <h6>Texto completo extraído:</h6>
                    <div class="border p-2 bg-light text-dark" style="overflow-x: auto;">
                        <code>${data.extracted_address}</code>
                    </div>
                </div>
                <div>
                    <h6>Dirección formateada:</h6>
                    <strong>${data.extracted_address}</strong>
                </div>
            `;
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
    
    // Load email preview
    function loadEmailPreview(subscriber) {
        const emailPreview = document.getElementById('email-preview');
        emailPreview.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Cargando...</span></div><p class="mt-2">Cargando vista previa del email...</p></div>';
        
        fetch('/preview-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ subscriber: subscriber })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                emailPreview.innerHTML = data.email_html;
            } else {
                emailPreview.innerHTML = '<div class="alert alert-warning">No se pudo cargar la vista previa del email</div>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            emailPreview.innerHTML = '<div class="alert alert-danger">Error al cargar la vista previa</div>';
        });
    }
    
    // Setup confirmation buttons
    function setupConfirmationButtons(data) {
        const editBtn = document.getElementById('edit-btn');
        const sendEmailBtn = document.getElementById('send-email-btn');
        const confirmationContainer = document.getElementById('confirmation-container');
        
        // Edit button goes back to manual entry
        editBtn.addEventListener('click', function() {
            hideElement(confirmationContainer);
            
            // Show manual form and populate with the extracted address
            showElement(manualAddressForm);
            manualAddressInput.value = data.extracted_address;
            showElement(restartBtn);
        });
        
        // Send email button
        sendEmailBtn.addEventListener('click', function() {
            // Disable button and show loading
            sendEmailBtn.disabled = true;
            sendEmailBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Enviando...';
            
            // Send email
            fetch('/send-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    subscriber: data.subscriber,
                    extracted_address: data.extracted_address
                })
            })
            .then(response => response.json())
            .then(result => {
                // Hide confirmation screen
                hideElement(confirmationContainer);
                
                // Show result
                displayResults(result);
            })
            .catch(error => {
                console.error('Error:', error);
                sendEmailBtn.disabled = false;
                sendEmailBtn.innerHTML = '<i class="fas fa-paper-plane me-1"></i> Enviar email';
                alert('Error al enviar el email: ' + (error.message || 'Error desconocido'));
            });
        });
    }
    
    // Restart the application
    function restartApp() {
        // Clear previous results
        statusMessage.innerHTML = '';
        extractedAddressEl.innerHTML = '';
        subscriberInfoEl.innerHTML = '';
        manualAddressInput.value = '';
        
        // Hide containers
        hideElement(resultContainer);
        hideElement(manualAddressForm);
        hideElement(document.getElementById('confirmation-container'));
        
        // Show webcam elements
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
    
    // Add event listener for new search button
    const newSearchBtn = document.getElementById('new-search-btn');
    if (newSearchBtn) {
        newSearchBtn.addEventListener('click', restartApp);
    }
    
    // Setup demo address listeners
    setupDemoAddressListeners();
    
    // Initialize webcam on page load
    initializeWebcam();
});
