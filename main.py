import os
import json
import requests
import time
import hmac
import hashlib
import base64
from datetime import datetime

# -------------------------------------------------------------------------
# 1. 환경변수 로드
# -------------------------------------------------------------------------
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
COUPANG_ACCESS_KEY = os.environ.get("COUPANG_ACCESS_KEY")
COUPANG_SECRET_KEY = os.environ.get("COUPANG_SECRET_KEY")

# [검색광고 API 키]
NAVER_AD_CUSTOMER_ID = os.environ.get("NAVER_AD_CUSTOMER_ID")
NAVER_AD_ACCESS_KEY = os.environ.get("NAVER_AD_ACCESS_KEY")
NAVER_AD_SECRET_KEY = os.environ.get("NAVER_AD_SECRET_KEY")

# -------------------------------------------------------------------------
# 2. 공통 유틸 함수
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
def get_naver_ad_stats(keyword):
    """ [핵심] 광고 API로 월간 검색량 & CPC 조회 """
    if not NAVER_AD_ACCESS_KEY: return 0, 0
    
    uri = "/keywordstool"
    method = "GET"
    timestamp = str(round(time.time() * 1000))
    
    headers = {
        "X-Timestamp": timestamp,
        "X-API-KEY": NAVER_AD_ACCESS_KEY,
        "X-Customer": NAVER_AD_CUSTOMER_ID,
        "X-Signature": generate_ad_signature(timestamp, method, uri)
    }
    
    try:
        time.sleep(0.1)
        res = requests.get(f"https://api.naver.com{uri}", params={"hintKeywords": keyword, "showDetail": 1}, headers=headers)
        if res.status_code == 200:
            data_list = res.json().get('keywordList', [])
            if data_list:
                item = data_list[0]
                vol_pc = item.get('monthlyPcQcCnt', 0)
                vol_mo = item.get('monthlyMobileQcCnt', 0)
                # "< 10" 처리
                if isinstance(vol_pc, str): vol_pc = 0
                if isinstance(vol_mo, str): vol_mo = 0
                return (vol_pc + vol_mo), item.get('avgBidAmt', 0)
    except:
        pass
    return 0, 0

def get_blog_count(keyword):
    """ 블로그 문서 수 조회 """
    if not NAVER_CLIENT_ID: return 1
    url = "https://openapi.naver.com/v1/search/blog.json"
    try:
        time.sleep(0.05)
        res = requests.get(url, headers=get_naver_search_header(), params={"query": keyword, "display": 1}, timeout=5)
        if res.status_code == 200:
            cnt = res.json().get('total', 0)
            return cnt if cnt > 0 else 1
    except:
        pass
    return 1

def get_naver_shopping():
    """ [성공한 코드] 쇼핑 검색 API로 인기 키워드 수집 """
    print("🔎 네이버 쇼핑 데이터 수집...")
    headers = get_naver_search_header()
    if not headers: return []
    
    url = "https://openapi.naver.com/v1/search/shop.json"
    # 예시로 '디지털가전' 검색 -> 인기 상품명 추출
    params = {"query": "디지털가전", "display": 10, "sort": "sim"}
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            items = res.json().get('items', [])
            keywords = []
            for item in items:
                title = item['title'].replace("<b>", "").replace("</b>", "")
                short_keyword = ' '.join(title.split()[:2])
                keywords.append({"keyword": short_keyword, "source": "NAVER"})
            return keywords
    except Exception as e:
        print(f"네이버 에러: {e}")
    return []

def get_coupang_best():
    """ 쿠팡 골드박스 수집 """
    print("🔎 쿠팡 데이터 수집...")
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
            keywords = []
            for p in products:
                raw = p.get('productName', '')
                short_kw = ' '.join(raw.split()[:2])
                keywords.append({"keyword": short_kw, "source": "COUPANG"})
            return keywords
    except Exception as e:
        print(f"쿠팡 에러: {e}")
    return []

# -------------------------------------------------------------------------
# 4. 황금지수 계산
# -------------------------------------------------------------------------
def calculate_score(vol, blog, cpc):
    if vol == 0: return 0
    
    # 1. 검색량 점수 (40점)
    score_vol = min((vol / 10000) * 40, 40)
    # 2. CPC 점수 (30점)
    score_cpc = min((cpc / 1000) * 30, 30)
    # 3. 경쟁 점수 (30점) - 블로그 적을수록 좋음
    if blog < 1000: score_comp = 30
    else: score_comp = max(0, 30 - ((blog - 1000) / 1000))
        
    return round(score_vol + score_cpc + score_comp, 1)

# -------------------------------------------------------------------------
# 5. 메인 실행
# -------------------------------------------------------------------------
def main():
    print("🚀 황금 키워드 분석 시작...")
    
    candidates = []
    candidates.extend(get_naver_shopping())
    candidates.extend(get_coupang_best())
    
    final_results = []
    
    print(f"📊 {len(candidates)}개 키워드 정밀 분석 중...")
    
    for item in candidates:
        kw = item['keyword']
        src = item['source']
        
        # 정밀 데이터 조회
        vol, cpc = get_naver_ad_stats(kw)
        blog_cnt = get_blog_count(kw)
        
        # 점수 계산
        score = calculate_score(vol, blog_cnt, cpc)
        
        # 등급
        grade = "Normal"
        if score >= 80: grade = "💎 DIAMOND"
        elif score >= 60: grade = "🌟 GOLD"
        elif score >= 40: grade = "✨ SILVER"
        elif vol == 0: grade = "❓ NO DATA"
        
        final_results.append({
            "source": src,
            "keyword": kw,
            "golden_score": score,
            "grade": grade,
            "search_volume": vol,
            "cpc": cpc,
            "blog_count": blog_cnt
        })

    final_results.sort(key=lambda x: x['golden_score'], reverse=True)

    os.makedirs("output", exist_ok=True)
    with open("output/data.json", "w", encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)
        
    print("✅ 분석 완료!")

if __name__ == "__main__":
    main()
