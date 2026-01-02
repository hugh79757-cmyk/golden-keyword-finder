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

# --- 아카이빙 ---
def create_archive_html(data, filename):
    now_str = datetime.now(KST).strftime("%Y년 %m월 %d일 %H시")
    date_only = datetime.now(KST).strftime("%Y년 %m월 %d일")
    
    briefing_html = ""
    if data:
        briefing_text = generate_report_text(data[0], date_only)
        briefing_html = f"""
        <section style="background:#f0f7ff; padding:20px; border-radius:10px; border:1px solid #cce5ff; margin-bottom:30px; line-height:1.6;">
            <h3 style="color:#0056b3; margin-top:0;">📊 {now_str} 트렌드 요약</h3>
            <p>{briefing_text}</p>
        </section>
        """

    rows = ""
    for item in data:
        badge = 'badge-coupang' if item['source'] == 'COUPANG' else 'badge-naver'
        score_html = f"<span style='color:#999;'>{item['golden_score']}점</span>"
        if "DIAMOND" in item['grade']: score_html = f"<span class='grade-dia'>💎 {item['golden_score']}점</span>"
        elif "GOLD" in item['grade']: score_html = f"<span class='grade-gold'>🌟 {item['golden_score']}점</span>"
        
        eff_class, eff_icon = '', ''
        if item['efficiency'] < 1.0: eff_class, eff_icon = 'eff-good', '🔥'
        elif item['efficiency'] > 5.0: eff_class, eff_icon = 'eff-bad', '💧'

        rows += f"""
        <tr>
            <td><span class="badge {badge}">{item['source']}</span></td>
            <td>{item['rank']}</td>
            <td><strong>{item['keyword']}</strong><br><small>{item['grade']}</small></td>
            <td class="num-col">{score_html}</td>
            <td class="num-col {eff_class}">{eff_icon} {item['efficiency']}</td>
            <td class="num-col"><strong>{item['search_volume']:,}</strong></td>
            <td class="num-col">{item['blog_count']:,}</td>
        </tr>"""

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{now_str} 황금 키워드 리포트</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
        <style>
            body {{ font-family: 'Pretendard', sans-serif; }} .container {{ max-width: 1200px; }}
            .badge {{ padding: 4px 8px; border-radius: 6px; font-size: 0.75em; font-weight: bold; color: white; }}
            .badge-naver {{ background-color: #03C75A; }} .badge-coupang {{ background-color: #E60F29; }}
            .grade-dia {{ color: #9C27B0; font-weight: 900; }} .grade-gold {{ color: #FF9800; font-weight: 800; }}
            .eff-good {{ color: #2e7d32; font-weight: bold; }} .eff-bad {{ color: #d32f2f; }}
            th {{ background-color: #f4f4f4; white-space: nowrap; }} .num-col {{ text-align: right; }}
        </style>
    </head>
    <body>
        <main class="container">
            <nav><ul><li><strong>💎 {now_str} 리포트</strong></li></ul><ul><li><a href="../index.html">← 메인으로</a></li></ul></nav>
            {briefing_html}
            <figure><table role="grid"><thead><tr><th>출처</th><th>순위</th><th>키워드</th><th>황금지수</th><th>경쟁강도</th><th>검색량</th><th>블로그</th></tr></thead><tbody>{rows}</tbody></table></figure>
            {briefing_html} <!-- 하단에도 추가 -->
            <footer><small>Generated by Golden Keyword Bot</small></footer>
        </main>
    </body>
    </html>
    """
    with open(filename, "w", encoding='utf-8') as f: f.write(html_content)

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
