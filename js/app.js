// js/app.js - 메인 앱 로직

document.addEventListener('DOMContentLoaded', function() {
    console.log('앱 초기화 시작...');
    loadData();
    loadArchiveList();
});

// 데이터 로드
function loadData() {
    var apiUrl = 'output/data.json';
    if (typeof CONFIG !== 'undefined' && CONFIG.api) {
        apiUrl = CONFIG.api.data || apiUrl;
    }
    
    console.log('데이터 로드 시도:', apiUrl);
    
    fetch(apiUrl)
        .then(function(response) {
            console.log('데이터 응답 상태:', response.status);
            if (!response.ok) {
                throw new Error('데이터를 불러올 수 없습니다 (상태: ' + response.status + ')');
            }
            return response.json();
        })
        .then(function(data) {
            console.log('데이터 로드 성공:', data);
            renderDashboard(data);
            
            // 광고 초기화
            if (typeof AdsManager !== 'undefined') {
                AdsManager.initAllAds();
            }
        })
        .catch(function(error) {
            console.error('데이터 로드 실패:', error);
            var tbody = document.getElementById('keyword-table-body');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">데이터를 불러오는 중 오류가 발생했습니다: ' + error.message + '</td></tr>';
            }
        });
}

// 대시보드 렌더링
function renderDashboard(data) {
    console.log('대시보드 렌더링 시작');
    
    // 업데이트 시간 (한국 시간)
    var updateTime = document.getElementById('update-time');
    if (updateTime && data.generated_at) {
        console.log('generated_at:', data.generated_at);
        updateTime.textContent = formatDate(data.generated_at);
    }
    
    // SEO 요약
    var seoSummary = document.getElementById('seo-summary');
    if (seoSummary && data.seo_summary) {
        seoSummary.textContent = data.seo_summary;
    }
    
    // 키워드 총평
    var keywordReview = document.getElementById('keyword-review');
    if (keywordReview && data.keyword_review) {
        keywordReview.innerHTML = data.keyword_review.replace(/\n/g, '<br>');
    }
    
    // 통계 카드 업데이트
    updateStatsCards(data.keywords);
    
    // 키워드 테이블 렌더링
    renderKeywordTable(data.keywords);
    
    console.log('대시보드 렌더링 완료');
}

// 통계 카드 업데이트
function updateStatsCards(keywords) {
    if (!keywords || !keywords.length) {
        console.log('키워드 데이터 없음');
        return;
    }
    
    var totalKeywords = keywords.length;
    var diamondCount = 0;
    var blueOceanCount = 0;
    var sources = {};
    
    for (var i = 0; i < keywords.length; i++) {
        var k = keywords[i];
        if (k.grade && k.grade.indexOf('DIAMOND') !== -1) {
            diamondCount++;
        }
        if (k.efficiency && k.efficiency < 1.0) {
            blueOceanCount++;
        }
        if (k.source) {
            sources[k.source] = true;
        }
    }
    
    var sourceCount = Object.keys(sources).length;
    
    var statTotal = document.getElementById('stat-total');
    var statDiamond = document.getElementById('stat-diamond');
    var statBlueocean = document.getElementById('stat-blueocean');
    var statSources = document.getElementById('stat-sources');
    
    if (statTotal) statTotal.textContent = totalKeywords;
    if (statDiamond) statDiamond.textContent = diamondCount;
    if (statBlueocean) statBlueocean.textContent = blueOceanCount;
    if (statSources) statSources.textContent = sourceCount;
    
    console.log('통계:', { total: totalKeywords, diamond: diamondCount, blueOcean: blueOceanCount, sources: sourceCount });
}

// 키워드 테이블 렌더링
function renderKeywordTable(keywords) {
    var tbody = document.getElementById('keyword-table-body');
    if (!tbody) {
        console.error('keyword-table-body 요소를 찾을 수 없습니다');
        return;
    }
    
    if (!keywords || !keywords.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">표시할 키워드가 없습니다.</td></tr>';
        return;
    }
    
    var html = '';
    var adInterval = 5;
    if (typeof CONFIG !== 'undefined' && CONFIG.ads) {
        adInterval = CONFIG.ads.interval || 5;
    }
    
    for (var i = 0; i < keywords.length; i++) {
        // 광고 삽입
        if (i > 0 && i % adInterval === 0 && typeof AdsManager !== 'undefined') {
            html += AdsManager.createTableAdRow(6);
        }
        
        html += createKeywordRow(keywords[i]);
    }
    
    tbody.innerHTML = html;
    
    // 아이콘 재초기화
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    console.log('키워드 테이블 렌더링 완료:', keywords.length + '개');
}

