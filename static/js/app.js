var timerInterval = null;
var timerSeconds = 0;
var timerRunning = false;

function showToast(message, type) {
    var toastEl = document.getElementById('appToast');
    var toastBody = document.getElementById('toastBody');
    var toastTitle = document.getElementById('toastTitle');
    var toastIcon = document.getElementById('toastIcon');
    if (!toastEl || !toastBody) return;

    toastBody.textContent = message;
    toastEl.className = 'toast';

    if (type === 'success') {
        toastEl.classList.add('toast-success');
        toastTitle.textContent = 'Success';
        toastIcon.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
    } else if (type === 'error') {
        toastEl.classList.add('toast-error');
        toastTitle.textContent = 'Error';
        toastIcon.innerHTML = '<i class="bi bi-exclamation-circle-fill text-danger"></i>';
    } else {
        toastTitle.textContent = 'Studyboard';
        toastIcon.innerHTML = '<i class="bi bi-info-circle-fill text-primary"></i>';
    }

    var toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
}

var pendingDeleteForm = null;

function setupConfirmDeleteForms() {
    var forms = document.querySelectorAll('.confirm-delete-form');
    forms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            pendingDeleteForm = form;
            var msg = form.getAttribute('data-confirm-msg') || 'Are you sure you want to delete this?';
            document.getElementById('confirmDeleteMessage').textContent = msg;
            var modal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
            modal.show();
        });
    });

    var confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function () {
            if (pendingDeleteForm) {
                pendingDeleteForm.submit();
                pendingDeleteForm = null;
            }
        });
    }
}

function formatDuration(totalSeconds) {
    if (totalSeconds >= 3600) {
        var h = Math.floor(totalSeconds / 3600);
        var m = Math.floor((totalSeconds % 3600) / 60);
        return h + 'h ' + m + 'm';
    } else if (totalSeconds >= 60) {
        var mins = Math.floor(totalSeconds / 60);
        var secs = totalSeconds % 60;
        return mins + 'm ' + secs + 's';
    } else {
        return totalSeconds + ' seconds';
    }
}

function getCSRFToken() {
    var input = document.querySelector('input[name="csrf_token"]');
    if (input) return input.value;
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    return '';
}

function setupColourBubbles() {
    var bubbles = document.querySelectorAll('.colour-bubble');
    var input = document.getElementById('colourInput');
    if (!bubbles.length || !input) return;

    bubbles.forEach(function (bubble) {
        if (bubble.getAttribute('data-colour') === input.value) {
            bubble.classList.add('selected');
        }
        bubble.addEventListener('click', function () {
            bubbles.forEach(function (b) { b.classList.remove('selected'); });
            bubble.classList.add('selected');
            input.value = bubble.getAttribute('data-colour');
        });
    });
}


function updateTimerDisplay() {
    const h = Math.floor(timerSeconds / 3600);
    const m = Math.floor((timerSeconds % 3600) / 60);
    const s = timerSeconds % 60;
    const display = document.getElementById('timerDisplay');
    if (display) {
        display.textContent =
            String(h).padStart(2, '0') + ':' +
            String(m).padStart(2, '0') + ':' +
            String(s).padStart(2, '0');
    }
}

function startTimer() {
    if (timerRunning) return;
    timerRunning = true;
    timerInterval = setInterval(function () {
        timerSeconds++;
        updateTimerDisplay();
    }, 1000);
    toggleTimerButtons('running');
}

function pauseTimer() {
    timerRunning = false;
    clearInterval(timerInterval);
    toggleTimerButtons('paused');
}

function resumeTimer() {
    startTimer();
}

function stopTimer() {
    timerRunning = false;
    clearInterval(timerInterval);

    if (timerSeconds === 0) {
        toggleTimerButtons('stopped');
        return;
    }

    const savedSeconds = timerSeconds;
    const durationMinutes = timerSeconds / 60;
    const subjectId = document.getElementById('timerSubject').value;

    fetch('/study/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            subject_id: parseInt(subjectId),
            duration_minutes: parseFloat(durationMinutes.toFixed(2))
        })
    })
    .then(function (response) { return response.json(); })
    .then(function (data) {
        if (data.success) {
            showToast('Study session saved! Duration: ' + formatDuration(savedSeconds), 'success');
            timerSeconds = 0;
            updateTimerDisplay();
            toggleTimerButtons('stopped');
        } else {
            showToast('Error saving session: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(function () {
        showToast('Error saving study session. Please try again.', 'error');
    });
}

function toggleTimerButtons(state) {
    const startBtn = document.getElementById('timerStart');
    const pauseBtn = document.getElementById('timerPause');
    const resumeBtn = document.getElementById('timerResume');
    const stopBtn = document.getElementById('timerStop');

    if (!startBtn) return;

    if (state === 'running') {
        startBtn.style.display = 'none';
        pauseBtn.style.display = 'inline-block';
        resumeBtn.style.display = 'none';
        stopBtn.style.display = 'inline-block';
    } else if (state === 'paused') {
        startBtn.style.display = 'none';
        pauseBtn.style.display = 'none';
        resumeBtn.style.display = 'inline-block';
        stopBtn.style.display = 'inline-block';
    } else {
        startBtn.style.display = 'inline-block';
        pauseBtn.style.display = 'none';
        resumeBtn.style.display = 'none';
        stopBtn.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    var alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            var closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) closeBtn.click();
        }, 4000);
    });
    setupConfirmDeleteForms();
    setupColourBubbles();
    setupDropZone();
});

function showFileName(input) {
    var display = document.getElementById('fileNameDisplay');
    if (input.files && input.files.length > 0 && display) {
        display.textContent = 'Selected: ' + input.files[0].name;
        display.style.display = 'block';
    }
}

function setupDropZone() {
    var dropZone = document.getElementById('dropZone');
    var pdfInput = document.getElementById('pdfInput');
    if (!dropZone || !pdfInput) return;

    ['dragenter', 'dragover'].forEach(function (evt) {
        dropZone.addEventListener(evt, function (e) {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(function (evt) {
        dropZone.addEventListener(evt, function (e) {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', function (e) {
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            pdfInput.files = e.dataTransfer.files;
            showFileName(pdfInput);
        }
    });
}