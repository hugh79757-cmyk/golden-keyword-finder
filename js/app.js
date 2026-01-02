// js/app.js - 메인 앱 로직 (에러 방지 강화)

document.addEventListener('DOMContentLoaded', function() {
    console.log('=== 앱 시작 ===');
    
    try {
        loadData();
        loadArchiveList();
    } catch (e) {
        console.error('초기화 오류:', e);
    }
});

// 데이터 로드
function loadData() {
    var apiUrl = 'output/data.json';
    
    console.log('데이터 로드:', apiUrl);
    
    fetch(apiUrl)
        .then(function(response) {
            console.log('응답 상태:', response.status);
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }
            return response.json();
        })
        .then(function(data) {
            console.log('데이터 수신 완료');
            
            if (!data || !data.keywords) {
                throw new Error('데이터 형식 오류');
            }
            
            renderDashboard(data);
        })
        .catch(function(error) {
            console.error('로드 실패:', error);
            showTableError('데이터 로드 실패: ' + error.message);
        });
}

// 테이블 에러 표시
function showTableError(message) {
    var tbody = document.getElementById('keyword-table-body');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;">' + message + '</td></tr>';
    }
}

// 대시보드 렌더링
function renderDashboard(data) {
    console.log('렌더링 시작');
    
    // 업데이트 시간
    var updateTime = document.getElementById('update-time');
    if (updateTime && data.generated_at) {
        try {
            updateTime.textContent = formatDate(data.generated_at);
        } catch (e) {
            updateTime.textContent = data.generated_at;
        }
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
    
    // 통계 업데이트
    updateStats(data.keywords);
    
    // 테이블 렌더링
    renderTable(data.keywords);
    
    console.log('렌더링 완료');
}

// 통계 업데이트
function updateStats(keywords) {
    if (!keywords) return;
    
    var total = keywords.length;
    var diamond = 0;
    var blueocean = 0;
    var sources = {};
    
    for (var i = 0; i < keywords.length; i++) {
        var k = keywords[i];
        if (k.grade && k.grade.indexOf('DIAMOND') >= 0) diamond++;
        if (k.efficiency && k.efficiency < 1.0) blueocean++;
        if (k.source) sources[k.source] = true;
    }
    
    var sourceCount = Object.keys(sources).length;
    
    setElementText('stat-total', total);
    setElementText('stat-diamond', diamond);
    setElementText('stat-blueocean', blueocean);
    setElementText('stat-sources', sourceCount);
}

// 요소 텍스트 설정 (안전)
function setElementText(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
}

// 테이블 렌더링
function renderTable(keywords) {
    var tbody = document.getElementById('keyword-table-body');
    if (!tbody) {
        console.error('테이블 tbody 없음');
        return;
    }
    
    if (!keywords || keywords.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">키워드가 없습니다</td></tr>';
        return;
    }
    
    var html = '';
    
    for (var i = 0; i < keywords.length; i++) {
        var item = keywords[i];
        
        // 검색량 0인 항목 스킵 (프론트엔드 필터링)
        if (!item.search_volume || item.search_volume === 0) {
            continue;
        }
        
        html += createRow(item);
    }
    
    if (html === '') {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">유효한 키워드가 없습니다</td></tr>';
        return;
    }
    
    tbody.innerHTML = html;
    
    // 아이콘 초기화
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// 테이블 행 생성
function createRow(item) {
    var sourceClass = item.source === 'NAVER' ? 'badge-naver' : 'badge-coupang';
    var sourceIcon = item.source === 'NAVER' ? 'shopping-bag' : 'shopping-cart';
    
    var gradeClass = 'grade-bad';
    var gradeIcon = '';
    var grade = item.grade || 'Normal';
    
    if (grade.indexOf('DIAMOND') >= 0) {
        gradeClass = 'grade-diamond';
        gradeIcon = '<i data-lucide="gem"></i>';
    } else if (grade.indexOf('GOLD') >= 0) {
        gradeClass = 'grade-gold';
        gradeIcon = '<i data-lucide="star"></i>';
    } else if (grade.indexOf('SILVER') >= 0) {
        gradeClass = 'grade-silver';
        gradeIcon = '<i data-lucide="sparkles"></i>';
    }
    
    var effClass = '';
    var effIcon = '';
    var eff = item.efficiency || 999;
    
    if (eff < 1.0) {
        effClass = 'eff-good';
        effIcon = '<i data-lucide="flame"></i>';
    } else if (eff > 5.0) {
        effClass = 'eff-bad';
        effIcon = '<i data-lucide="droplet"></i>';
    }
    
    var keyword = item.keyword || '';
    var escapedKw = keyword.replace(/'/g, "\\'").replace(/"/g, '\\"');
    var vol = item.search_volume ? Number(item.search_volume).toLocaleString() : '-';
    var blog = item.blog_count ? Number(item.blog_count).toLocaleString() : '-';
    var score = item.golden_score ? Number(item.golden_score).toFixed(1) : '-';
    var effDisplay = (eff < 999) ? eff.toFixed(2) : '-';
    
    return '<tr>' +
        '<td data-label="출처"><span class="badge ' + sourceClass + '"><i data-lucide="' + sourceIcon + '"></i> ' + item.source + '</span></td>' +
        '<td data-label="키워드"><div class="keyword-cell"><div class="keyword-info"><div class="keyword-name">' + keyword + '</div><div class="keyword-grade"><span class="grade ' + gradeClass + '">' + gradeIcon + ' ' + grade + '</span></div></div><div class="action-btns"><button class="action-btn copy" onclick="copyKeyword(\'' + escapedKw + '\', this)"><i data-lucide="copy"></i> 복사</button><a class="action-btn analyze" href="https://search.naver.com/search.naver?query=' + encodeURIComponent(keyword) + '" target="_blank" rel="noopener"><i data-lucide="search"></i> 분석</a></div></div></td>' +
        '<td data-label="황금지수" class="num-col"><span class="score-badge">' + score + '점</span></td>' +
        '<td data-label="경쟁강도" class="num-col"><span class="efficiency ' + effClass + '">' + effIcon + ' ' + effDisplay + '</span></td>' +
        '<td data-label="검색량" class="num-col"><strong>' + vol + '</strong></td>' +
        '<td data-label="블로그수" class="num-col">' + blog + '</td>' +
    '</tr>';
}

// 아카이브 로드
function loadArchiveList() {
    var apiUrl = 'output/archive_list.json';
    
    console.log('아카이브 로드:', apiUrl);
    
    fetch(apiUrl)
        .then(function(response) {
            if (!response.ok) throw new Error('HTTP ' + response.status);
            return response.json();
        })
        .then(function(files) {
            console.log('아카이브 파일:', files);
            renderArchiveList(files);
        })
        .catch(function(error) {
            console.error('아카이브 로드 실패:', error);
            var container = document.getElementById('archive-list');
            if (container) {
                container.innerHTML = '<li>아카이브 로드 실패</li>';
            }
        });
}

// 아카이브 목록 렌더링
function renderArchiveList(files) {
    var container = document.getElementById('archive-list');
    if (!container) return;
    
    if (!files || files.length === 0) {
        container.innerHTML = '<li>저장된 아카이브가 없습니다</li>';
        return;
    }
    
    var html = '';
    var max = Math.min(files.length, 10);
    
    for (var i = 0; i < max; i++) {
        var file = files[i];
        var name = file.replace('.html', '').replace(/_/g, ' ').replace(/-/g, '.').replace(/(\d+)h/g, '$1시');
        
        html += '<li class="archive-item"><a href="output/archives/' + file + '" class="archive-link"><i data-lucide="file-text"></i> <span>' + name + '</span></a></li>';
    }
    
    container.innerHTML = html;
    
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}
