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

function getCSRFToken() {
    var input = document.querySelector('input[name="csrf_token"]');
    if (input) return input.value;
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    return '';
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
});