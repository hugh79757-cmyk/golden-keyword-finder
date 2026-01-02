// js/utils.js - 유틸리티 함수 모음

/**
 * 토스트 메시지 표시
 */
function showToast(message, duration) {
    var toastDuration = duration || 2500;
    if (typeof CONFIG !== 'undefined' && CONFIG.toastDuration) {
        toastDuration = duration || CONFIG.toastDuration;
    }
    
    var toast = document.getElementById('toast');
    var toastMessage = document.getElementById('toast-message');
    
    if (toast && toastMessage) {
        toastMessage.textContent = message;
        toast.classList.add('show');
        setTimeout(function() {
            toast.classList.remove('show');
        }, toastDuration);
    } else {
        console.log(message);
    }
}

/**
 * 클립보드에 텍스트 복사
 */
function copyToClipboard(text) {
    return new Promise(function(resolve) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text)
                .then(function() { resolve(true); })
                .catch(function() { resolve(fallbackCopy(text)); });
        } else {
            resolve(fallbackCopy(text));
        }
    });
}

/**
 * 클립보드 복사 대체 방법
 */
function fallbackCopy(text) {
    var textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        document.execCommand('copy');
        document.body.removeChild(textarea);
        return true;
    } catch (e) {
        document.body.removeChild(textarea);
        return false;
    }
}

/**
 * 키워드 복사 (버튼 상태 변경 포함)
 */
function copyKeyword(keyword, btn) {
    copyToClipboard(keyword).then(function(success) {
        if (success) {
            if (btn) {
                btn.classList.add('copied');
                btn.innerHTML = '<i data-lucide="check"></i> 복사됨';
                
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
                
                setTimeout(function() {
                    btn.classList.remove('copied');
                    btn.innerHTML = '<i data-lucide="copy"></i> 복사';
                    if (typeof lucide !== 'undefined') {
                        lucide.createIcons();
                    }
                }, 1500);
            }
            showToast("'" + keyword + "' 클립보드에 복사됨");
        } else {
            showToast('복사에 실패했습니다');
        }
    });
}

/**
 * 날짜 포맷팅 (한국 시간 KST 기준)
 * data.json의 generated_at 문자열을 받아서 한국 시간으로 표시
 */
function formatDate(dateInput) {
    // 입력값이 없으면
    if (!dateInput) {
        return '-';
    }
    
    var date;
    
    // 문자열인 경우 Date 객체로 변환
    if (typeof dateInput === 'string') {
        date = new Date(dateInput);
    } else if (dateInput instanceof Date) {
        date = dateInput;
    } else {
        return '-';
    }
    
    // 유효한 날짜인지 확인
    if (isNaN(date.getTime())) {
        return '-';
    }
    
    try {
        // 한국 시간으로 표시
        return date.toLocaleString('ko-KR', {
            timeZone: 'Asia/Seoul',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    } catch (e) {
        // toLocaleString 실패 시 수동 포맷
        try {
            var year = date.getFullYear();
            var month = date.getMonth() + 1;
            var day = date.getDate();
            var hours = date.getHours();
            var minutes = date.getMinutes();
            
            return year + '년 ' + month + '월 ' + day + '일 ' + 
                   padZero(hours) + ':' + padZero(minutes);
        } catch (e2) {
            return String(dateInput);
        }
    }
}

/**
 * 날짜만 포맷팅
 */
function formatDateOnly(dateInput) {
    if (!dateInput) return '-';
    
    var date;
    if (typeof dateInput === 'string') {
        date = new Date(dateInput);
    } else if (dateInput instanceof Date) {
        date = dateInput;
    } else {
        return '-';
    }
    
    if (isNaN(date.getTime())) return '-';
    
    try {
        return date.toLocaleDateString('ko-KR', {
            timeZone: 'Asia/Seoul',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch (e) {
        var year = date.getFullYear();
        var month = date.getMonth() + 1;
        var day = date.getDate();
        return year + '년 ' + month + '월 ' + day + '일';
    }
}

/**
 * 날짜+시간 포맷팅
 */
function formatDateTime(dateInput) {
    return formatDate(dateInput);
}

/**
 * 숫자 앞에 0 붙이기
 */
function padZero(num) {
    return (num < 10 ? '0' : '') + num;
}

/**
 * 숫자 천단위 콤마 포맷팅
 */
function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) {
        return '-';
    }
    
    try {
        return Number(num).toLocaleString('ko-KR');
    } catch (e) {
        return String(num).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
}

/**
 * 등급에 따른 CSS 클래스 반환
 */
function getGradeClass(grade) {
    if (!grade) return 'grade-bad';
    
    var gradeStr = String(grade);
    if (gradeStr.indexOf('DIAMOND') !== -1) return 'grade-diamond';
    if (gradeStr.indexOf('GOLD') !== -1) return 'grade-gold';
    if (gradeStr.indexOf('SILVER') !== -1) return 'grade-silver';
    
    return 'grade-bad';
}

/**
 * 경쟁강도에 따른 CSS 클래스 반환
 */
function getEfficiencyClass(efficiency) {
    if (efficiency === null || efficiency === undefined) return '';
    if (efficiency < 1.0) return 'eff-good';
    if (efficiency > 5.0) return 'eff-bad';
    return '';
}

/**
 * 디바이스 정보 가져오기
 */
function getDeviceInfo() {
    var ua = navigator.userAgent.toLowerCase();
    return {
        isIOS: /ipad|iphone|ipod/.test(ua),
        isAndroid: /android/.test(ua),
        isMobile: /mobile|android|iphone|ipad|ipod/.test(ua),
        isStandalone: window.matchMedia('(display-mode: standalone)').matches
    };
}

/**
 * URL 파라미터 가져오기
 */
function getUrlParam(name) {
    var urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

/**
 * 디바운스 함수
 */
function debounce(func, wait) {
    var timeout;
    return function() {
        var context = this;
        var args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(function() {
            func.apply(context, args);
        }, wait || 300);
    };
}

/**
 * 로딩 표시/숨김
 */
function toggleLoading(show) {
    var loader = document.getElementById('loading');
    if (loader) {
        loader.style.display = show ? 'flex' : 'none';
    }
}

/**
 * 에러 메시지 표시
 */
function showError(message, container) {
    var html = '<div class="error-message">' +
        '<i data-lucide="alert-circle"></i> ' +
        '<span>' + message + '</span>' +
        '</div>';
    
    if (container) {
        container.innerHTML = html;
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
}
