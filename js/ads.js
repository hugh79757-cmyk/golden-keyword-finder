// js/ads.js - 광고 관리 모듈

const AdsManager = {
    // 인라인 광고 HTML 생성
    createInlineAd: function(index = 0) {
        if (!CONFIG.ads.enabled) return '';
        
        return `
            <div class="ad-container ad-inline" data-ad-index="${index}">
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="${CONFIG.ads.client}"
                     data-ad-slot="${CONFIG.ads.slot}"
                     data-ad-format="auto"
                     data-full-width-responsive="true"></ins>
            </div>
        `;
    },

    // 사이드레일 광고 HTML 생성
    createSideAd: function(position = 'left') {
        if (!CONFIG.ads.enabled) return '';
        
        return `
            <div class="ad-container ad-side ad-${position}">
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="${CONFIG.ads.client}"
                     data-ad-slot="${CONFIG.ads.slot}"
                     data-ad-format="vertical"
                     data-full-width-responsive="false"></ins>
            </div>
        `;
    },

    // 테이블 중간에 삽입할 광고 행 생성
    createTableAdRow: function(colSpan = 7) {
        if (!CONFIG.ads.enabled) return '';
        
        return `
            <tr class="ad-row">
                <td colspan="${colSpan}" class="ad-cell">
                    <ins class="adsbygoogle"
                         style="display:block"
                         data-ad-client="${CONFIG.ads.client}"
                         data-ad-slot="${CONFIG.ads.slot}"
                         data-ad-format="horizontal"
                         data-full-width-responsive="true"></ins>
                </td>
            </tr>
        `;
    },

    // 카드형 레이아웃(모바일)용 광고
    createCardAd: function() {
        if (!CONFIG.ads.enabled) return '';
        
        return `
            <article class="keyword-card ad-card">
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="${CONFIG.ads.client}"
                     data-ad-slot="${CONFIG.ads.slot}"
                     data-ad-format="fluid"
                     data-ad-layout-key="-6t+ed+2i-1n-4w"></ins>
            </article>
        `;
    },

    // 모든 광고 초기화 (페이지 로드 후 호출)
    initAllAds: function() {
        if (!CONFIG.ads.enabled) return;
        
        // 약간의 지연 후 광고 초기화 (DOM 완전 로드 보장)
        setTimeout(() => {
            const ads = document.querySelectorAll('.adsbygoogle:not([data-adsbygoogle-status])');
            ads.forEach(() => {
                try {
                    (adsbygoogle = window.adsbygoogle || []).push({});
                } catch (e) {
                    console.log('AdSense 로드 중...');
                }
            });
        }, 100);
    },

    // 동적으로 추가된 광고 초기화
    initNewAds: function(container) {
        if (!CONFIG.ads.enabled) return;
        
        const ads = container.querySelectorAll('.adsbygoogle:not([data-adsbygoogle-status])');
        ads.forEach(() => {
            try {
                (adsbygoogle = window.adsbygoogle || []).push({});
            } catch (e) {
                console.log('AdSense 로드 중...');
            }
        });
    }
};
