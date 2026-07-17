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
    setupFlashcardDeck();
    setupSettings();
    setupTour();
});

function pickFile(acceptTypes) {
    var input = document.getElementById('taskFileInput');
    if (!input) return;
    input.setAttribute('accept', acceptTypes);
    input.click();
}

function showFileName(input) {
    var display = document.getElementById('fileNameDisplay');
    if (!display) return;
    if (!input.files || input.files.length === 0) {
        clearFile();
        return;
    }

    var existing = document.getElementById('existingFileCard');
    if (existing) existing.style.display = 'none';

    var file = input.files[0];
    var sizeKB = file.size / 1024;
    var sizeText = sizeKB > 1024 ? (sizeKB / 1024).toFixed(1) + ' MB' : Math.round(sizeKB) + ' KB';
    var lowerName = file.name.toLowerCase();
    var icon = 'bi-file-earmark-text';
    if (lowerName.endsWith('.pdf')) icon = 'bi-file-earmark-pdf';
    else if (lowerName.endsWith('.docx') || lowerName.endsWith('.doc')) icon = 'bi-file-earmark-word';

    display.innerHTML =
        '<div class="file-preview-card">' +
            '<i class="bi ' + icon + ' file-preview-icon"></i>' +
            '<div class="file-preview-info">' +
                '<div class="file-preview-name"></div>' +
                '<div class="file-preview-size">' + sizeText + '</div>' +
            '</div>' +
            '<button type="button" class="file-preview-remove" onclick="clearFile()">&times;</button>' +
        '</div>';
    display.querySelector('.file-preview-name').textContent = file.name;
    display.style.display = 'block';
}

function removeExistingFile() {
    var card = document.getElementById('existingFileCard');
    var flag = document.getElementById('removeTaskFile');
    if (flag) flag.value = '1';
    if (card) card.style.display = 'none';
}

function clearFile() {
    var input = document.getElementById('taskFileInput');
    if (input) input.value = '';
    var display = document.getElementById('fileNameDisplay');
    if (!display) return;
    display.style.display = 'none';
    display.innerHTML = '';
}

function setupDropZone() {
    var dropZone = document.getElementById('dropZone');
    var fileInput = document.getElementById('taskFileInput');
    if (!dropZone || !fileInput) return;

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
            fileInput.files = e.dataTransfer.files;
            showFileName(fileInput);
        }
    });
}

function toggleSubtask(btn, taskId) {
    var detail = document.getElementById('subtaskDetail' + taskId);
    if (!detail) return;
    var isOpen = detail.style.display !== 'none';
    detail.style.display = isOpen ? 'none' : 'block';
    btn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
    btn.setAttribute('title', isOpen ? 'Show details' : 'Hide details');
    btn.querySelector('i').className = isOpen ? 'bi bi-chevron-down' : 'bi bi-chevron-up';
}
var deck = [];
var deckIndex = 0;
var deckCorrect = 0;

function setupFlashcardDeck() {
    var data = document.getElementById('deckData');
    if (!data) return;
    deck = JSON.parse(data.textContent);
    restartDeck();
}

function shuffleDeck(list) {
    for (var i = list.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var temp = list[i];
        list[i] = list[j];
        list[j] = temp;
    }
}

function restartDeck() {
    shuffleDeck(deck);
    deckIndex = 0;
    deckCorrect = 0;
    showCard();
}

function showCard() {
    if (deckIndex >= deck.length) {
        showDeckSummary();
        return;
    }
    var card = deck[deckIndex];
    document.getElementById('cardQuestion').textContent = card.question;
    document.getElementById('cardAnswer').textContent = card.answer;
    document.getElementById('cardAnswer').style.display = 'none';
    document.getElementById('showAnswerBtn').style.display = 'inline-block';
    document.getElementById('markButtons').style.display = 'none';
    document.getElementById('cardProgress').textContent = 'Card ' + (deckIndex + 1) + ' of ' + deck.length;
    document.getElementById('deckSummary').style.display = 'none';
    document.getElementById('cardFace').style.display = 'block';
}

function showAnswer() {
    document.getElementById('cardAnswer').style.display = 'block';
    document.getElementById('showAnswerBtn').style.display = 'none';
    document.getElementById('markButtons').style.display = 'flex';
}

function markCard(wasCorrect) {
    var card = deck[deckIndex];
    var buttons = document.querySelectorAll('#markButtons button');
    buttons.forEach(function (b) { b.disabled = true; });

    fetch(card.review_url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ was_correct: wasCorrect })
    })
    .then(function (response) { return response.json(); })
    .then(function (data) {
        buttons.forEach(function (b) { b.disabled = false; });
        if (!data.success) {
            showToast(data.error || 'Could not save that answer.', 'error');
            return;
        }
        if (wasCorrect) deckCorrect++;
        deckIndex++;
        showCard();
    })
    .catch(function () {
        buttons.forEach(function (b) { b.disabled = false; });
        showToast('Could not save that answer. Please try again.', 'error');
    });
}

function showDeckSummary() {
    document.getElementById('cardFace').style.display = 'none';
    var pct = deck.length ? Math.round(deckCorrect / deck.length * 100) : 0;
    document.getElementById('summaryScore').textContent = deckCorrect + ' of ' + deck.length + ' (' + pct + '%)';
    document.getElementById('deckSummary').style.display = 'block';
}

var SB_SETTINGS_KEY = 'sbSettings';

