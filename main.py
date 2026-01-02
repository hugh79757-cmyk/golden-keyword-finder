import os
import json
import requests
import time
import hmac
import hashlib
import base64
from datetime import datetime, timedelta

# -------------------------------------------------------------------------
# 1. 환경변수
# -------------------------------------------------------------------------
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
COUPANG_ACCESS_KEY = os.environ.get("COUPANG_ACCESS_KEY")
COUPANG_SECRET_KEY = os.environ.get("COUPANG_SECRET_KEY")
NAVER_AD_CUSTOMER_ID = os.environ.get("NAVER_AD_CUSTOMER_ID", "").strip()
NAVER_AD_ACCESS_KEY = os.environ.get("NAVER_AD_ACCESS_KEY", "").strip()
NAVER_AD_SECRET_KEY = os.environ.get("NAVER_AD_SECRET_KEY", "").strip()

# -------------------------------------------------------------------------
# 2. 유틸리티
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

# -------------------------------------------------------------------------
# 3. 데이터 수집 함수들
# -------------------------------------------------------------------------

def get_related_keywords(keyword):
    """ [NEW] 네이버 연관검색어(자동완성) 가져오기 """
    url = f"https://ac.search.naver.com/nx/ac?q={keyword}&con=0&frm=nv&ans=2&r_format=json&r_enc=UTF-8&r_unicode=0&t_koreng=1&run=2&rev=4&q_enc=UTF-8&st=100"
    try:
        res = requests.get(url, timeout=2)
        if res.status_code == 200:
            data = res.json()
            items = data.get('items', [])[0]
            # 상위 3개만 추출 (너무 많으면 API 제한 걸림)
            return [item[0] for item in items[:3]]
    except:
        pass
    return []

def get_naver_ad_stats(keyword):
    """ 광고 API: 검색량 & CPC """
    if not NAVER_AD_ACCESS_KEY: return 0, 0
    
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
            data_list = res.json().get('keywordList', [])
            if data_list:
                item = data_list[0]
                vol_pc = item.get('monthlyPcQcCnt', 0)
                vol_mo = item.get('monthlyMobileQcCnt', 0)
                if str(vol_pc).startswith('<'): vol_pc = 0
                if str(vol_mo).startswith('<'): vol_mo = 0
                
                total = int(vol_pc) + int(vol_mo)
                cpc = int(item.get('avgBidAmt', 0))
                return total, cpc
    except:
        pass
    return 0, 0

def get_blog_count(keyword):
    """ 블로그 문서 수 """
    if not NAVER_CLIENT_ID: return 1
    url = "https://openapi.naver.com/v1/search/blog.json"
    try:
        time.sleep(0.05)
        res = requests.get(url, headers=get_naver_search_header(), params={"query": keyword, "display": 1}, timeout=5)
        if res.status_code == 200:
            return res.json().get('total', 1)
    except:
        pass
    return 1

def get_naver_shopping():
    print("🔎 네이버 쇼핑 수집...")
    headers = get_naver_search_header()
    if not headers: return []
    
    url = "https://openapi.naver.com/v1/search/shop.json"
    try:
        res = requests.get(url, headers=headers, params={"query": "디지털가전", "display": 5, "sort": "sim"}, timeout=10)
        if res.status_code == 200:
            items = res.json().get('items', [])
            result = []
            for idx, item in enumerate(items):
                title = item['title'].replace("<b>", "").replace("</b>", "")
                kw = ' '.join(title.split()[:2])
                result.append({"keyword": kw, "source": "NAVER", "rank": idx + 1})
            return result
    except:
        pass
    return []

def get_coupang_best():
    print("🔎 쿠팡 수집...")
    if not COUPANG_ACCESS_KEY: return []
    
    url_path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/goldbox"
    dt = datetime.utcnow().strftime('%y%m%d') + 'T' + datetime.utcnow().strftime('%H%M%S') + 'Z'
    msg = dt + "GET" + url_path
    sig = hmac.new(COUPANG_SECRET_KEY.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).hexdigest()
    auth = f"CEA algorithm=HmacSHA256, access-key={COUPANG_ACCESS_KEY}, signed-date={dt}, signature={sig}"

    try:
        res = requests.get(f"https://api-gateway.coupang.com{url_path}", headers={"Authorization": auth}, timeout=10)
        if res.status_code == 200:
            products = res.json().get('data', [])[:5]
            result = []
            for idx, p in enumerate(products):
                raw = p.get('productName', '')
                kw = ' '.join(raw.split()[:2])
                result.append({"keyword": kw, "source": "COUPANG", "rank": idx + 1})
            return result
    except:
        pass
    return []

# -------------------------------------------------------------------------
# 4. 황금지수 로직 (효율성 반영)
# -------------------------------------------------------------------------
def calculate_score(vol, blog, cpc):
    if vol == 0: return 0
    if blog == 0: blog = 1
    
    efficiency = vol / blog # 효율 (검색/경쟁)
    
    score = 0
    score += min((vol / 5000) * 40, 40)
    score += min((cpc / 500) * 20, 20)
    
    # 패널티 로직
    if blog > 50000: score = min(score, 30) # 경쟁 과열
    elif efficiency < 0.5: score = score * 0.5
    elif efficiency < 1: score = score * 0.8
    else: score += 20 # 가산점
    
    return round(score, 1)

# -------------------------------------------------------------------------
# 5. 메인
# -------------------------------------------------------------------------
def main():
    print("🚀 황금 키워드 분석 시작...")
    
    # 1. 씨앗 키워드 수집
    seeds = []
    seeds.extend(get_naver_shopping())
    seeds.extend(get_coupang_best())
    
    # 2. 키워드 확장 (연관검색어 추가)
    print("🌱 키워드 확장(연관검색어) 중...")
    expanded_candidates = []
    
    for item in seeds:
        # 원본 키워드 추가
        expanded_candidates.append(item)
        
        # 연관 키워드 3개 가져오기
        related_kws = get_related_keywords(item['keyword'])
        for r_kw in related_kws:
            # 연관 키워드는 순위 정보가 없으므로 '연관'으로 표시
            expanded_candidates.append({
                "keyword": r_kw,
                "source": item['source'], # 출처는 모태를 따름
                "rank": "연관" 
            })
            
    print(f"📊 총 {len(expanded_candidates)}개 키워드 정밀 분석 중...")
    
    final = []
    for item in expanded_candidates:
        kw = item['keyword']
        vol, cpc = get_naver_ad_stats(kw)
        blog = get_blog_count(kw)
        score = calculate_score(vol, blog, cpc)
        
        grade = "Normal"
        if score >= 60: grade = "💎 DIAMOND"
        elif score >= 40: grade = "🌟 GOLD"
        elif score >= 20: grade = "✨ SILVER"
        else: grade = "💩 BAD"
        
        final.append({
            "source": item['source'],
            "rank": item['rank'],
            "keyword": kw,
            "golden_score": score,
            "grade": grade,
            "search_volume": vol,
            "cpc": cpc,
            "blog_count": blog
        })
        
    final.sort(key=lambda x: x['golden_score'], reverse=True)
    
    os.makedirs("output", exist_ok=True)
    with open("output/data.json", "w", encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 완료! {len(final)}개 분석됨.")

if __name__ == "__main__":
    main()
