#!/User/anaconda3/python3
# -*- coding: utf-8 -*-
# @Time     :   2018/10/18/018 20:01
# @Author   :   Qingyunke
import json
import os
from hashlib import md5

import pymongo
from urllib.parse import urlencode
from config import *
from requests import RequestException, codes

import requests

client = pymongo.MongoClient(MONGO_URI)
db = client[MONGO_DB]

headers = {
    'cookie': 'UM_distinctid=1639b3226b0232-040f726178ec83-3f3c5501-1fa400-1639b3226b16c4; csrftoken=483497fc2eb9b0eff6237107e4bba175; tt_webid=6589869001508832771; tt_webid=6589869001508832771; WEATHER_CITY=%E5%8C%97%E4%BA%AC; CNZZDATA1259612802=454515046-1527315218-https%253A%252F%252Fwww.baidu.com%252F%7C1539907629',
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
                # for image in images:
                yield {
                    'title': title,
                    'image': ['https:' + image.get('url').replace('list', 'origin') for image in images],
                }


def save_image(item):
    img_path = 'img' + os.path.sep + item.get('title')
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    try:
        response = requests.get(item.get('image'), headers=headers)
        if response.status_code == codes.ok:
            file_path = img_path + os.path.sep + '{file_name}.{file_suffix}'.format(
                file_name=md5(response.content).hexdigest(), file_suffix='jpg')
            if not os.path.exists(file_path):
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print('Downloaded image path is %s' % file_path)
            else:
                print('Already Downloaded', file_path)
    except requests.ConnectionError:
        print('Failed to Save Image，item %s' % item)


def save_to_mongo(result):
    if db[MONGO_TABLE].insert_many(result):
        print('Save to MongoDB successfully', result)
        return True
    else:
        return False


def main():
    html = get_index_page(0, '街拍')
    items = parse_index_page(html)
    save_to_mongo(items)


if __name__ == '__main__':
    main()
