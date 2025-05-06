/**
 * WebcamJS v1.0.26
 * Adapted for this project's specific needs
 */
(function(window) {
    var Webcam = {
        version: '1.0.26',
        
        // properties
        width: 0,
        height: 0,
        streaming: false,
        
        // DOM elements
        mediaElement: null,
        container: null,
        
        // user callbacks
        onCaptureComplete: null,
        
        /**
         * Initialize webcam and attach to DOM element
         */
        attach: function(element_id) {
            // get DOM element
            this.container = document.getElementById(element_id) || document.createElement('div');
            
            // create video element if needed
            if (!this.mediaElement) {
                this.mediaElement = document.createElement('video');
                this.mediaElement.setAttribute('autoplay', 'autoplay');
                this.mediaElement.setAttribute('playsinline', 'playsinline');
                this.mediaElement.style.width = '100%';
                this.mediaElement.style.height = '100%';
                
                this.container.appendChild(this.mediaElement);
            }
            
            // set container size
            this.width = this.container.offsetWidth;
            this.height = this.container.offsetHeight;
            
            // set up event listeners
            var self = this;
            
            // when video stream starts playing
            this.mediaElement.addEventListener('canplay', function() {
                self.streaming = true;
            }, false);
            
            // access the webcam
            return this.getUserMedia();
        },
        
        /**
         * Access the webcam
         */
        getUserMedia: function() {
            var self = this;
            
            // check for getUserMedia support
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                // modern browser API
                return navigator.mediaDevices.getUserMedia({
                    audio: false,
                    video: { facingMode: 'environment' } // prefer back camera if available
                })
                .then(function(stream) {
                    self.mediaElement.srcObject = stream;
                    return true;
                })
                .catch(function(err) {
                    console.error("getUserMedia failed:", err);
                    // Display the error message in the webcam container
                    if (self.container) {
                        self.container.innerHTML = `
                            <div class="webcam-error alert alert-warning p-3">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                <strong>No se puede acceder a la cámara</strong><br>
                                Puede deberse a permisos denegados o a que no hay una cámara disponible.<br>
                                Por favor, utilice la opción de entrada manual de dirección.
                            </div>
                        `;
                    }
                    // Dispatch a custom event to notify the main JS
                    window.dispatchEvent(new CustomEvent('webcamError', { 
                        detail: { message: err.message || 'No se pudo acceder a la cámara' } 
                    }));
                    return false;
                });
            } else {
                console.error("getUserMedia not supported in this browser");
                return Promise.resolve(false);
            }
        },
        
        /**
         * Take a snapshot from the webcam
         */
        snap: function(callback, quality) {
            if (!this.streaming) {
                console.error("Webcam is not streaming");
                return false;
            }
            
            // default callback
            callback = callback || this.onCaptureComplete;
            if (!callback) {
                console.error("No capture callback specified");
                return false;
            }
            
            // set default quality
            quality = quality || 0.9;
            
            // create offscreen canvas element to hold pixels
            var canvas = document.createElement('canvas');
            canvas.width = this.width;
            canvas.height = this.height;
            
            // copy video to canvas and get image data
            var context = canvas.getContext('2d');
            context.drawImage(this.mediaElement, 0, 0, this.width, this.height);
            
            // get image data URL
            var dataURL = canvas.toDataURL('image/jpeg', quality);
            
            // execute callback with data
            callback(dataURL);
            
            return true;
        },
        
        /**
         * Stop the webcam stream
         */
        stop: function() {
            if (this.mediaElement && this.mediaElement.srcObject) {
                // stop all tracks
                var tracks = this.mediaElement.srcObject.getTracks();
                tracks.forEach(function(track) {
                    track.stop();
                });
                
                this.mediaElement.srcObject = null;
                this.streaming = false;
            }
            
            return true;
        }
    };
    
    // Export to global namespace
    window.Webcam = Webcam;
    
})(window);
