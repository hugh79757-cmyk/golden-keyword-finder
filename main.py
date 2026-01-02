import os
import json
import requests
import time
import hmac
import hashlib
import base64
from datetime import datetime, timedelta, timezone

# -------------------------------------------------------------------------
# 1. 환경변수
# -------------------------------------------------------------------------
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "").strip()
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "").strip()
COUPANG_ACCESS_KEY = os.environ.get("COUPANG_ACCESS_KEY", "").strip()
COUPANG_SECRET_KEY = os.environ.get("COUPANG_SECRET_KEY", "").strip()
NAVER_AD_CUSTOMER_ID = os.environ.get("NAVER_AD_CUSTOMER_ID", "").strip()
NAVER_AD_ACCESS_KEY = os.environ.get("NAVER_AD_ACCESS_KEY", "").strip()
NAVER_AD_SECRET_KEY = os.environ.get("NAVER_AD_SECRET_KEY", "").strip()

KST = timezone(timedelta(hours=9))

# -------------------------------------------------------------------------
# 2. 유틸리티 & 데이터 수집
# -------------------------------------------------------------------------
def get_naver_search_header():
    if not NAVER_CLIENT_ID: return None
    return {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        "Content-Type": "application/json"
    }

def generate_ad_signature(timestamp, method, uri):
    message = f"{timestamp}.{method}.{uri}"
    hash_obj = hmac.new(NAVER_AD_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    return base64.b64encode(hash_obj.digest()).decode('utf-8')

def get_related_keywords(keyword):
    """연관검색어 수집"""
    url = f"https://ac.search.naver.com/nx/ac?q={keyword}&con=0&frm=nv&ans=2&r_format=json&r_enc=UTF-8&r_unicode=0&t_koreng=1&run=2&rev=4&q_enc=UTF-8&st=100"
    try:
        res = requests.get(url, timeout=2)
        if res.status_code == 200:
            items = res.json().get('items', [])
            if items and len(items) > 0:
                return [item[0] for item in items[0][:3]]
    except:
        pass
    return []

def get_search_volume(keyword):
    if not NAVER_AD_ACCESS_KEY: return 0
    uri = "/keywordstool"
    method = "GET"
    timestamp = str(round(time.time() * 1000))
    headers = {
        "X-Timestamp": timestamp,
        "X-API-KEY": NAVER_AD_ACCESS_KEY,
        "X-Customer": str(NAVER_AD_CUSTOMER_ID),
        "X-Signature": generate_ad_signature(timestamp, method, uri)
    }
    try:
        clean_kw = keyword.replace(" ", "")
        time.sleep(0.1)
        res = requests.get(f"https://api.naver.com{uri}", params={"hintKeywords": clean_kw, "showDetail": 1}, headers=headers)
        if res.status_code == 200:
            data = res.json().get('keywordList', [])
            if data:
                item = data[0]
                vol = int(item.get('monthlyPcQcCnt', 0) if str(item.get('monthlyPcQcCnt')) != '< 10' else 0) + \
                      int(item.get('monthlyMobileQcCnt', 0) if str(item.get('monthlyMobileQcCnt')) != '< 10' else 0)
                return vol
    except:
        pass
    return 0

def get_blog_count(keyword):
    if not NAVER_CLIENT_ID: return 1
    try:
        time.sleep(0.05)
        res = requests.get("https://openapi.naver.com/v1/search/blog.json", headers=get_naver_search_header(), params={"query": keyword, "display": 1}, timeout=5)
        if res.status_code == 200:
            return res.json().get('total', 1)
    except:
        pass
    return 1

def get_naver_shopping():
    print("🔎 네이버 쇼핑 수집...")
    if not NAVER_CLIENT_ID: return []
    try:
        res = requests.get("https://openapi.naver.com/v1/search/shop.json", headers=get_naver_search_header(), params={"query": "디지털가전", "display": 5, "sort": "sim"}, timeout=10)
        if res.status_code == 200:
            return [{"keyword": i['title'].replace("<b>","").replace("</b>",""), "source": "NAVER"} for i in res.json().get('items', [])]
    except:
        pass
    return []

def get_coupang_best():
    print("🔎 쿠팡 수집...")
    if not COUPANG_ACCESS_KEY: return []
    url = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/goldbox"
    dt = datetime.utcnow().strftime('%y%m%d') + 'T' + datetime.utcnow().strftime('%H%M%S') + 'Z'
    msg = dt + "GET" + url
    sig = hmac.new(COUPANG_SECRET_KEY.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).hexdigest()
    auth = f"CEA algorithm=HmacSHA256, access-key={COUPANG_ACCESS_KEY}, signed-date={dt}, signature={sig}"
    try:
        res = requests.get(f"https://api-gateway.coupang.com{url}", headers={"Authorization": auth}, timeout=10)
        if res.status_code == 200:
            return [{"keyword": p['productName'], "source": "COUPANG"} for p in res.json().get('data', [])[:5]]
    except:
        pass
    return []

def calculate_score(vol, blog):
    if vol == 0: return 0
    if blog == 0: blog = 1
    
    score = min((vol / 5000) * 60, 60)
    if blog < 1000: score += 40
    elif blog < 5000: score += 30
    elif blog < 10000: score += 10
    
    efficiency = blog / vol if vol > 0 else 999
    if blog > 50000: score = min(score, 20)
    elif efficiency > 2: score = score * 0.5
    elif efficiency > 1: score = score * 0.8
    else: score += 10
    
    return round(score, 1)

# --- SEO 친화적 문장형 리포트 생성 ---
def generate_seo_summary(data, date_str):
    """구글 검색 노출에 최적화된 문장형 요약 생성"""
    if not data:
        return "현재 분석된 키워드가 없습니다."
    
    top = data[0]
    kw = top['keyword']
    vol = f"{top['search_volume']:,}"
    eff = top['efficiency']
    
    # 등급별 개수
    diamond_count = len([i for i in data if 'DIAMOND' in i.get('grade', '')])
    gold_count = len([i for i in data if 'GOLD' in i.get('grade', '')])
    blueocean_count = len([i for i in data if i.get('efficiency', 999) < 1.0])
    
    # 경쟁 상태 판단
    if eff < 0.5:
        competition = "매우 낮은 경쟁률을 보이는 블루오션"
    elif eff < 1.0:
        competition = "경쟁이 적은 유망한 시장"
    elif eff < 3.0:
        competition = "적정 수준의 경쟁이 있는 시장"
    else:
        competition = "경쟁이 치열한 레드오션"
    
    # 문장형 요약 생성
    summary = f"""{date_str} 기준 네이버와 쿠팡의 실시간 트렌드를 분석한 결과, 
총 {len(data)}개의 키워드 중 가장 주목할 만한 황금 키워드는 '{kw}'입니다. 

이 키워드는 월간 검색량 {vol}건을 기록하며 높은 관심도를 보이고 있으며, 
경쟁강도 {eff}로 {competition}으로 분석됩니다. 

현재 다이아몬드 등급 키워드 {diamond_count}개, 골드 등급 {gold_count}개가 발견되었으며, 
블루오션 키워드는 총 {blueocean_count}개로 확인되었습니다. 

블로거와 마케터, 온라인 셀러라면 지금이 이 키워드를 선점할 최적의 타이밍입니다."""
    
    return summary

def generate_keyword_review(data):
    """키워드 총평 생성"""
    if not data:
        return ""
    
    # 통계 계산
    total = len(data)
    diamond_count = len([i for i in data if 'DIAMOND' in i.get('grade', '')])
    gold_count = len([i for i in data if 'GOLD' in i.get('grade', '')])
    blueocean_count = len([i for i in data if i.get('efficiency', 999) < 1.0])
    redocean_count = len([i for i in data if i.get('efficiency', 0) > 5.0])
    
    avg_volume = sum(i.get('search_volume', 0) for i in data) / total if total > 0 else 0
    avg_competition = sum(i.get('efficiency', 0) for i in data if i.get('efficiency', 999) < 999) / total if total > 0 else 0
    
    # 상위 키워드 추출
    top_keywords = [i['keyword'] for i in data[:5]]
    blueocean_keywords = [i['keyword'] for i in data if i.get('efficiency', 999) < 1.0][:3]
    
    # 시장 상황 판단
    if blueocean_count >= 3:
        market_status = "현재 시장에는 진입 기회가 많은 블루오션 키워드가 다수 발견되었습니다."
        recommendation = "빠른 콘텐츠 제작과 상품 등록을 통해 선점 효과를 노려보세요."
    elif diamond_count >= 2:
        market_status = "높은 가치의 다이아몬드 등급 키워드가 발견되어 긍정적인 시장 상황입니다."
        recommendation = "다이아몬드 키워드를 중심으로 콘텐츠 전략을 수립하시기 바랍니다."
    elif redocean_count > total * 0.5:
        market_status = "전반적으로 경쟁이 치열한 레드오션 키워드가 많습니다."
        recommendation = "틈새 키워드나 롱테일 키워드 전략을 고려해보세요."
    else:
        market_status = "다양한 기회와 경쟁이 혼재된 시장 상황입니다."
        recommendation = "각 키워드의 경쟁강도를 확인하고 선별적으로 접근하세요."
    
    review = f"""오늘의 키워드 총평

{market_status}

📊 주요 지표
• 분석 키워드: 총 {total}개
• 평균 검색량: {avg_volume:,.0f}건
• 평균 경쟁강도: {avg_competition:.2f}
• 블루오션 키워드: {blueocean_count}개
• 레드오션 키워드: {redocean_count}개

🏆 주목할 키워드
{', '.join(top_keywords)}

🔥 블루오션 추천
{', '.join(blueocean_keywords) if blueocean_keywords else '해당 없음'}

💡 전략 제안
{recommendation}"""
    
    return review

# --- 아카이빙 HTML 생성 (수정됨) ---
def create_archive_html(data, filename):
    now_str = datetime.now(KST).strftime("%Y년 %m월 %d일 %H시")
    date_only = datetime.now(KST).strftime("%Y년 %m월 %d일")
    
    # 통계 계산
    diamond_count = len([i for i in data if 'DIAMOND' in i.get('grade', '')])
    blueocean_count = len([i for i in data if i.get('efficiency', 999) < 1.0])
    
    # SEO 문장형 요약
    seo_summary = generate_seo_summary(data, date_only)
    
    # 키워드 총평
    keyword_review = generate_keyword_review(data)

    # 테이블 행 생성 (순위 컬럼 제거)
    rows = ""
    for item in data:
        badge_class = 'badge-coupang' if item['source'] == 'COUPANG' else 'badge-naver'
        badge_icon = 'shopping-cart' if item['source'] == 'COUPANG' else 'shopping-bag'
        
        grade_class = 'grade-bad'
        grade_icon = ''
        
        if "DIAMOND" in item['grade']:
            grade_class = 'grade-diamond'
            grade_icon = '<i data-lucide="gem"></i>'
        elif "GOLD" in item['grade']:
            grade_class = 'grade-gold'
            grade_icon = '<i data-lucide="star"></i>'
        elif "SILVER" in item['grade']:
            grade_class = 'grade-silver'
            grade_icon = '<i data-lucide="sparkles"></i>'
        
        eff_class = ''
        eff_icon = ''
        comp = item.get('efficiency', 999.99)
        
        if comp < 1.0:
            eff_class = 'eff-good'
            eff_icon = '<i data-lucide="flame"></i>'
        elif comp > 5.0:
            eff_class = 'eff-bad'
            eff_icon = '<i data-lucide="droplet"></i>'

        escaped_kw = item['keyword'].replace("'", "\\'").replace('"', '\\"')

        rows += f"""
        <tr>
            <td data-label="출처">
                <span class="badge {badge_class}">
                    <i data-lucide="{badge_icon}"></i>
                    {item['source']}
                </span>
            </td>
            <td data-label="키워드">
                <div class="keyword-cell">
                    <div class="keyword-info">
                        <div class="keyword-name">{item['keyword']}</div>
                        <div class="keyword-grade">
                            <span class="grade {grade_class}">{grade_icon} {item['grade']}</span>
                        </div>
                    </div>
                    <div class="action-btns">
                        <button class="action-btn copy" onclick="copyKeyword('{escaped_kw}', this)">
                            <i data-lucide="copy"></i> 복사
                        </button>
                        <a class="action-btn analyze" href="https://search.naver.com/search.naver?query={item['keyword']}" target="_blank" rel="noopener">
                            <i data-lucide="search"></i> 분석
                        </a>
                    </div>
                </div>
            </td>
            <td data-label="황금지수" class="num-col">
                <span class="grade {grade_class}">{grade_icon} {item['golden_score']}점</span>
            </td>
            <td data-label="경쟁강도" class="num-col">
                <span class="efficiency {eff_class}">{eff_icon} {comp}</span>
            </td>
            <td data-label="검색량" class="num-col"><strong>{item['search_volume']:,}</strong></td>
            <td data-label="블로그수" class="num-col">{item['blog_count']:,}</td>
        </tr>"""

    # 총평 HTML 변환
    review_html = keyword_review.replace('\n', '<br>')

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <title>{now_str} 황금 키워드 리포트 | 블루오션 키워드 분석</title>
    <meta name="description" content="{date_only} 기준 네이버, 쿠팡 실시간 트렌드 분석. {data[0]['keyword'] if data else ''} 등 황금 키워드 {len(data)}개 발굴. 다이아몬드 {diamond_count}개, 블루오션 {blueocean_count}개.">
    <meta name="keywords" content="황금키워드, 블루오션키워드, {', '.join([i['keyword'] for i in data[:5]])}">
    <meta name="robots" content="index, follow">
    
    <meta property="og:type" content="article">
    <meta property="og:title" content="{now_str} 황금 키워드 리포트">
    <meta property="og:description" content="다이아몬드 {diamond_count}개, 블루오션 {blueocean_count}개 발견!">
    <meta property="og:locale" content="ko_KR">
    
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pretendard@latest/dist/web/static/pretendard.css">
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
    <link rel="stylesheet" href="../../css/variables.css">
    <link rel="stylesheet" href="../../css/base.css">
    <link rel="stylesheet" href="../../css/components.css">
    <link rel="stylesheet" href="../../css/layout.css">
    <link rel="stylesheet" href="../../css/responsive.css">
    
    <style>
        .back-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 18px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 600;
            transition: var(--transition);
        }}
        .back-btn:hover {{
            background: var(--bg-card-hover);
            color: var(--text-primary);
        }}
        .back-btn svg {{ width: 16px; height: 16px; }}
        
        .review-section {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-xl);
            padding: 28px;
            margin-top: 28px;
            white-space: pre-line;
            line-height: 1.8;
        }}
        .review-section h3 {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            font-size: 1.1rem;
        }}
        .review-content {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        .review-content strong {{
            color: var(--text-primary);
        }}
    </style>
</head>
<body>
    <div class="page-wrapper">
        <div class="container">
            <header class="header">
                <div class="logo">
                    <div class="logo-icon"><i data-lucide="gem"></i></div>
                    <span class="logo-text">황금 키워드 발굴기</span>
                </div>
                <a href="../../index.html" class="back-btn">
                    <i data-lucide="arrow-left"></i> 메인으로
                </a>
            </header>

            <section class="hero-section">
                <div class="hero-header">
                    <div class="hero-icon"><i data-lucide="bar-chart-3"></i></div>
                    <h1 class="hero-title">{now_str} 트렌드 분석</h1>
                </div>
                <div class="hero-content">{seo_summary}</div>
            </section>

            <section class="table-card">
                <div class="table-header">
                    <h2 class="table-title">
                        <div class="table-title-icon"><i data-lucide="trophy"></i></div>
                        황금 키워드 목록
                    </h2>
                    <div class="legend">
                        <span class="legend-item"><span class="legend-dot blue"></span>블루오션</span>
                        <span class="legend-item"><span class="legend-dot red"></span>레드오션</span>
                    </div>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>출처</th>
                            <th>키워드</th>
                            <th class="num-col">황금지수</th>
                            <th class="num-col">경쟁강도</th>
                            <th class="num-col">검색량</th>
                            <th class="num-col">블로그수</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </section>

            <section class="review-section">
                <h3><i data-lucide="clipboard-list"></i> 키워드 총평</h3>
                <div class="review-content">{review_html}</div>
            </section>

            <footer class="footer">
                <p>© 2025 황금 키워드 발굴기</p>
            </footer>
        </div>
    </div>

    <div class="toast" id="toast">
        <i data-lucide="check-circle"></i>
        <span id="toast-message">복사되었습니다</span>
    </div>

    <script>
        lucide.createIcons();

        function showToast(msg) {{
            const t = document.getElementById('toast');
            document.getElementById('toast-message').textContent = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 2500);
        }}

        function copyKeyword(kw, btn) {{
            navigator.clipboard.writeText(kw).then(() => {{
                btn.classList.add('copied');
                btn.innerHTML = '<i data-lucide="check"></i> 복사됨';
                lucide.createIcons();
                showToast("'" + kw + "' 복사됨");
                setTimeout(() => {{
                    btn.classList.remove('copied');
                    btn.innerHTML = '<i data-lucide="copy"></i> 복사';
                    lucide.createIcons();
                }}, 1500);
            }});
        }}
    </script>
