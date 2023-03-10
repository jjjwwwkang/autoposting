import NaverDataLab as ND
import hmac
import hashlib
import binascii
import os
import time
import requests
import json
import urllib
import pandas as pd
from bs4 import BeautifulSoup
from time import strftime, gmtime

#keywords  = ND.get_keywords()
#Keywords 5개 리스트를 받고, 키워드로 쿠팡에서 검색하고 상품명, 사진, 숏링크, 가격을 담은 데이터프레임을 반환

def get_coupang(keywords) :
    Datas = pd.DataFrame()
    for keyword in keywords:
        data = pd.DataFrame()
    ################################# 사이트 호출 #################################
        target_url = 'https://www.coupang.com/np/search?component=&q=' + str(keyword) + '&channel=user'  # URL
        headers = {'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6,zh;q=0.5',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
               'Accept-Encoding': 'gzip'
               }
        res = requests.get(url=target_url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        # 상품명
        product_name = soup.select('div > div.name')

        # 상품가격
        product_price = soup.select('div.price-wrap > div.price > em > strong')

        # 상품리뷰 수
        product_review = soup.select('div.other-info > div > span.rating-total-count')

        # 상품 구매 링크
        product_link = soup.select('a.search-product-link')

        # 상품 이미지
        product_image = soup.select('dt > img')

        # 여기까지가 키워드하나 가지고 검색, 해당 키워드로 크롤링된 정보중 12개를 모으기
        product_names = []  # 상품명
        product_prices = []  # 가격
        product_reviews = []  # 리뷰
        product_links = []  # 구매링크
        product_images = []  # 상품이미지

        for name in product_name[:12]:  # 상품명 리스트 집어넣기
            p_name = name.text
            p_name = p_name.replace('\n', '')  # 상품명 필터링1
            p_name = p_name.replace('  ', '')  # 상품명 필터링2
            p_name = p_name.replace(',', '')  # 상품명 필터링3
            product_names.append(p_name)

        for price in product_price[:12]:  # 상품가격 리스트 집어넣기
            p_price = price.text
            p_price = p_price.replace(",", "")
            product_prices.append(p_price)

        for review in product_review[:12]:  # 상품리뷰 갯수 리스트 집어넣기
            try:
                p_review_cnt = re.sub("[()]", "", review.text)
            except:
                p_review_cnt = '0'
            product_reviews.append(p_review_cnt)

        for link in product_link[:12]:  # 상품구매링크 리스트 집어넣기
            p_link = "https://www.coupang.com" + link['href']
            product_links.append(p_link)

        for image in product_image[:12]:  # 상품이미지 리스트 집어넣기
            p_image = image.get('data-img-src')
            if p_image is None:
                p_image = image.get('src')
                # print(p_image)
                p_image = p_image.replace("//", "")
                product_images.append(p_image)
            else:
                p_image = p_image.replace("//", "")
                product_images.append(p_image)
            # 아래는 쿠팡숏츠 만들기
        coupang_short_urls = []  # 쿠팡 숏츠 링크 리스트 담을거

        REQUEST_METHOD = "POST"
        DOMAIN = "https://api-gateway.coupang.com"
        URL = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"

        # Replace with your own ACCESS_KEY and SECRET_KEY
        ACCESS_KEY = "776679bb-dec1-4027-bdf2-8f03c26bdb50"  # 키를 입력하세요!
        SECRET_KEY = "8a9695de19955215cde90f51dc9fd598a2dfb588"  # 키를 입력하세요!

        for i in product_links[:12]:
            coupang_link = i  # 쿠팡링크
            REQUEST = {"coupangUrls": [coupang_link]}  # 해당 쿠팡링크 받기


            def generateHmac(method, url, api_secret_key, api_access_key):
                path, *query = url.split('?')
                os.environ['TZ'] = 'GMT+0'
                dt_datetime = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'  # GMT+0
                msg = dt_datetime + method + path + (query[0] if query else '')
                signature = hmac.new(bytes(api_secret_key, 'utf-8'), msg.encode('utf-8'), hashlib.sha256).hexdigest()

                return 'CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}'.format(api_access_key, dt_datetime, signature)

            authorization = generateHmac(REQUEST_METHOD, URL, SECRET_KEY, ACCESS_KEY)
            url = "{}{}".format(DOMAIN, URL)
            resposne = requests.request(method=REQUEST_METHOD, url=url,
                                    headers={
                                        "Authorization": authorization,
                                        "Content-Type": "application/json"
                                    },
                                    data=json.dumps(REQUEST)
                                    )

            time.sleep(2)  # 10초마다 한번씩 (총 5분걸림)
            text = resposne.json()
            try:
                text_2 = text['data']
            except:
                text_2 = ['https://www.coupang.com/np/coupangglobal']  # 없을시 가짜 리스트 생성
            for i in text_2:
                try:
                    coupang_short_url = i['shortenUrl']
                except:
                    coupang_short_url = 'https://link.coupang.com/a/mEezS'  # 가짜 링크 집어넣기
                #print(coupang_short_url)  # 확인
                coupang_short_urls.append(coupang_short_url)

        print("키워드 {}의 최종 숏츠링크가 최종 완료되었습니다.".format(keyword))  # 최종확인
        data['names'] = product_names
        data['keyword'] = keyword
        data['prices'] = product_prices
        data['urls'] = coupang_short_urls
        data['images'] = product_images
        Datas = pd.concat([Datas, data], axis=0)
    return Datas

#a = get_coupang(keywords)
#print(a)
#print(a.shape)