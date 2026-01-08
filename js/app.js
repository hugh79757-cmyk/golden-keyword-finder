// js/app.js - 메인 앱 로직 (광고 삽입 + 정렬 기능)

let currentKeywords = []; // 전역 데이터 저장
let currentSort = { column: null, ascending: true };

document.addEventListener('DOMContentLoaded', function() {
    loadData();
    loadArchiveList();
});

async function loadData() {
    try {
        const response = await fetch(CONFIG.api.data);
        if (!response.ok) throw new Error('데이터를 불러올 수 없습니다');
        
        const data = await response.json();
        currentKeywords = data.keywords || [];
        renderDashboard(data);
        
        // ✅ 데이터 로드 완료 후 광고 초기화
        AdsManager.initAllAds();
        
    } catch (error) {
        console.error('데이터 로드 실패:', error);
        document.getElementById('keyword-table-body').innerHTML = 
            '<tr><td colspan="7" class="text-center">데이터를 불러오는 중 오류가 발생했습니다.</td></tr>';
    }
}

function renderDashboard(data) {
    // 업데이트 시간
    const updateTime = document.getElementById('update-time');
    if (updateTime && data.generated_at) {
        updateTime.textContent = formatDate(data.generated_at);
    }
    
    // SEO 요약
    const seoSummary = document.getElementById('seo-summary');
    if (seoSummary && data.seo_summary) {
        seoSummary.textContent = data.seo_summary;
    }
    
    // 키워드 총평
    const keywordReview = document.getElementById('keyword-review');
    if (keywordReview && data.keyword_review) {
        keywordReview.textContent = data.keyword_review;
    }
    
    // 통계 카드 업데이트
    updateStatsCards(data.keywords);
    
    // 테이블 헤더에 정렬 기능 추가
    setupSortableHeaders();
    
    // 키워드 테이블 렌더링 (광고 포함)
    renderKeywordTable(currentKeywords);
}

function updateStatsCards(keywords) {
    if (!keywords) return;
    
    const totalKeywords = keywords.length;
    const diamondCount = keywords.filter(k => k.grade?.includes('DIAMOND')).length;
    const blueOceanCount = keywords.filter(k => k.efficiency < 1.0).length;
    const sourceCount = [...new Set(keywords.map(k => k.source))].length;
    
    const statTotal = document.getElementById('stat-total');
    const statDiamond = document.getElementById('stat-diamond');
    const statBlueocean = document.getElementById('stat-blueocean');
    const statSources = document.getElementById('stat-sources');
    
    if (statTotal) statTotal.textContent = totalKeywords;
    if (statDiamond) statDiamond.textContent = diamondCount;
    if (statBlueocean) statBlueocean.textContent = blueOceanCount;
    if (statSources) statSources.textContent = sourceCount;
}

// ✅ 정렬 가능한 헤더 설정
function setupSortableHeaders() {
    const headers = document.querySelectorAll('.keyword-table thead th');
    const sortableColumns = {
        3: 'golden_score',   // 황금지수
        4: 'efficiency',     // 경쟁강도
        5: 'search_volume',  // 월간검색량
        6: 'blog_count'      // 블로그수
    };
    
    headers.forEach((th, index) => {
        if (sortableColumns[index]) {
            th.style.cursor = 'pointer';
            th.dataset.column = sortableColumns[index];
            th.innerHTML += ' <span class="sort-icon">↕</span>';
            
            th.addEventListener('click', () => {
                sortTable(sortableColumns[index], th);
            });
        }
    });
}

// ✅ 테이블 정렬 함수
function sortTable(column, headerElement) {
    // 같은 컬럼 클릭 시 방향 전환
    if (currentSort.column === column) {
        currentSort.ascending = !currentSort.ascending;
    } else {
        currentSort.column = column;
        currentSort.ascending = false; // 기본 내림차순
    }
    
    // 정렬 실행
    currentKeywords.sort((a, b) => {
        let valA = a[column] ?? 0;
        let valB = b[column] ?? 0;
        
        if (currentSort.ascending) {
            return valA - valB;
        } else {
            return valB - valA;
        }
    });
    
    // 정렬 아이콘 업데이트
    document.querySelectorAll('.keyword-table thead th .sort-icon').forEach(icon => {
        icon.textContent = '↕';
    });
    const sortIcon = headerElement.querySelector('.sort-icon');
    if (sortIcon) {
        sortIcon.textContent = currentSort.ascending ? '↑' : '↓';
    }
    
    // 테이블 다시 렌더링
    renderKeywordTable(currentKeywords);
}