</body>
</html>"""
    
    with open(filename, "w", encoding='utf-8') as f:
        f.write(html_content)

# -------------------------------------------------------------------------
# 5. 메인 실행
# -------------------------------------------------------------------------
def main():
    print("🚀 시작...")
    
    # 1. 시드 수집
    seeds = []
    seeds.extend(get_naver_shopping())
    seeds.extend(get_coupang_best())
    
    # 2. 키워드 확장 (연관검색어) - 네이버, 쿠팡 모두 적용
    print("🌱 키워드 확장 중...")
    final_candidates = []
    seen = set()
    
    for item in seeds:
        # 원본 정제 (너무 긴 상품명은 앞 3단어로 줄임)
        short_kw = ' '.join(item['keyword'].split()[:3])
        clean = short_kw.replace(" ", "")
        
        if clean not in seen:
            item['keyword'] = short_kw
            final_candidates.append(item)
            seen.add(clean)
        
        # 네이버 연관검색어 추가 (쿠팡 키워드도 포함)
        related = get_related_keywords(short_kw)
        for r_kw in related:
            r_clean = r_kw.replace(" ", "")
            if r_clean not in seen:
                final_candidates.append({
                    "keyword": r_kw, 
                    "source": item['source']  # 원본 출처 유지
                })
                seen.add(r_clean)
            
    print(f"📊 {len(final_candidates)}개 분석...")
    
    final = []
    for item in final_candidates:
        kw = item['keyword']
        vol = get_search_volume(kw)
        blog = get_blog_count(kw)
        score = calculate_score(vol, blog)
        
        grade = "Normal"
        if score >= 60: grade = "💎 DIAMOND"
        elif score >= 40: grade = "🌟 GOLD"
        elif score >= 20: grade = "✨ SILVER"
        else: grade = "Normal"
        
        eff = round(blog / vol, 2) if vol > 0 else 999.99
        final.append({
            **item, 
            "golden_score": score, 
            "grade": grade, 
            "search_volume": vol, 
            "blog_count": blog, 
            "efficiency": eff
        })
        
    final.sort(key=lambda x: x['golden_score'], reverse=True)
    
    # SEO 요약 생성
    date_only = datetime.now(KST).strftime("%Y년 %m월 %d일")
    seo_summary = generate_seo_summary(final, date_only)
    keyword_review = generate_keyword_review(final)
    
    # 파일 저장
    os.makedirs("output", exist_ok=True)
    
    # data.json에 요약 정보 포함
    output_data = {
        "generated_at": datetime.now(KST).isoformat(),
        "seo_summary": seo_summary,
        "keyword_review": keyword_review,
        "keywords": final
    }
    
    with open("output/data.json", "w", encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    # 아카이브 저장
    os.makedirs("output/archives", exist_ok=True)
    now_kst = datetime.now(KST)
    fname = f"output/archives/{now_kst.strftime('%Y-%m-%d_%Hh')}.html"
    create_archive_html(final, fname)
    
    archives = sorted(os.listdir("output/archives"), reverse=True)
    with open("output/archive_list.json", "w", encoding='utf-8') as f:
        json.dump(archives, f)
    
    print("✅ 완료")

if __name__ == "__main__":
    main()
