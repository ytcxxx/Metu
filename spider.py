#!/User/anaconda3/python3
# -*- coding: utf-8 -*-
# @Time     :   2018/10/18/018 20:01
# @Author   :   Qingyunke

import json
import os
from hashlib import md5
from multiprocessing.pool import Pool
import pymongo
from urllib.parse import urlencode
from config import *
from requests import RequestException, codes
import requests


headers = {
    'cookie': 'UM_distinctid=1639b3226b0232-040f726178ec83-3f3c5501-1fa400-1639b3226b16c4; csrftoken=483497fc2eb9b0eff6237107e4bba175; tt_webid=6589869001508832771; tt_webid=6589869001508832771; WEATHER_CITY=%E5%8C%97%E4%BA%AC; uuid="w:108e9a560de6483eac9e8c3a889e97c6"; __utma=24953151.1897997518.1539918251.1539918251.1539918251.1; __utmz=24953151.1539918251.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); CNZZDATA1259612802=454515046-1527315218-https%253A%252F%252Fwww.baidu.com%252F%7C1539995474; __tasessionId=olh0tztk21540003162803',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    'accept-language': 'zh-CN,zh;q=0.9',
}


def get_index_page(offset, keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': '20',
        'cur_tab': '1',
        'from': 'search_tab',
    }
    url = 'https://www.toutiao.com/search_content/?' + urlencode(data)
    response = requests.get(url, headers)
    try:
        if response.status_code == codes.ok:
            return response.text
        else:
            return None
    except RequestException:
        print('This % can\'t be accessing' % url)
        return None


def parse_index_page(html):
    result = json.loads(html)
    if result and 'data' in result.keys():
        for item in result.get('data'):
            if item.get('title') and item.get('image_list'):
                title = item.get('title')
                images = item.get('image_list')
                yield {
                    'title': title,
                    'image': ['https:' + image.get('url').replace('list', 'origin') for image in images],
                }


def save_image(item):
    file_path = 'F:\img' + os.path.sep + item.get('title')
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    try:
        for url in item.get('image'):
            response = requests.get(url, headers=headers)
            if response.status_code == codes.ok:
                image_path = file_path + os.path.sep + '{img_name}.{img_suffix}'.format(
                    img_name=md5(response.content).hexdigest(), img_suffix='jpg'
                )
                if not os.path.exists(image_path):
                    with open(image_path, 'wb') as f:
                        f.write(response.content)
                    print('Downloading image', image_path)
                else:
                    print('Already Downloaded', image_path)
    except requests.ConnectionError:
        print('Failed to download image: %s ' % item)


def save_to_mongo(result):
    client = pymongo.MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    if db[MONGO_TABLE].update_many({'title': result.get('title')}, {'$set': result}, upsert=True):
        print('Save to MongoDB successfully')
        return True
    else:
        return False


def main(offset):
    html = get_index_page(offset, keyword)
    items = parse_index_page(html)
    for item in items:
        save_image(item)
    items = parse_index_page(html)
    for item in items:
        save_to_mongo(item)


if __name__ == '__main__':
    pool = Pool()
    pages = ([x * 20 for x in range(FIRST_PAGE, LAST_PAGE + 1)])
    pool.map(main, pages)
    pool.close()
    pool.join()
