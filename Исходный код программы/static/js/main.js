// Подтверждение перед удалением
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.confirm-delete').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            const msg = form.dataset.confirm || 'Вы уверены, что хотите удалить запись? Это действие необратимо.';
            if (!confirm(msg)) {
                e.preventDefault();
            }
        });
    });

    // Автоматически скрыть уведомления через 5 секунд
    document.querySelectorAll('.alert').forEach(function (el) {
        setTimeout(function () {
            el.style.transition = 'opacity 0.5s';
            el.style.opacity = '0';
            setTimeout(function () { el.remove(); }, 500);
        }, 5000);
    });
});