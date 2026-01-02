function showModal({ title, content, icon = 'info' }) {
    closeModal();
    
    const modal = document.createElement('div');
    modal.id = 'modal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-overlay" onclick="closeModal()"></div>
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-icon"><i data-lucide="${icon}"></i></div>
                <h3 class="modal-title">${title}</h3>
                <button class="modal-close" onclick="closeModal()"><i data-lucide="x"></i></button>
            </div>
            <div class="modal-body">${content}</div>
        </div>
    `;
    
    document.getElementById('modal-container').appendChild(modal);
    lucide.createIcons();
    requestAnimationFrame(() => modal.classList.add('show'));
    document.addEventListener('keydown', handleModalEsc);
}

function closeModal() {
    const modal = document.getElementById('modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.remove(), 200);
    }
    document.removeEventListener('keydown', handleModalEsc);
}

function handleModalEsc(e) {
    if (e.key === 'Escape') closeModal();
}

(function addModalStyles() {
    if (document.getElementById('modal-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'modal-styles';
    style.textContent = `
        .modal { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 20px; opacity: 0; visibility: hidden; transition: var(--transition); }
        .modal.show { opacity: 1; visibility: visible; }
        .modal-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.8); backdrop-filter: blur(4px); }
        .modal-content { position: relative; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-xl); max-width: 400px; width: 100%; transform: translateY(20px); transition: var(--transition); }
        .modal.show .modal-content { transform: translateY(0); }
        .modal-header { display: flex; align-items: center; gap: 12px; padding: 20px 24px; border-bottom: 1px solid var(--border-color); }
        .modal-icon { width: 40px; height: 40px; background: var(--bg-secondary); border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center; color: var(--diamond-light); }
        .modal-icon svg { width: 20px; height: 20px; }
        .modal-title { flex: 1; font-size: 1rem; font-weight: 700; }
        .modal-close { width: 32px; height: 32px; border: none; background: transparent; color: var(--text-muted); cursor: pointer; border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center; transition: var(--transition); }
        .modal-close:hover { background: var(--bg-secondary); color: var(--text-primary); }
        .modal-close svg { width: 18px; height: 18px; }
        .modal-body { padding: 24px; color: var(--text-secondary); font-size: 0.9rem; line-height: 1.7; }
        .modal-body strong { color: var(--text-primary); }
        .modal-body ol, .modal-body ul { color: var(--text-primary); margin: 12px 0; padding-left: 20px; }
    `;
    document.head.appendChild(style);
})();
