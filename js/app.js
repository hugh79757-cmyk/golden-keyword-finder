function generateHeroContent(summary) {
    // SEO 요약을 그대로 사용 (문장형)
    return summary.replace(/\n/g, '<br>');
}

function createTableRow(item) {
    let badgeClass = 'badge-naver', badgeIcon = 'shopping-bag';
    if (item.source === 'COUPANG') { badgeClass = 'badge-coupang'; badgeIcon = 'shopping-cart'; }
    
    let gradeClass = 'grade-bad', gradeIcon = '';
    if (item.grade.includes('DIAMOND')) { gradeClass = 'grade-diamond'; gradeIcon = '<i data-lucide="gem"></i>'; }
    else if (item.grade.includes('GOLD')) { gradeClass = 'grade-gold'; gradeIcon = '<i data-lucide="star"></i>'; }
    else if (item.grade.includes('SILVER')) { gradeClass = 'grade-silver'; gradeIcon = '<i data-lucide="sparkles"></i>'; }
    
    let effClass = '', effIcon = '';
    const comp = item.efficiency ?? 999.99;
    if (comp < 1.0) { effClass = 'eff-good'; effIcon = '<i data-lucide="flame"></i>'; }
    else if (comp > 5.0) { effClass = 'eff-bad'; effIcon = '<i data-lucide="droplet"></i>'; }

    const escapedKw = item.keyword.replace(/'/g, "\\'");
    const naverUrl = `https://search.naver.com/search.naver?query=${encodeURIComponent(item.keyword)}`;

    // 순위 컬럼 제거됨
    return `<tr>
        <td data-label="출처"><span class="badge ${badgeClass}"><i data-lucide="${badgeIcon}"></i>${item.source}</span></td>
        <td data-label="키워드"><div class="keyword-cell"><div class="keyword-info"><div class="keyword-name">${item.keyword}</div><div class="keyword-grade"><span class="grade ${gradeClass}">${gradeIcon} ${item.grade}</span></div></div><div class="action-btns"><button class="action-btn copy" onclick="copyKeyword('${escapedKw}', this)"><i data-lucide="copy"></i> 복사</button><a class="action-btn analyze" href="${naverUrl}" target="_blank"><i data-lucide="search"></i> 분석</a></div></div></td>
        <td data-label="황금지수" class="num-col"><span class="grade ${gradeClass}">${gradeIcon} ${item.golden_score}점</span></td>
        <td data-label="경쟁강도" class="num-col"><span class="efficiency ${effClass}">${effIcon} ${comp}</span></td>
        <td data-label="검색량" class="num-col"><strong>${formatNumber(item.search_volume)}</strong></td>
        <td data-label="블로그수" class="num-col">${formatNumber(item.blog_count)}</td>
    </tr>`;
}

async function loadData() {
    try {
        const response = await fetch(CONFIG.api.data);
        const jsonData = await response.json();
        
        // 새로운 데이터 구조 처리
        const data = jsonData.keywords || jsonData;  // 호환성 유지
        const seoSummary = jsonData.seo_summary || '';
        const keywordReview = jsonData.keyword_review || '';
        
        document.getElementById('update-time').innerHTML = `<i data-lucide="clock"></i><span>${formatDateTime()}</span>`;
        
        const diamondCount = data.filter(i => i.grade.includes('DIAMOND')).length;
        const blueOceanCount = data.filter(i => i.efficiency < 1.0).length;
        const sources = [...new Set(data.map(i => i.source))].length;
        
        document.getElementById('stat-total').textContent = data.length;
        document.getElementById('stat-diamond').textContent = diamondCount;
        document.getElementById('stat-blueocean').textContent = blueOceanCount;
        document.getElementById('stat-sources').textContent = sources;
        
        // SEO 문장형 요약 표시
        if (seoSummary) {
            document.getElementById('hero-content').innerHTML = generateHeroContent(seoSummary);
            document.getElementById('hero-section').style.display = 'block';
        }
        
        // 테이블 렌더링
        document.getElementById('keyword-list').innerHTML = data.map(createTableRow).join('');
        
        // 키워드 총평 표시
        if (keywordReview) {
            renderKeywordReview(keywordReview);
        }
        
        lucide.createIcons();
    } catch (err) {
        console.error('데이터 로드 실패:', err);
        document.getElementById('keyword-list').innerHTML = '<tr><td colspan="6" class="loading-cell" style="color:var(--danger);">데이터를 불러올 수 없습니다</td></tr>';
    }
}

function renderKeywordReview(review) {
    // 기존 총평 섹션이 있으면 제거
    const existing = document.getElementById('keyword-review-section');
    if (existing) existing.remove();
    
    // 새 총평 섹션 생성
    const section = document.createElement('section');
    section.id = 'keyword-review-section';
    section.className = 'review-section';
    section.innerHTML = `
        <h3><i data-lucide="clipboard-list"></i> 키워드 총평</h3>
        <div class="review-content">${review.replace(/\n/g, '<br>')}</div>
    `;
    
    // 아카이브 섹션 앞에 삽입
    const archiveSection = document.querySelector('.archive-section');
    if (archiveSection) {
        archiveSection.parentNode.insertBefore(section, archiveSection);
    }
    
    lucide.createIcons();
}

async function loadArchive() {
    try {
        const response = await fetch(CONFIG.api.archiveList);
        const files = await response.json();
        
        if (!files || files.length === 0) {
            document.getElementById('archive-list').innerHTML = '<li class="archive-item">아직 저장된 리포트가 없습니다.</li>';
            return;
        }
        
        document.getElementById('archive-list').innerHTML = files.slice(0, CONFIG.archiveLimit).map(file => {
            const name = file.replace('.html', '').replace('_', '일 ').replace('h', '시');
            // 절대 경로 사용
            return `<li class="archive-item"><a href="./output/archives/${file}"><i data-lucide="file-text"></i>${name}</a></li>`;
        }).join('');
        
        lucide.createIcons();
    } catch (err) {
        console.error('아카이브 로드 실패:', err);
        document.getElementById('archive-list').innerHTML = '<li class="archive-item">리포트를 불러올 수 없습니다.</li>';
    }
}


function initApp() {
    lucide.createIcons();
    loadData();
    loadArchive();
}

document.addEventListener('DOMContentLoaded', initApp);
async function loadArchive() {
    try {
        console.log('아카이브 로드 시작...');
        
        const response = await fetch(CONFIG.api.archiveList);
        console.log('응답 상태:', response.status);
        
        const files = await response.json();
        console.log('아카이브 파일 목록:', files);
        
        if (!files || files.length === 0) {
            console.log('아카이브 파일 없음');
            document.getElementById('archive-list').innerHTML = '<li>저장된 리포트가 없습니다.</li>';
            return;
        }
        
        document.getElementById('archive-list').innerHTML = files.slice(0, CONFIG.archiveLimit).map(file => {
            const fullPath = `./output/archives/${file}`;
            console.log('아카이브 경로:', fullPath);
            
            const name = file.replace('.html', '').replace('_', '일 ').replace('h', '시');
            return `<li class="archive-item"><a href="${fullPath}"><i data-lucide="file-text"></i>${name}</a></li>`;
        }).join('');
        
        lucide.createIcons();
        console.log('아카이브 로드 완료');
        
    } catch (err) {
        console.error('아카이브 로드 실패:', err);
    }
}