// ✅ 키워드 테이블 렌더링 (광고 삽입 포함)
function renderKeywordTable(keywords) {
    const tbody = document.getElementById('keyword-table-body');
    if (!tbody || !keywords) return;
    
    let html = '';
    const adInterval = CONFIG.ads.interval || 5;
    
    keywords.forEach((item, index) => {
        if (index > 0 && index % adInterval === 0) {
            html += AdsManager.createTableAdRow(7);
        }
        html += createKeywordRow(item);
    });
    
    tbody.innerHTML = html;
    
    // 아이콘 재초기화
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

function createKeywordRow(item) {
    const sourceClass = item.source === 'NAVER' ? 'source-naver' : 'source-coupang';
    const sourceIcon = item.source === 'NAVER' ? 'N' : 'C';
    const gradeClass = getGradeClass(item.grade);
    const efficiencyClass = item.efficiency < 1.0 ? 'eff-good' : 'eff-bad';
    const efficiencyIcon = item.efficiency < 1.0 ? 'droplet' : 'flame';
    
    return `
        <tr>
            <td>
                <span class="source-badge ${sourceClass}">
                    ${sourceIcon}
                </span>
            </td>
            <td class="keyword-cell">
                <span class="keyword-text">${item.keyword}</span>
                <div class="keyword-actions">
                    <button class="btn-icon btn-copy" onclick="copyKeyword('${item.keyword}')" title="복사">
                        <i data-lucide="copy"></i>
                    </button>
                    <a href="https://search.naver.com/search.naver?query=${encodeURIComponent(item.keyword)}" 
                       target="_blank" class="btn-icon btn-analyze" title="네이버 검색">
                        <i data-lucide="search"></i>
                    </a>
                </div>
            </td>
            <td>
                <span class="grade-badge ${gradeClass}">${item.grade}</span>
            </td>
            <td>
                <span class="score-badge">${item.golden_score?.toFixed(1) || '-'}</span>
            </td>
            <td>
                <span class="efficiency-badge ${efficiencyClass}">
                    <i data-lucide="${efficiencyIcon}"></i>
                    ${item.efficiency?.toFixed(2) || '-'}
                </span>
            </td>
            <td>${formatNumber(item.search_volume)}</td>
            <td>${formatNumber(item.blog_count)}</td>
        </tr>
    `;
}

function getGradeClass(grade) {
    if (!grade) return 'grade-bad';
    if (grade.includes('DIAMOND')) return 'grade-diamond';
    if (grade.includes('GOLD')) return 'grade-gold';
    if (grade.includes('SILVER')) return 'grade-silver';
    return 'grade-bad';
}

async function loadArchiveList() {
    try {
        const response = await fetch(CONFIG.api.archiveList);
        if (!response.ok) throw new Error('아카이브 목록을 불러올 수 없습니다');
        
        const files = await response.json();
        renderArchiveList(files);
    } catch (error) {
        console.error('아카이브 로드 실패:', error);
    }
}

function renderArchiveList(files) {
    const container = document.getElementById('archive-list');
    if (!container || !files || files.length === 0) {
        if (container) container.innerHTML = '<li>아카이브가 없습니다.</li>';
        return;
    }
    
    const html = files.slice(0, 10).map(file => {
        const displayName = file.replace('.html', '').replace(/_/g, ' ');
        return `
            <li class="archive-item">
                <a href="${CONFIG.api.archivePath}${file}">
                    <i data-lucide="file-text"></i>
                    <span>${displayName}</span>
                </a>
            </li>
        `;
    }).join('');
    
    container.innerHTML = html;
    
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}