function loadSettings() {
    try {
        return JSON.parse(localStorage.getItem(SB_SETTINGS_KEY) || '{}');
    } catch (e) {
        return {};
    }
}

function applySetting(name, cssClass, isOn) {
    document.documentElement.classList.toggle(cssClass, isOn);
    var settings = loadSettings();
    settings[name] = isOn;
    try {
        localStorage.setItem(SB_SETTINGS_KEY, JSON.stringify(settings));
    } catch (e) {
        showToast('That setting is on, but your browser would not save it.', 'error');
    }
}

function setupSettings() {
    var toggles = [
        ['largeText', 'sb-large-text', 'setLargeText'],
        ['highContrast', 'sb-high-contrast', 'setHighContrast'],
        ['reduceMotion', 'sb-reduce-motion', 'setReduceMotion']
    ];
    var saved = loadSettings();

    toggles.forEach(function (row) {
        var name = row[0], cssClass = row[1], id = row[2];
        var input = document.getElementById(id);
        if (!input) return;
        input.checked = !!saved[name];
        input.addEventListener('change', function () {
            applySetting(name, cssClass, input.checked);
        });
    });
}

var SB_TOUR = [
    {
        icon: 'bi-grid-1x2',
        title: 'Your dashboard',
        body: 'Everything due today, your study timer, and how each subject is tracking, all on one screen. Start here.'
    },
    {
        icon: 'bi-book',
        title: 'Start with your subjects',
        body: 'Add each HSC subject you take and give it a colour. That colour follows it everywhere, so you can spot Chemistry at a glance. Every assessment, note and flashcard are based on a subject.'
    },
    {
        icon: 'bi-magic',
        title: 'Add an assessment, get a plan',
        body: 'Upload your task notification as a PDF or Word file and the AI reads it, then breaks it into dated subtasks working backwards from the due date.'
    },
    {
        icon: 'bi-check2-square',
        title: 'Tick things off',
        body: 'Your subtasks land in Today automatically. Add your own to-dos alongside them. Tick one and it turns green and stays put, so you can see what you got done.'
    },
    {
        icon: 'bi-card-text',
        title: 'Find your weak topics',
        body: 'Make flashcards under a topic, then quiz yourself and mark each one right or wrong. Studyboard tracks every answer and tells you which topics need work and which you have nailed.'
    },
    {
        icon: 'bi-graph-up-arrow',
        title: 'Know where you stand',
        body: 'Record a mark and your predicted internal grade updates. Set a target and it tells you the average you need on what is left, or that you have already got there.'
    }
];

var tourIndex = 0;
var tourModalInstance = null;

function showTourStep() {
    var step = SB_TOUR[tourIndex];
    var last = tourIndex === SB_TOUR.length - 1;

    document.getElementById('tourIcon').className = 'bi ' + step.icon;
    document.getElementById('tourTitle').textContent = step.title;
    document.getElementById('tourBody').textContent = step.body;
    document.getElementById('tourStepText').textContent = 'Step ' + (tourIndex + 1) + ' of ' + SB_TOUR.length;

    var dots = '';
    for (var i = 0; i < SB_TOUR.length; i++) {
        dots += '<span class="sb-tour-dot' + (i === tourIndex ? ' active' : '') + '"></span>';
    }
    document.getElementById('tourDots').innerHTML = dots;

    document.getElementById('tourBack').style.display = tourIndex === 0 ? 'none' : 'inline-block';
    document.getElementById('tourSkip').style.display = last ? 'none' : 'inline-block';
    document.getElementById('tourNext').textContent = last ? 'Done' : 'Next';
}

function markTourSeen() {
    var el = document.getElementById('tourModal');
    if (!el || el.dataset.sbSeenSent) return;
    el.dataset.sbSeenSent = '1';

    fetch(el.getAttribute('data-sb-seen-url'), {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(function (response) {
        if (!response.ok) console.error('TOUR SEEN failed, status ' + response.status);
    })
    .catch(function (error) {
        console.error('TOUR SEEN network error:', error);
    });
}

function startTour() {
    var el = document.getElementById('tourModal');
    if (!el) return;
    tourIndex = 0;
    showTourStep();
    if (!tourModalInstance) tourModalInstance = new bootstrap.Modal(el);
    tourModalInstance.show();
}

function setupTour() {
    var el = document.getElementById('tourModal');
    if (!el) return;

    document.getElementById('tourNext').addEventListener('click', function () {
        if (tourIndex === SB_TOUR.length - 1) {
            markTourSeen();
            tourModalInstance.hide();
            return;
        }
        tourIndex++;
        showTourStep();
    });

    document.getElementById('tourBack').addEventListener('click', function () {
        if (tourIndex > 0) {
            tourIndex--;
            showTourStep();
        }
    });

    document.getElementById('tourSkip').addEventListener('click', markTourSeen);
    el.addEventListener('hidden.bs.modal', markTourSeen);

    var help = document.getElementById('helpBtn');
    if (help) {
        help.addEventListener('click', function () {
            var settingsEl = document.getElementById('settingsModal');
            var settings = bootstrap.Modal.getInstance(settingsEl);
            if (!settings) {
                startTour();
                return;
            }
            settingsEl.addEventListener('hidden.bs.modal', function once() {
                settingsEl.removeEventListener('hidden.bs.modal', once);
                startTour();
            });
            settings.hide();
        });
    }
    if (el.hasAttribute('data-sb-autostart')) {
        startTour();
    }
}