function generateHeroContent(topItem, totalCount, diamondCount, blueOceanCount) {
    const dateStr = formatDate();
    const kw = topItem.keyword;
    const vol = formatNumber(topItem.search_volume);
    const eff = topItem.efficiency;
    
    let status = '블루오션', statusClass = 'eff-good';
    if (eff > 5.0) { status = '레드오션'; statusClass = 'eff-bad'; }
    else if (eff > 1.0) { status = '보통'; statusClass = ''; }

    return `<strong>${dateStr}</strong> 기준, 총 <strong>${totalCount}개</strong> 키워드 분석<br><br>1위 황금 키워드: <span class="keyword-highlight">'${kw}'</span><br>검색량 <strong>${vol}건</strong> · 경쟁강도 <strong class="${statusClass}">${eff}</strong> (${status})<br><br>다이아몬드 <strong>${diamondCount}개</strong> · 블루오션 <strong>${blueOceanCount}개</strong>`;
}

function createTableRow(item) {
    let badgeClass = 'badge-naver', badgeIcon = 'shopping-bag';
    if (item.source === 'COUPANG') { badgeClass = 'badge-coupang'; badgeIcon = 'shopping-cart'; }
    else if (item.rank === '연관') { badgeClass = 'badge-related'; badgeIcon = 'link'; }
    
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

    return `<tr>
        <td data-label="출처"><span class="badge ${badgeClass}"><i data-lucide="${badgeIcon}"></i>${item.source}</span></td>
        <td data-label="순위">${item.rank}</td>
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
        const data = await response.json();
        
        document.getElementById('update-time').innerHTML = `<i data-lucide="clock"></i><span>${formatDateTime()}</span>`;
        
        const diamondCount = data.filter(i => i.grade.includes('DIAMOND')).length;
        const blueOceanCount = data.filter(i => i.efficiency < 1.0).length;
        const sources = [...new Set(data.map(i => i.source))].length;
        
        document.getElementById('stat-total').textContent = data.length;
        document.getElementById('stat-diamond').textContent = diamondCount;
        document.getElementById('stat-blueocean').textContent = blueOceanCount;
        document.getElementById('stat-sources').textContent = sources;
        
        if (data.length > 0) {
            document.getElementById('hero-content').innerHTML = generateHeroContent(data[0], data.length, diamondCount, blueOceanCount);
            document.getElementById('hero-section').style.display = 'block';
        }
        
        document.getElementById('keyword-list').innerHTML = data.map(createTableRow).join('');
        lucide.createIcons();
    } catch (err) {
        document.getElementById('keyword-list').innerHTML = '<tr><td colspan="7" class="loading-cell" style="color:var(--danger);">데이터를 불러올 수 없습니다</td></tr>';
    }
}

async function loadArchive() {
    try {
        const response = await fetch(CONFIG.api.archiveList);
        const files = await response.json();
        
        document.getElementById('archive-list').innerHTML = files.slice(0, CONFIG.archiveLimit).map(file => {
            const name = file.replace('.html', '').replace('_', '일 ').replace('h', '시');
            return `<li class="archive-item"><a href="${CONFIG.api.archivePath}${file}"><i data-lucide="file-text"></i>${name}</a></li>`;
        }).join('');
        
        lucide.createIcons();
    } catch (err) { console.error(err); }
}

function initApp() {
    lucide.createIcons();
    loadData();
    loadArchive();
}

document.addEventListener('DOMContentLoaded', initApp);
