import os

import requests
import json
from collections import namedtuple
from re import sub
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request
from store_functions import *
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

JUMIA_URL = os.getenv('JUMIA_URL', 'https://www.jumia.com.ng/catalog/?q=')
KONGA_URL = os.getenv('KONGA_URL', 'https://b9zcrrrvom-3.algolianet.com/1/indexes/*/queries')
KARA_URL = os.getenv('KARA_URL', 'http://www.kara.com.ng/catalogsearch/result?q=')
SLOT_URL = os.getenv('SLOT_URL', 'https://slot.ng/?post_type=product&s=')
JIJI_URL= os.getenv('JIJI_URL', 'https://jiji.ng/search?query=')
EMPTY_LIST = []

urls = [JUMIA_URL,KONGA_URL,KARA_URL,SLOT_URL,JIJI_URL]


@app.route('/')
def home_page():
	return render_template('index.html'),200

@app.route('/search/<term>/', methods=['GET'])
def search_products(term=None):
    '''
    Searches online stores using the given term. If no term is given, defaults to recent.
    '''
    #sort_arg = sort_filters[request.args.get('sort')] if sort in sort_filters else ''

    jumiaurl = JUMIA_URL + sub(r"\s+", '+', str(term))
    #kongaurl = KONGA_URL + sub(r"\s+", '%20', str(term))
    karaurl = KARA_URL + str(term)
    sloturl = SLOT_URL + sub(r"\s+", '+', str(term))
	jijiurl= JIJI_URL + term.replace(' ', '+')	
    jumiaresult=parse_jumia(jumiaurl)
    kararesult=parse_kara(karaurl)
    kongaresult=parse_konga(KONGA_URL,term)
    slotresult=parse_slot(sloturl)
	jijiresult=parse_jiji(jijiurl)
    results = jumiaresult + kongaresult + slotresult + kararesult+jijiresult

    return jsonify(results), 200


def parse_all(soup,STORE):
    titles = parse_titles(soup,STORE)
    images = parse_images(soup,STORE)
    prices = parse_prices(soup,STORE)
    #ratings = parse_ratings(soup,STORE)
    product_urls = parse_product_urls(soup,STORE)
    #price_drops = parse_price_drops(soup,STORE)
    search_results = []
    for search_result in zip(titles, images, prices, product_urls):
        search_results.append({
            'title': search_result[0],
            'image': search_result[1],
            'price': search_result[2],
            'url': search_result[3],
        })
    return search_results



def parse_jumia(url, sort=None):
    '''
    This function parses the page and returns list of torrents
    '''
    #print(url)
    STORE = "jumia"
    try:
        data = requests.get(url).text
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print(e)
        sys.exit(1)
    soup = BeautifulSoup(data, 'lxml')
    #print(soup)
    table_present = soup.find('section', {'class': 'products -mabaya'})
    if table_present is None:
        return EMPTY_LIST
    return parse_all(soup,STORE)

def parse_jiji(url, sort=None):
	'''
    This function parses the page and returns list of torrents
    '''
    STORE ="jiji"
    try:
        data = requests.get(url).text
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print(e)
        sys.exit(1)
    soup = BeautifulSoup(data, 'lxml')
    table_present = soup.find('div', {'class': 'container'})
    if table_present is None:
        return EMPTY_LIST
    return parse_all(soup,STORE)

def parse_kara(url, sort=None):
    '''
    This function parses the page and returns list of torrents
    '''
    #print(url)
    STORE = "kara"
    try:
        data = requests.get(url).text
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print(e)
        sys.exit(1)
    soup = BeautifulSoup(data, 'lxml')
    #print(soup)
    table_present = soup.find('ul', {'class': 'searchindex-results'})
    if table_present is None:
        return EMPTY_LIST
    return parse_all(soup,STORE)

def parse_konga(url, term):
    '''
    This function parses the page and returns list of torrents
    '''
    #print(url)
    STORE = "konga"
    params = {"x-algolia-agent": "Algolia for vanilla JavaScript 3.30.0;react-instantsearch 5.3.2;JS Helper 2.26.1", "x-algolia-application-id": "B9ZCRRRVOM", "x-algolia-api-key": "cb605b0936b05ce1a62d96f53daa24f7"}
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36','accept': 'application/json','content-type': 'application/x-www-form-urlencoded','Origin': 'https://www.konga.com'}
    data = json.dumps({"requests" : [{"indexName":"catalog_store_konga_price_desc" ,"params":"query=" + sub(r"\s+", '%20', str(term))  }]})
    try:
        response = requests.post(url,headers=headers, params=params, data=data).json()
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print(e)
        sys.exit(1)
    #n.loads(response['requests'][], object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
    soup = response['results'][0]['hits']    
    #print(response)
    #table_present = soup.find('div', {'class': 'ais-InstantSearch__root'})
    return parse_all(soup,STORE)

def parse_slot(url, sort=None):
    '''
    This function parses the page and returns list of torrents
    '''
    #print(url)
    STORE = "slot"
    data = requests.get(url).text
    soup = BeautifulSoup(data, 'lxml')
    #print(soup)
    table_present = soup.find('div', {'class': 'products-found'})
    if table_present is None:
        return EMPTY_LIST
    return parse_all(soup,STORE)

def parse_titles(soup,STORE):
    switcher = {
        'jumia': parse_title_jumia,
        'konga': parse_title_konga,
        'kara': parse_title_kara,
        'slot': parse_title_slot,
		'jiji':parse_title_jiji
    }
    # Get the function from switcher dictionary
    func = switcher.get(STORE, lambda: "Store is not supported yet")
    # Execute the function
    titles = func(soup)
    return titles


def parse_images(soup,STORE):
    switcher = {
        'jumia': parse_image_jumia,
        'konga': parse_image_konga,
        'kara': parse_image_kara,
        'slot': parse_image_slot,
		'jiji':parse_image_jiji
    }
    # Get the function from switcher dictionary
    func = switcher.get(STORE, lambda: "Store is not supported yet")
    # Execute the function
    images = func(soup)
    return images

def parse_prices(soup,STORE):
    switcher = {
        'jumia': parse_price_jumia,
        'konga': parse_price_konga,
        'kara': parse_price_kara,
        'slot': parse_price_slot,
		'jiji': parse_price_jiji
    }
    # Get the function from switcher dictionary
    func = switcher.get(STORE, lambda: "Store is not supported yet")
    # Execute the function
    images = func(soup)
    return images

def parse_ratings(soup,STORE):

    return

def parse_product_urls(soup,STORE):
    switcher = {
        'jumia': parse_url_jumia,
        'konga': parse_url_konga,
        'kara': parse_url_kara,
        'slot': parse_url_slot,
		'jiji': parse_url_jiji
    }
    # Get the function from switcher dictionary
    func = switcher.get(STORE, lambda: "Store is not supported yet")
    # Execute the function
    urls = func(soup)
    return urls

def parse_price_drops(soup,STORE):

    return 

if __name__ == '__main__':
	app.debug = True
	app.run()
