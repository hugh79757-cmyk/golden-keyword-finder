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
    """ [복구됨] 연관검색어 수집 """
    url = f"https://ac.search.naver.com/nx/ac?q={keyword}&con=0&frm=nv&ans=2&r_format=json&r_enc=UTF-8&r_unicode=0&t_koreng=1&run=2&rev=4&q_enc=UTF-8&st=100"
    try:
        res = requests.get(url, timeout=2)
        if res.status_code == 200:
            items = res.json().get('items', [])[0]
            return [item[0] for item in items[:3]] # 상위 3개만
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
            # HTML 태그 제거 및 정제
            return [{"keyword": i['title'].replace("<b>","").replace("</b>",""), "source": "NAVER", "rank": f"{idx+1}위"} for idx, i in enumerate(res.json().get('items', []))]
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
            return [{"keyword": p['productName'], "source": "COUPANG", "rank": f"{idx+1}위"} for idx, p in enumerate(res.json().get('data', [])[:5])]
    except:
        pass
    return []

def calculate_score(vol, blog):
    if vol == 0: return 0
    if blog == 0: blog = 1
    efficiency = vol / blog 
    
    score = min((vol / 5000) * 60, 60)
    if blog < 1000: score += 40
    elif blog < 5000: score += 30
    elif blog < 10000: score += 10
    
    if blog > 50000: score = min(score, 20)
    elif efficiency < 0.5: score = score * 0.5
    elif efficiency < 1: score = score * 0.8
    else: score += 10
    
    return round(score, 1)

# --- 5문장 리포트 생성기 ---
def generate_report_text(top_item, date_str):
    kw = top_item['keyword']
    vol = top_item['search_volume']
    eff = top_item['efficiency']
    
    # 문장 조립
    s1 = f"{date_str} 기준, 현재 데이터를 분석한 결과 가장 가치 있는 황금 키워드는 '{kw}'입니다."
    s2 = f"이 키워드의 월간 검색량은 약 {vol:,}건으로 상당히 높은 수요를 보이고 있습니다."
    
    status = "매우 양호(블루오션)"
    recommend = "지금 바로 블로그 포스팅이나 상품 등록을 추천합니다."
    if eff > 5.0:
        status = "다소 높음(레드오션)"
        recommend = "경쟁이 치열하므로 세부 키워드로 우회하거나 차별화된 콘텐츠가 필요합니다."
    elif eff > 1.0:
        status = "보통"
        recommend = "충분히 진입해볼 만한 시장입니다."
        
    s3 = f"반면 경쟁 강도(블로그 수 대비 검색량)는 '{eff}' 수준으로, 경쟁 상태가 '{status}'입니다."
    s4 = f"따라서 {recommend}"
    s5 = "이 데이터는 실시간 트렌드를 반영하므로, 빠르게 선점하여 트래픽을 확보하시기 바랍니다."
    
    return f"{s1}<br>{s2}<br>{s3}<br>{s4}<br>{s5}"

