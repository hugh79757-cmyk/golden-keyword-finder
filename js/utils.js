function showToast(message, duration = CONFIG.toastDuration) {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    
    if (toast && toastMessage) {
        toastMessage.textContent = message;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), duration);
    }
}

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            return true;
        } catch (e) {
            return false;
        } finally {
            document.body.removeChild(textarea);
        }
    }
}

async function copyKeyword(keyword, btn) {
    const success = await copyToClipboard(keyword);
    
    if (success) {
        btn.classList.add('copied');
        btn.innerHTML = '<i data-lucide="check"></i> 복사됨';
        lucide.createIcons();
        showToast(`'${keyword}' 클립보드에 복사됨`);
        
        setTimeout(() => {
            btn.classList.remove('copied');
            btn.innerHTML = '<i data-lucide="copy"></i> 복사';
            lucide.createIcons();
        }, 1500);
    }
}

function formatNumber(num) {
    return num.toLocaleString('ko-KR');
}

function formatDate(date = new Date()) {
    return date.toLocaleDateString('ko-KR');
}

function formatDateTime(date = new Date()) {
    return date.toLocaleString('ko-KR');
}

function getDeviceInfo() {
    const ua = navigator.userAgent.toLowerCase();
    return {
        isIOS: /ipad|iphone|ipod/.test(ua),
        isAndroid: /android/.test(ua),
        isMobile: /mobile|android|iphone|ipad|ipod/.test(ua),
        isStandalone: window.matchMedia('(display-mode: standalone)').matches
    };
}
