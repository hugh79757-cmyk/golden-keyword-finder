// js/app.js - 메인 앱 로직 (광고 삽입 포함)

document.addEventListener('DOMContentLoaded', function() {
    loadData();
    loadArchiveList();
});

async function loadData() {
    try {
        const response = await fetch(CONFIG.api.data);
        if (!response.ok) throw new Error('데이터를 불러올 수 없습니다');
        
        const data = await response.json();
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
    
    // 키워드 테이블 렌더링 (광고 포함)
    renderKeywordTable(data.keywords);
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

// ✅ 키워드 테이블 렌더링 (광고 삽입 포함)
function renderKeywordTable(keywords) {
    const tbody = document.getElementById('keyword-table-body');
    if (!tbody || !keywords) return;
    
    let html = '';
    const adInterval = CONFIG.ads.interval || 5; // 기본 5개마다 광고
    
    keywords.forEach((item, index) => {
        // ✅ 일정 간격마다 광고 행 삽입
        if (index > 0 && index % adInterval === 0) {
            html += AdsManager.createTableAdRow(7);
        }
        
        html += createKeywordRow(item);
    });
    
    tbody.innerHTML = html;
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

// ... 나머지 함수들 (getGradeClass, loadArchiveList 등)

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
    
    // 아이콘 재초기화
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}