// 키워드 행 생성
function createKeywordRow(item) {
    var sourceClass = item.source === 'NAVER' ? 'badge-naver' : 'badge-coupang';
    var sourceIcon = item.source === 'NAVER' ? 'shopping-bag' : 'shopping-cart';
    
    var gradeClass = 'grade-bad';
    var gradeIcon = '';
    
    if (item.grade && item.grade.indexOf('DIAMOND') !== -1) {
        gradeClass = 'grade-diamond';
        gradeIcon = '<i data-lucide="gem"></i>';
    } else if (item.grade && item.grade.indexOf('GOLD') !== -1) {
        gradeClass = 'grade-gold';
        gradeIcon = '<i data-lucide="star"></i>';
    } else if (item.grade && item.grade.indexOf('SILVER') !== -1) {
        gradeClass = 'grade-silver';
        gradeIcon = '<i data-lucide="sparkles"></i>';
    }
    
    var effClass = '';
    var effIcon = '';
    var efficiency = item.efficiency || 999;
    
    if (efficiency < 1.0) {
        effClass = 'eff-good';
        effIcon = '<i data-lucide="flame"></i>';
    } else if (efficiency > 5.0) {
        effClass = 'eff-bad';
        effIcon = '<i data-lucide="droplet"></i>';
    }
    
    var escapedKw = String(item.keyword).replace(/'/g, "\\'").replace(/"/g, '\\"');
    var searchVolume = item.search_volume ? Number(item.search_volume).toLocaleString() : '-';
    var blogCount = item.blog_count ? Number(item.blog_count).toLocaleString() : '-';
    var goldenScore = item.golden_score ? Number(item.golden_score).toFixed(1) : '-';
    var efficiencyDisplay = (efficiency !== 999) ? Number(efficiency).toFixed(2) : '-';
    
    return '<tr>' +
        '<td data-label="출처">' +
            '<span class="badge ' + sourceClass + '">' +
                '<i data-lucide="' + sourceIcon + '"></i> ' +
                item.source +
            '</span>' +
        '</td>' +
        '<td data-label="키워드">' +
            '<div class="keyword-cell">' +
                '<div class="keyword-info">' +
                    '<div class="keyword-name">' + item.keyword + '</div>' +
                    '<div class="keyword-grade">' +
                        '<span class="grade ' + gradeClass + '">' + gradeIcon + ' ' + item.grade + '</span>' +
                    '</div>' +
                '</div>' +
                '<div class="action-btns">' +
                    '<button class="action-btn copy" onclick="copyKeyword(\'' + escapedKw + '\', this)">' +
                        '<i data-lucide="copy"></i> 복사' +
                    '</button>' +
                    '<a class="action-btn analyze" href="https://search.naver.com/search.naver?query=' + encodeURIComponent(item.keyword) + '" target="_blank" rel="noopener">' +
                        '<i data-lucide="search"></i> 분석' +
                    '</a>' +
                '</div>' +
            '</div>' +
        '</td>' +
        '<td data-label="황금지수" class="num-col">' +
            '<span class="score-badge">' + goldenScore + '점</span>' +
        '</td>' +
        '<td data-label="경쟁강도" class="num-col">' +
            '<span class="efficiency ' + effClass + '">' + effIcon + ' ' + efficiencyDisplay + '</span>' +
        '</td>' +
        '<td data-label="검색량" class="num-col"><strong>' + searchVolume + '</strong></td>' +
        '<td data-label="블로그수" class="num-col">' + blogCount + '</td>' +
    '</tr>';
}

// ============================================
// 아카이브 관련 함수
// ============================================

