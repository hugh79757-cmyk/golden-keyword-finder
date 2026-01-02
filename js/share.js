const SHARE_ICONS = {
    kakao: `<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M12 3c-5.52 0-10 3.59-10 8 0 2.79 1.86 5.24 4.66 6.62-.2.76-.73 2.75-.84 3.18-.13.54.2.53.42.39.17-.12 2.75-1.87 3.86-2.64.62.09 1.25.14 1.9.14 5.52 0 10-3.59 10-8s-4.48-8-10-8z"/></svg>`,
    x: `<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>`,
    threads: `<svg viewBox="0 0 192 192" width="16" height="16" fill="currentColor"><path d="M141.537 88.988a66.667 66.667 0 0 0-2.518-1.143c-1.482-27.307-16.403-42.94-41.457-43.1h-.34c-14.986 0-27.449 6.396-35.12 18.036l13.779 9.452c5.73-8.695 14.724-10.548 21.348-10.548h.229c8.249.053 14.474 2.452 18.503 7.129 2.932 3.405 4.893 8.111 5.864 14.05-7.314-1.243-15.224-1.626-23.68-1.14-23.82 1.371-39.134 15.24-38.37 34.767.39 9.964 4.882 18.558 12.651 24.186 6.56 4.751 15.015 7.165 23.793 6.795 11.56-.488 20.633-4.828 26.987-12.905 4.795-6.086 7.88-13.99 9.228-23.698 5.538 3.342 9.653 7.848 11.988 13.306 3.968 9.269 4.202 24.498-8.288 36.988-10.978 10.978-24.193 15.737-44.16 15.903-22.14-.184-38.918-7.261-49.9-21.035C52.996 140.057 47.033 119.103 47 96c.033-23.103 5.996-44.057 17.737-62.334 10.982-13.774 27.76-20.851 49.9-21.035 22.262.188 39.265 7.316 50.527 21.19 5.508 6.791 9.686 15.202 12.438 24.857l15.14-4.07c-3.18-11.212-8.224-21.25-15.023-29.626C163.749 7.752 142.136-.292 116.154 0h-.327C89.918.295 68.533 8.452 54.49 26.86 38.816 47.479 30.803 75.693 30.763 96c.04 20.307 8.053 48.521 23.727 69.14 14.043 18.408 35.428 26.565 61.364 26.86h.327c24.922-.191 41.924-6.397 56.612-21.085 18.704-18.703 18.09-41.9 12.009-56.106-4.37-10.21-12.811-18.387-24.265-23.82zm-42.282 48.659c-9.676.463-19.733-3.794-20.156-14.609-.304-7.796 5.528-16.501 25.493-17.654 2.237-.129 4.424-.177 6.561-.177 6.081 0 11.781.527 16.985 1.527-1.527 22.955-16.559 30.379-28.883 30.913z"/></svg>`,
    facebook: `<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>`
};

function renderShareButtons() {
    const headerContainer = document.getElementById('social-share');
    const footerContainer = document.getElementById('footer-social');
    
    const buttons = `
        <button class="share-btn kakao" onclick="shareKakao()" title="카카오톡">${SHARE_ICONS.kakao}</button>
        <button class="share-btn x" onclick="shareX()" title="X">${SHARE_ICONS.x}</button>
        <button class="share-btn threads" onclick="shareThreads()" title="스레드">${SHARE_ICONS.threads}</button>
        <button class="share-btn facebook" onclick="shareFacebook()" title="페이스북">${SHARE_ICONS.facebook}</button>
        <button class="share-btn native" onclick="shareNative()" title="공유"><i data-lucide="share-2"></i></button>
        <button class="share-btn bookmark" onclick="addToHome()" title="홈 추가"><i data-lucide="plus-square"></i></button>
    `;
    
    if (headerContainer) headerContainer.innerHTML = buttons;
    if (footerContainer) footerContainer.innerHTML = `
        <button class="share-btn kakao" onclick="shareKakao()">${SHARE_ICONS.kakao}</button>
        <button class="share-btn x" onclick="shareX()">${SHARE_ICONS.x}</button>
        <button class="share-btn threads" onclick="shareThreads()">${SHARE_ICONS.threads}</button>
        <button class="share-btn facebook" onclick="shareFacebook()">${SHARE_ICONS.facebook}</button>
    `;
    
    lucide.createIcons();
}

function shareKakao() {
    if (CONFIG.kakao.enabled && window.Kakao) {
        if (!Kakao.isInitialized()) Kakao.init(CONFIG.kakao.appKey);
        Kakao.Share.sendDefault({
            objectType: 'feed',
            content: { title: CONFIG.site.title, description: CONFIG.site.description, imageUrl: CONFIG.site.image, link: { mobileWebUrl: CONFIG.site.url, webUrl: CONFIG.site.url } }
        });
    } else {
        if (navigator.share) shareNative();
        else { copyLink(); showToast('링크가 복사되었습니다!'); }
    }
}

function shareX() {
    const text = encodeURIComponent(`${CONFIG.site.title} - ${CONFIG.site.description}`);
    const url = encodeURIComponent(CONFIG.site.url);
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, 'share-x', 'width=550,height=450');
}

function shareThreads() {
    const text = encodeURIComponent(`${CONFIG.site.title}\n\n${CONFIG.site.description}\n\n${CONFIG.site.url}`);
    window.open(`https://www.threads.net/intent/post?text=${text}`, 'share-threads', 'width=550,height=600');
}

function shareFacebook() {
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(CONFIG.site.url)}`, 'share-fb', 'width=550,height=450');
}

async function shareNative() {
    if (navigator.share) {
        try {
            await navigator.share({ title: CONFIG.site.title, text: CONFIG.site.description, url: CONFIG.site.url });
        } catch (err) { if (err.name !== 'AbortError') copyLink(); }
    } else copyLink();
}

async function copyLink() {
    const success = await copyToClipboard(CONFIG.site.url);
    if (success) showToast('링크가 복사되었습니다!');
}

let deferredPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); deferredPrompt = e; });

async function addToHome() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') showToast('홈 화면에 추가되었습니다!');
        deferredPrompt = null;
        return;
    }
    
    const device = getDeviceInfo();
    
    if (device.isIOS && !device.isStandalone) {
        showModal({ title: '홈 화면에 추가', icon: 'smartphone', content: '<p><strong>Safari에서:</strong></p><ol><li>공유 버튼 (□↑) 탭</li><li>"홈 화면에 추가" 선택</li></ol>' });
        return;
    }
    
    if (device.isAndroid) {
        showModal({ title: '홈 화면에 추가', icon: 'smartphone', content: '<p><strong>Chrome에서:</strong></p><ol><li>메뉴 (⋮) 탭</li><li>"홈 화면에 추가" 선택</li></ol>' });
        return;
    }
    
    showModal({ title: '바로가기 추가', icon: 'bookmark', content: '<p>Ctrl+D (Windows) 또는 ⌘+D (Mac)으로 북마크하세요</p><button onclick="copyLink();closeModal();" class="btn" style="width:100%;margin-top:16px;"><i data-lucide="link"></i> 링크 복사</button>' });
    lucide.createIcons();
}

document.addEventListener('DOMContentLoaded', renderShareButtons);
