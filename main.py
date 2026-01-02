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

NAVER_AD_CUSTOMER_ID = os.environ.get("NAVER_AD_CUSTOMER_ID")
NAVER_AD_ACCESS_KEY = os.environ.get("NAVER_AD_ACCESS_KEY")
NAVER_AD_SECRET_KEY = os.environ.get("NAVER_AD_SECRET_KEY")

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
# 3. 데이터 수집
# -------------------------------------------------------------------------
def get_naver_ad_stats(keyword):
    """ 광고 API: 검색량/CPC 조회 (강력한 디버깅 모드) """
    if not NAVER_AD_ACCESS_KEY or not NAVER_AD_SECRET_KEY or not NAVER_AD_CUSTOMER_ID:
        print(f"⚠️ [API설정오류] 광고 API 키가 누락되었습니다. ID: {NAVER_AD_CUSTOMER_ID}")
        return 0, 0
    
    uri = "/keywordstool"
    method = "GET"
    timestamp = str(round(time.time() * 1000))
    
    headers = {
        "X-Timestamp": timestamp,
        "X-API-KEY": NAVER_AD_ACCESS_KEY,
        "X-Customer": str(NAVER_AD_CUSTOMER_ID), # 문자로 변환해서 전송
        "X-Signature": generate_ad_signature(timestamp, method, uri)
    }
    
    try:
        clean_kw = keyword.replace(" ", "")
        time.sleep(0.1)
        
        # API 호출
        res = requests.get(f"https://api.naver.com{uri}", params={"hintKeywords": clean_kw, "showDetail": 1}, headers=headers)
        
        # [중요] 성공이든 실패든 응답 코드를 확인
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
                print(f"✅ [성공] {keyword} -> 검색량: {total}, CPC: {cpc}")
                return total, cpc
            else:
                print(f"⚠️ [데이터없음] {keyword}에 대한 결과가 비어있습니다.")
        else:
            # [핵심] 실패 원인을 로그에 찍음
            print(f"❌ [API실패] {keyword} 코드: {res.status_code}, 메시지: {res.text}")

    except Exception as e:
        print(f"❌ [시스템에러] {e}")
        
    return 0, 0


def get_blog_count(keyword):
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
        # 인기 상품 10개
        res = requests.get(url, headers=headers, params={"query": "디지털가전", "display": 10, "sort": "sim"}, timeout=10)
        if res.status_code == 200:
            items = res.json().get('items', [])
            result = []
            for idx, item in enumerate(items):
                title = item['title'].replace("<b>", "").replace("</b>", "")
                kw = ' '.join(title.split()[:2])
                result.append({"keyword": kw, "source": "NAVER", "rank": idx + 1}) # rank 추가
            return result
    except Exception as e:
        print(f"네이버 에러: {e}")
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
                result.append({"keyword": kw, "source": "COUPANG", "rank": idx + 1}) # rank 추가
            return result
    except:
        pass
    return []

# -------------------------------------------------------------------------
# 4. 메인
# -------------------------------------------------------------------------
def calculate_score(vol, blog, cpc):
    if vol == 0: return 0
    
    # 가중치 조정 (검색량 비중 높임)
    s_vol = min((vol / 5000) * 50, 50) # 5천건 이상이면 50점 만점
    s_cpc = min((cpc / 500) * 20, 20)  # 20점 만점
    
    # 경쟁 점수 (30점 만점)
    if blog < 500: s_comp = 30
    elif blog < 2000: s_comp = 20
    elif blog < 10000: s_comp = 10
    else: s_comp = 0
    
    return round(s_vol + s_cpc + s_comp, 1)

def main():
    print("🚀 시작...")
    candidates = []
    candidates.extend(get_naver_shopping())
    candidates.extend(get_coupang_best())
    
    final = []
    for item in candidates:
        kw = item['keyword']
        vol, cpc = get_naver_ad_stats(kw) # 검색량 조회
        blog = get_blog_count(kw)
        score = calculate_score(vol, blog, cpc)
        
        grade = "Normal"
        if score >= 70: grade = "💎 DIAMOND"
        elif score >= 50: grade = "🌟 GOLD"
        elif score >= 30: grade = "✨ SILVER"
        
        final.append({
            "source": item['source'],
            "rank": item['rank'],      # 순위 필드 복구
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
    print("✅ 완료")

if __name__ == "__main__":
    main()
