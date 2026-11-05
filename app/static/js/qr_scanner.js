/**
 * Kitaab Bank - Offline QR Scanner & Camera Lifecycle Manager
 * Implements Secure Context detection, native BarcodeDetector + jsQR fallback,
 * and strict stream teardown (preventing stuck camera indicators).
 */

(function () {
  'use strict';

  // Elements
  const insecureBanner = document.getElementById('insecure-context-banner');
  const secureScannerWrap = document.getElementById('secure-scanner-wrap');
  const video = document.getElementById('qr-video');
  const canvas = document.getElementById('qr-canvas');
  const startBtn = document.getElementById('start-camera-btn');
  const stopBtn = document.getElementById('stop-camera-btn');
  const switchBtn = document.getElementById('switch-camera-btn');
  const statusBadge = document.getElementById('scanner-status');
  const manualInput = document.getElementById('manual-code-input');

  let activeStream = null;
  let animFrameId = null;
  let scanIntervalId = null;
  let currentFacingMode = 'environment'; // Prefer rear camera on mobile
  let barcodeDetector = null;
  let isScanning = false;

  // 1. Detect Secure Context
  const isSecure = window.isSecureContext ||
                   window.location.hostname === 'localhost' ||
                   window.location.hostname === '127.0.0.1';

  const hasMediaSupport = Boolean(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);

  // Initialize UI based on security context
  function initContext() {
    if (!isSecure || !hasMediaSupport) {
      if (insecureBanner) insecureBanner.style.display = 'block';
      if (secureScannerWrap) secureScannerWrap.style.display = 'none';
      if (manualInput) {
        setTimeout(() => manualInput.focus(), 300);
      }
    } else {
      if (insecureBanner) insecureBanner.style.display = 'none';
      if (secureScannerWrap) secureScannerWrap.style.display = 'block';

      // Check native BarcodeDetector
      if ('BarcodeDetector' in window) {
        try {
          barcodeDetector = new window.BarcodeDetector({ formats: ['qr_code'] });
          console.log('[KitaabQR] Using Native BarcodeDetector hardware engine');
        } catch (e) {
          barcodeDetector = null;
          console.log('[KitaabQR] Falling back to bundled jsQR engine');
        }
      } else {
        console.log('[KitaabQR] BarcodeDetector not in window; using bundled jsQR engine');
      }
    }
  }

  // 2. Audio Feedback on Successful Scan (Synthesized Web Audio API - Zero External Assets)
  function playSuccessChime() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(659.25, ctx.currentTime); // E5
      osc.frequency.setValueAtTime(880.00, ctx.currentTime + 0.08); // A5

      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.3);
    } catch (e) {
      // Audio autoplay policy or unsupported - silent fallback
    }
  }

  // 3. Stop Stream & Release Camera Hardware (Madrasah Library pattern)
  function stopCamera() {
    isScanning = false;
    if (animFrameId) {
      cancelAnimationFrame(animFrameId);
      animFrameId = null;
    }
    if (scanIntervalId) {
      clearInterval(scanIntervalId);
      scanIntervalId = null;
    }
    if (activeStream) {
      activeStream.getTracks().forEach(track => {
        try {
          track.stop();
        } catch (e) {}
      });
      activeStream = null;
    }
    if (video) {
      video.srcObject = null;
    }
    if (startBtn) startBtn.style.display = 'inline-flex';
    if (stopBtn) stopBtn.style.display = 'none';
    if (switchBtn) switchBtn.style.display = 'none';
    if (statusBadge) {
      statusBadge.textContent = 'Camera Off';
      statusBadge.className = 'badge badge-secondary';
    }
  }

  // 4. Start Camera Stream
  async function startCamera() {
    stopCamera();

    if (statusBadge) {
      statusBadge.textContent = 'Opening Camera...';
      statusBadge.className = 'badge badge-warning';
    }

    try {
      const constraints = {
        video: {
          facingMode: { ideal: currentFacingMode },
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      activeStream = stream;
      video.srcObject = stream;
      await video.play();

      isScanning = true;
      if (startBtn) startBtn.style.display = 'none';
      if (stopBtn) stopBtn.style.display = 'inline-flex';
      if (switchBtn) switchBtn.style.display = 'inline-flex';
      if (statusBadge) {
        statusBadge.textContent = 'Scanning Active';
        statusBadge.className = 'badge badge-success';
      }

      startScanLoop();
    } catch (err) {
      console.warn('[KitaabQR] Camera access error:', err);
      stopCamera();
      if (statusBadge) {
        statusBadge.textContent = 'Camera Denied / Unavailable';
        statusBadge.className = 'badge badge-danger';
      }
      alert('Could not access camera. Please check camera permissions or use the 6-digit Book Code input.');
      if (manualInput) manualInput.focus();
    }
  }

  // 5. Continuous Frame Decoding Loop
  function startScanLoop() {
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });

    async function tick() {
      if (!isScanning || !video || video.readyState !== video.HAVE_ENOUGH_DATA) {
        if (isScanning) {
          animFrameId = requestAnimationFrame(tick);
        }
        return;
      }

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      let detectedCode = null;

      // Try native BarcodeDetector first
      if (barcodeDetector) {
        try {
          const barcodes = await barcodeDetector.detect(canvas);
          if (barcodes && barcodes.length > 0) {
            detectedCode = barcodes[0].rawValue;
          }
        } catch (e) {
          // Fall back to jsQR
        }
      }

      // Fall back to bundled jsQR
      if (!detectedCode && window.jsQR) {
        try {
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const code = window.jsQR(imageData.data, imageData.width, imageData.height, {
            inversionAttempts: 'dontInvert'
          });
          if (code && code.data) {
            detectedCode = code.data;
          }
        } catch (e) {
          // Frame decode error - continue loop
        }
      }

      if (detectedCode) {
        onQrCodeDetected(detectedCode);
        return; // Stop scanning loop on detection
      }

      if (isScanning) {
        animFrameId = requestAnimationFrame(tick);
      }
    }

    animFrameId = requestAnimationFrame(tick);
  }

  // 6. Handle Detected Code
  function onQrCodeDetected(rawData) {
    console.log('[KitaabQR] Detected QR code:', rawData);
    playSuccessChime();
    stopCamera();

    if (statusBadge) {
      statusBadge.textContent = 'Code Scanned!';
      statusBadge.className = 'badge badge-primary';
    }

    // Populate manual input to give user instant visual feedback
    if (manualInput) {
      manualInput.value = rawData;
    }

    // Redirect to scan resolver route
    const encoded = encodeURIComponent(rawData.trim());
    window.location.href = '/scan?code=' + encoded;
  }

  // 7. Event Listeners & Hardware Lifecycle Hooks
  if (startBtn) {
    startBtn.addEventListener('click', startCamera);
  }

  if (stopBtn) {
    stopBtn.addEventListener('click', stopCamera);
  }

  if (switchBtn) {
    switchBtn.addEventListener('click', () => {
      currentFacingMode = (currentFacingMode === 'environment') ? 'user' : 'environment';
      startCamera();
    });
  }

  // Critical Cleanup Listeners (Madrasah Library pattern)
  // Ensures phone camera light turns off when navigating away or switching tabs
  window.addEventListener('beforeunload', stopCamera);
  window.addEventListener('pagehide', stopCamera);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      stopCamera();
    }
  });

  // Export functions to global scope for testing and accessibility
  window.KitaabQR = {
    startCamera,
    stopCamera,
    initContext,
    isSecure
  };

  // Initialize on page load
  document.addEventListener('DOMContentLoaded', initContext);
})();