# --- 아카이빙 (새 디자인 적용) ---
def create_archive_html(data, filename):
    now_str = datetime.now(KST).strftime("%Y년 %m월 %d일 %H시")
    date_only = datetime.now(KST).strftime("%Y년 %m월 %d일")
    
    # 통계 계산
    diamond_count = len([i for i in data if 'DIAMOND' in i.get('grade', '')])
    blueocean_count = len([i for i in data if i.get('efficiency', 999) < 1.0])
    
    # 브리핑 텍스트
    briefing_html = ""
    if data:
        top = data[0]
        kw = top['keyword']
        vol = f"{top['search_volume']:,}"
        eff = top['efficiency']
        
        status = "블루오션"
        if eff > 5.0: status = "레드오션"
        elif eff > 1.0: status = "보통"
        
        briefing_html = f"""
        <section class="hero-section">
            <div class="hero-header">
                <div class="hero-icon"><i data-lucide="bar-chart-3"></i></div>
                <h1 class="hero-title">{now_str} 트렌드 분석</h1>
            </div>
            <div class="hero-content">
                <strong>{date_only}</strong> 기준, 총 <strong>{len(data)}개</strong> 키워드 분석 완료<br><br>
                오늘의 <strong>1위 황금 키워드</strong>는 <span class="keyword-highlight">'{kw}'</span><br>
                월간 검색량 <strong>{vol}건</strong> · 경쟁강도 <strong>{eff}</strong> ({status})<br><br>
                다이아몬드 등급 <strong>{diamond_count}개</strong> · 블루오션 키워드 <strong>{blueocean_count}개</strong> 발견
            </div>
        </section>
        """

    # 테이블 행 생성
    rows = ""
    for item in data:
        # 뱃지
        badge_class = 'badge-coupang' if item['source'] == 'COUPANG' else ('badge-related' if item['rank'] == '연관' else 'badge-naver')
        badge_icon = 'shopping-cart' if item['source'] == 'COUPANG' else ('link' if item['rank'] == '연관' else 'shopping-bag')
        
        # 등급
        grade_class = 'grade-bad'
        grade_icon = ''
        score_text = f"{item['golden_score']}점"
        
        if "DIAMOND" in item['grade']:
            grade_class = 'grade-diamond'
            grade_icon = '<i data-lucide="gem"></i>'
        elif "GOLD" in item['grade']:
            grade_class = 'grade-gold'
            grade_icon = '<i data-lucide="star"></i>'
        elif "SILVER" in item['grade']:
            grade_class = 'grade-silver'
            grade_icon = '<i data-lucide="sparkles"></i>'
        
        # 경쟁강도
        eff_class = ''
        eff_icon = ''
        comp = item.get('efficiency', 999.99)
        
        if comp < 1.0:
            eff_class = 'eff-good'
            eff_icon = '<i data-lucide="flame"></i>'
        elif comp > 5.0:
            eff_class = 'eff-bad'
            eff_icon = '<i data-lucide="droplet"></i>'

        rows += f"""
        <tr>
            <td data-label="출처">
                <span class="badge {badge_class}">
                    <i data-lucide="{badge_icon}"></i>
                    {item['source']}
                </span>
            </td>
            <td data-label="순위">{item['rank']}</td>
            <td data-label="키워드">
                <div class="keyword-cell">
                    <div class="keyword-info">
                        <div class="keyword-name">{item['keyword']}</div>
                        <div class="keyword-grade">
                            <span class="grade {grade_class}">{grade_icon} {item['grade']}</span>
                        </div>
                    </div>
                    <div class="action-btns">
                        <button class="action-btn copy" onclick="copyKeyword('{item['keyword'].replace("'", "\\'")}', this)">
                            <i data-lucide="copy"></i> 복사
                        </button>
                        <a class="action-btn analyze" href="https://search.naver.com/search.naver?query={item['keyword']}" target="_blank" rel="noopener">
                            <i data-lucide="search"></i> 분석
                        </a>
                    </div>
                </div>
            </td>
            <td data-label="황금지수" class="num-col">
                <span class="grade {grade_class}">{grade_icon} {score_text}</span>
            </td>
            <td data-label="경쟁강도" class="num-col">
                <span class="efficiency {eff_class}">{eff_icon} {comp}</span>
            </td>
            <td data-label="검색량" class="num-col"><strong>{item['search_volume']:,}</strong></td>
            <td data-label="블로그수" class="num-col">{item['blog_count']:,}</td>
        </tr>"""

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- SEO 메타 태그 -->
    <title>{now_str} 황금 키워드 리포트 | 블루오션 키워드 분석</title>
    <meta name="description" content="{now_str} 기준 네이버, 쿠팡 실시간 트렌드 분석 리포트. 검색량 높고 경쟁 낮은 황금 키워드 {len(data)}개 발굴. 다이아몬드 등급 {diamond_count}개, 블루오션 {blueocean_count}개 포함.">
    <meta name="keywords" content="황금키워드, 블루오션키워드, 키워드분석, {date_only}, 네이버키워드, 쿠팡키워드, SEO분석">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://golden-keyword-finder.pages.dev/output/archives/{filename.split('/')[-1]}">
    
    <!-- Open Graph -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="{now_str} 황금 키워드 리포트">
    <meta property="og:description" content="다이아몬드 등급 {diamond_count}개, 블루오션 키워드 {blueocean_count}개 발견! 실시간 트렌드 분석 결과를 확인하세요.">
    <meta property="og:image" content="https://golden-keyword-finder.pages.dev/og-image.png">
    <meta property="og:url" content="https://golden-keyword-finder.pages.dev/output/archives/{filename.split('/')[-1]}">
    <meta property="og:locale" content="ko_KR">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{now_str} 황금 키워드 리포트">
    <meta name="twitter:description" content="다이아몬드 {diamond_count}개, 블루오션 {blueocean_count}개 발견!">
    
    <!-- 구조화된 데이터 -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "{now_str} 황금 키워드 분석 리포트",
        "description": "네이버, 쿠팡 트렌드 기반 블루오션 키워드 분석",
        "datePublished": "{datetime.now(KST).isoformat()}",
        "author": {{"@type": "Organization", "name": "황금 키워드 발굴기"}}
    }}
    </script>
    
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pretendard@latest/dist/web/static/pretendard.css">
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
    
    <style>
        :root {{
            --bg-primary: #09090b;
            --bg-secondary: #18181b;
            --bg-card: #1f1f23;
            --bg-card-hover: #27272a;
            --border-color: #27272a;
            --border-hover: #3f3f46;
            --text-primary: #fafafa;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --gold: #fbbf24;
            --gold-light: #fcd34d;
            --diamond: #a855f7;
            --diamond-light: #c084fc;
            --naver: #03c75a;
            --coupang: #e60f29;
            --blue-ocean: #22d3ee;
            --danger: #f87171;
            --success: #34d399;
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
            --radius-xl: 20px;
            --transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Pretendard', -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
            padding: 24px;
        }}

        .container {{ max-width: 1280px; margin: 0 auto; }}

        /* 헤더 */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0 28px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 28px;
            flex-wrap: wrap;
            gap: 16px;
        }}

        .logo {{ display: flex; align-items: center; gap: 14px; }}

        .logo-icon {{
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, var(--diamond) 0%, var(--gold) 100%);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .logo-icon svg {{ width: 26px; height: 26px; color: white; }}

        .logo-text {{
            font-size: 1.5rem;
            font-weight: 800;
            background: linear-gradient(90deg, var(--gold) 0%, var(--diamond-light) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

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
            border-color: var(--border-hover);
        }}

        .back-btn svg {{ width: 16px; height: 16px; }}

        /* 히어로 섹션 */
        .hero-section {{
            background: linear-gradient(135deg, rgba(168,85,247,0.08) 0%, rgba(251,191,36,0.04) 100%);
            border: 1px solid rgba(168,85,247,0.2);
            border-radius: var(--radius-xl);
            padding: 32px;
            margin-bottom: 28px;
        }}

        .hero-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }}

        .hero-icon {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--diamond) 0%, var(--diamond-light) 100%);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .hero-icon svg {{ color: white; width: 22px; height: 22px; }}
        .hero-title {{ font-size: 1.2rem; font-weight: 700; }}
        .hero-content {{ font-size: 0.95rem; line-height: 1.9; color: var(--text-secondary); }}
        .hero-content strong {{ color: var(--text-primary); }}

        .keyword-highlight {{
            background: linear-gradient(90deg, var(--gold) 0%, var(--gold-light) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 1.1em;
        }}

        /* 테이블 카드 */
        .table-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-xl);
            overflow: hidden;
            margin-bottom: 28px;
        }}

        .table-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 24px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            flex-wrap: wrap;
            gap: 16px;
        }}

        .table-title {{ display: flex; align-items: center; gap: 12px; font-size: 1rem; font-weight: 700; }}

        .table-title-icon {{
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .table-title-icon svg {{ color: var(--bg-primary); width: 18px; height: 18px; }}

        .legend {{ display: flex; gap: 20px; font-size: 0.75rem; color: var(--text-secondary); }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; }}
        .legend-dot {{ width: 8px; height: 8px; border-radius: 50%; }}
        .legend-dot.blue {{ background: var(--blue-ocean); }}
        .legend-dot.red {{ background: var(--danger); }}

        /* 테이블 */
        .data-table {{ width: 100%; border-collapse: collapse; }}

        .data-table th {{
            background: rgba(255,255,255,0.02);
            padding: 14px 20px;
            text-align: left;
            font-weight: 600;
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }}

        .data-table td {{
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
            vertical-align: middle;
        }}

        .data-table tbody tr:hover {{ background: var(--bg-card-hover); }}
        .num-col {{ text-align: right; font-variant-numeric: tabular-nums; }}

        /* 뱃지 */
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 100px;
            font-size: 0.65rem;
            font-weight: 700;
            color: white;
        }}

        .badge svg {{ width: 12px; height: 12px; }}
        .badge-naver {{ background: var(--naver); }}
        .badge-coupang {{ background: var(--coupang); }}
        .badge-related {{ background: var(--text-muted); }}

        /* 등급 */
        .grade {{ display: inline-flex; align-items: center; gap: 6px; font-weight: 700; }}
        .grade svg {{ width: 16px; height: 16px; }}
        .grade-diamond {{ color: var(--diamond-light); }}
        .grade-gold {{ color: var(--gold); }}
        .grade-silver {{ color: var(--text-secondary); }}
        .grade-bad {{ color: var(--text-muted); }}

        /* 경쟁강도 */
        .efficiency {{ display: inline-flex; align-items: center; gap: 6px; }}
        .efficiency svg {{ width: 14px; height: 14px; }}
        .eff-good {{ color: var(--blue-ocean); font-weight: 700; }}
        .eff-bad {{ color: var(--danger); }}

        /* 키워드 셀 */
        .keyword-cell {{ display: flex; align-items: center; gap: 16px; }}
        .keyword-info {{ flex: 1; }}
        .keyword-name {{ font-weight: 600; font-size: 0.9rem; margin-bottom: 4px; }}
        .keyword-grade {{ font-size: 0.75rem; }}

        /* 액션 버튼 */
        .action-btns {{ display: flex; gap: 6px; }}

        .action-btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 12px;
            border-radius: var(--radius-sm);
            border: 1px solid var(--border-color);
            background: var(--bg-secondary);
            color: var(--text-secondary);
            font-size: 0.7rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            text-decoration: none;
        }}

        .action-btn svg {{ width: 14px; height: 14px; }}
        .action-btn:hover {{ background: var(--bg-card-hover); color: var(--text-primary); }}
        .action-btn.copy:hover {{ border-color: var(--success); color: var(--success); }}
        .action-btn.analyze:hover {{ border-color: var(--naver); color: var(--naver); }}
        .action-btn.copied {{ background: var(--success); color: white; border-color: var(--success); }}

        /* 모바일 */
        @media (max-width: 900px) {{
            .data-table thead {{ display: none; }}
            .data-table tbody tr {{
                display: block;
                background: var(--bg-secondary);
                border-radius: var(--radius-lg);
                padding: 16px;
                margin: 10px 0;
                border: 1px solid var(--border-color);
            }}
            .data-table td {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 0;
                border-bottom: 1px solid var(--border-color);
            }}
            .data-table td:last-child {{ border-bottom: none; }}
            .data-table td::before {{
                content: attr(data-label);
                font-weight: 600;
                color: var(--text-muted);
                font-size: 0.7rem;
            }}
            .keyword-cell {{ flex-direction: column; align-items: flex-end; gap: 10px; }}
            .keyword-info {{ text-align: right; }}
        }}

        /* 푸터 */
        .footer {{
            text-align: center;
            padding: 32px 0;
            color: var(--text-muted);
            font-size: 0.8rem;
            border-top: 1px solid var(--border-color);
            margin-top: 32px;
        }}

        /* 토스트 */
        .toast {{
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: var(--bg-card);
            border: 1px solid var(--success);
            color: var(--success);
            padding: 12px 20px;
            border-radius: var(--radius-md);
            font-weight: 600;
            font-size: 0.85rem;
            opacity: 0;
            transition: var(--transition);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .toast.show {{ transform: translateX(-50%) translateY(0); opacity: 1; }}
        .toast svg {{ width: 18px; height: 18px; }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="logo">
                <div class="logo-icon"><i data-lucide="gem"></i></div>
                <span class="logo-text">황금 키워드 발굴기</span>
            </div>
            <a href="../../index.html" class="back-btn">
                <i data-lucide="arrow-left"></i> 메인으로 돌아가기
            </a>
        </header>

        {briefing_html}

        <section class="table-card">
            <div class="table-header">
                <h2 class="table-title">
                    <div class="table-title-icon"><i data-lucide="trophy"></i></div>
                    {now_str} 황금 키워드 랭킹
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
                        <th>순위</th>
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

        <footer class="footer">
            <p>© 2025 황금 키워드 발굴기 · Generated by Golden Keyword Bot</p>
        </footer>
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
    
    # 2. 키워드 확장 (연관검색어)
    print("🌱 키워드 확장 중...")
    final_candidates = []
    seen = set()
    
    for item in seeds:
        # 원본 정제 (너무 긴 상품명은 앞 3단어로 줄임)
        short_kw = ' '.join(item['keyword'].split()[:3])
        clean = short_kw.replace(" ", "")
        
        if clean not in seen:
            # 원본 추가
            item['keyword'] = short_kw # 줄인 이름으로 저장
            final_candidates.append(item)
            seen.add(clean)
        
        # 연관검색어 추가
        related = get_related_keywords(short_kw)
        for r_kw in related:
            r_clean = r_kw.replace(" ", "")
            if r_clean not in seen:
                final_candidates.append({
                    "keyword": r_kw, 
                    "source": item['source'], 
                    "rank": "연관"
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
        else: grade = "💩 BAD"
        
        eff = round(blog / vol, 2) if vol > 0 else 999.99
        final.append({**item, "golden_score": score, "grade": grade, "search_volume": vol, "blog_count": blog, "efficiency": eff})
        
    final.sort(key=lambda x: x['golden_score'], reverse=True)
    
    # 파일 저장
    os.makedirs("output", exist_ok=True)
    with open("output/data.json", "w", encoding='utf-8') as f: json.dump(final, f, ensure_ascii=False, indent=2)
    
    # 아카이브 저장
    os.makedirs("output/archives", exist_ok=True)
    now_kst = datetime.now(KST)
    fname = f"output/archives/{now_kst.strftime('%Y-%m-%d_%Hh')}.html"
    create_archive_html(final, fname)
    
    archives = sorted(os.listdir("output/archives"), reverse=True)
    with open("output/archive_list.json", "w", encoding='utf-8') as f: json.dump(archives, f)
    print("✅ 완료")

if __name__ == "__main__":
    main()