// 아카이브 목록 로드
function loadArchiveList() {
    var apiUrl = 'output/archive_list.json';
    if (typeof CONFIG !== 'undefined' && CONFIG.api) {
        apiUrl = CONFIG.api.archiveList || apiUrl;
    }
    
    console.log('=== 아카이브 로드 시작 ===');
    console.log('아카이브 URL:', apiUrl);
    
    fetch(apiUrl)
        .then(function(response) {
            console.log('아카이브 응답 상태:', response.status);
            console.log('아카이브 응답 OK:', response.ok);
            
            if (!response.ok) {
                throw new Error('HTTP 오류: ' + response.status);
            }
            return response.json();
        })
        .then(function(files) {
            console.log('아카이브 파일 목록:', files);
            console.log('아카이브 파일 수:', files ? files.length : 0);
            
            if (files && files.length > 0) {
                renderArchiveList(files);
            } else {
                var container = document.getElementById('archive-list');
                if (container) {
                    container.innerHTML = '<li class="archive-empty">저장된 아카이브가 없습니다.</li>';
                }
            }
        })
        .catch(function(error) {
            console.error('=== 아카이브 로드 실패 ===');
            console.error('오류:', error.message);
            
            var container = document.getElementById('archive-list');
            if (container) {
                container.innerHTML = '<li class="archive-error">' +
                    '<i data-lucide="alert-circle"></i> ' +
                    '아카이브를 불러올 수 없습니다' +
                    '</li>';
                
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }
        });
}

// 아카이브 목록 렌더링
function renderArchiveList(files) {
    console.log('=== 아카이브 렌더링 시작 ===');
    
    var container = document.getElementById('archive-list');
    if (!container) {
        console.error('archive-list 컨테이너를 찾을 수 없습니다!');
        return;
    }
    
    console.log('컨테이너 찾음:', container);
    
    if (!files || !Array.isArray(files)) {
        console.error('파일 목록이 배열이 아닙니다:', files);
        container.innerHTML = '<li class="archive-empty">아카이브 데이터 형식 오류</li>';
        return;
    }
    
    if (files.length === 0) {
        container.innerHTML = '<li class="archive-empty">저장된 아카이브가 없습니다.</li>';
        return;
    }
    
    // 아카이브 경로 설정
    var archivePath = 'output/archives/';
    if (typeof CONFIG !== 'undefined' && CONFIG.api && CONFIG.api.archivePath) {
        archivePath = CONFIG.api.archivePath;
    }
    
    console.log('아카이브 경로:', archivePath);
    
    var html = '';
    var maxItems = Math.min(files.length, 10);
    
    for (var i = 0; i < maxItems; i++) {
        var file = files[i];
        console.log('처리 중인 파일 [' + i + ']:', file);
        
        // 파일명에서 날짜/시간 추출하여 보기 좋게 표시
        // 예: 2026-01-02_16h.html → 2026.01.02 16시
        var displayName = String(file)
            .replace('.html', '')
            .replace(/_/g, ' ')
            .replace(/-/g, '.')
            .replace(/(\d+)h/g, '$1시');
        
        var fullPath = archivePath + file;
        console.log('링크 경로:', fullPath);
        
        html += '<li class="archive-item">' +
            '<a href="' + fullPath + '" class="archive-link">' +
                '<i data-lucide="file-text"></i> ' +
                '<span class="archive-name">' + displayName + '</span>' +
                '<i data-lucide="chevron-right" class="archive-arrow"></i>' +
            '</a>' +
        '</li>';
    }
    
    // 10개 초과 시 안내
    if (files.length > 10) {
        html += '<li class="archive-more">' +
            '<i data-lucide="more-horizontal"></i> ' +
            '외 ' + (files.length - 10) + '개의 리포트' +
        '</li>';
    }
    
    console.log('생성된 HTML 길이:', html.length);
    container.innerHTML = html;
    
    // 아이콘 재초기화
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
        console.log('아이콘 초기화 완료');
    }
    
    console.log('=== 아카이브 렌더링 완료: ' + maxItems + '개 ===');
}

// 수동으로 아카이브 다시 로드 (디버깅용)
function reloadArchive() {
    console.log('아카이브 수동 재로드...');
    loadArchiveList();
}
