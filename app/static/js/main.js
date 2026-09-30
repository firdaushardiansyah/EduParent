/**
 * EduParent Frontend Script
 * Interactivity: Modals, Status Polling, Lucide Icons, and Form Previews
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Lucide Icons
    if (window.lucide) {
        window.lucide.createIcons();
    }

    // 2. Auto dismiss flash alerts after 6 seconds
    const flashMessages = document.querySelectorAll('.flash-alert');
    flashMessages.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 500);
        }, 6000);
    });

    // 3. Setup Modal Handlers
    window.openModal = function (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            document.body.style.overflow = 'hidden';
            if (window.lucide) window.lucide.createIcons();
        }
    };

    window.closeModal = function (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.style.overflow = '';
        }
    };

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-dialog:not(.hidden)').forEach(modal => {
                modal.classList.add('hidden');
                modal.classList.remove('flex');
                document.body.style.overflow = '';
            });
        }
    });

    // Close modal when clicking outside overlay
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                const parentModal = overlay.closest('.modal-dialog');
                if (parentModal) {
                    parentModal.classList.add('hidden');
                    parentModal.classList.remove('flex');
                    document.body.style.overflow = '';
                }
            }
        });
    });

    // 4. Image preview for file inputs
    document.querySelectorAll('input[type="file"][data-preview]').forEach(input => {
        input.addEventListener('change', function () {
            const previewId = this.getAttribute('data-preview');
            const previewEl = document.getElementById(previewId);
            if (previewEl && this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    previewEl.src = e.target.result;
                    previewEl.classList.remove('hidden');
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    });

    // 5. Real-Time Pickup Status Polling for Parent & Teacher views
    const pickupStatusWidget = document.getElementById('live-pickup-widget');
    if (pickupStatusWidget) {
        const studentId = pickupStatusWidget.getAttribute('data-student-id');
        if (studentId) {
            setInterval(() => {
                fetch(`/api/pickup/status/${studentId}`)
                    .then(res => res.json())
                    .then(data => {
                        const statusBadge = document.getElementById('live-pickup-badge');
                        const statusDetails = document.getElementById('live-pickup-details');
                        
                        if (statusBadge && data.status) {
                            if (data.status === 'SUDAH_DIJEMPUT') {
                                statusBadge.className = 'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold bg-teal-50 text-teal-700 border border-teal-200';
                                statusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-teal-500"></span> SUDAH DIJEMPUT`;
                                if (statusDetails) {
                                    statusDetails.innerHTML = `
                                        <div class="mt-3 p-3 bg-teal-50/70 border border-teal-100 rounded-xl text-xs space-y-1 text-teal-900">
                                            <p><span class="font-semibold text-teal-700">Penjemput:</span> ${data.collector_name || 'Orang Tua'}</p>
                                            <p><span class="font-semibold text-teal-700">Hubungan:</span> ${data.collector_relation || 'Keluarga'}</p>
                                            <p><span class="font-semibold text-teal-700">Waktu:</span> ${data.pickup_time || '-'}</p>
                                        </div>
                                    `;
                                }
                            } else {
                                statusBadge.className = 'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200 pulse-waiting';
                                statusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-500 animate-ping"></span> BELUM DIJEMPUT`;
                                if (statusDetails) {
                                    statusDetails.innerHTML = `<p class="mt-2 text-xs text-slate-500 italic">Anak saat ini berada di ruang tunggu sekolah dalam pengawasan guru.</p>`;
                                }
                            }
                        }
                    })
                    .catch(err => console.debug('Polling pickup error:', err));
            }, 8000); // Poll every 8s
        }
    }
});
