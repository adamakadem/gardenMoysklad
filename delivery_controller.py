import json
import logging
import sys
import logging
import requests
import log_helper
import config


def append_delivery(addre, pwz=None):
    logging.info(addre)
    addr = addre
    if addr == '':
        return False
    if 'Самовывоз' in addr:
        addr = 'Самовывоз пос.Ливенское'
    if addr.startswith('Доставка до адрес') and pwz is None:
        addr = 'Доставка по адресу'
    if 'Заказов' in addr and 'Портов' in pwz:
        addr = 'Доставка ПВЗ Портовая 20А'
    if 'Заказов' in addr and 'ктябрь' in pwz:
        addr = 'ПВЗ Октябрьская 12'
    addr_obj = config.attribute_static
    checker = False
    try:
        with open('delivery_points.json', 'r') as f:
            file = json.load(f)
            for item in file['rows']:

                if addr == item['name']:

                    addr_obj['value']['meta'] = item['meta']
                    checker = True
                    break
            if not checker:
                return False
            else:
                return addr_obj
    except:
        print(sys.exc_info())
        return False


def append_delivery_item(delivery, payload_num, delivery_price):
    logging.info(delivery)
    logging.info(payload_num)
    prep_item = {
        "quantity": 1,
        "reserve": 1,
        "price": 0,
        "discount": 0,
        "vat": 0,
        "assortment": {}
    }
    if 'Самовывоз' in delivery:
        prep_item["assortment"] = {
            "meta": {
                "href": "https://api.moysklad.ru/api/remap/1.2/entity/product/" + config.delivery_samo_service,
                "type": 'product',
                "mediaType": "application/json"
            }}
        return prep_item
    elif 'Пункт' in delivery or 'ПВЗ' in delivery:
        if payload_num == 1:
            prep_item["assortment"] = {
                "meta": {
                    "href": "https://api.moysklad.ru/api/remap/1.2/entity/product/" + config.delivery_pwz_service,
                    "type": 'product',
                    "mediaType": "application/json"
                }}
        else:
            prep_item["assortment"] = {
                "meta": {
                    "href": "https://api.moysklad.ru/api/remap/1.2/entity/product/" + config.delivery_address_item_sazh,
                    "type": 'product',
                    "mediaType": "application/json"
                }}
            delivery_price = 70000
            if delivery_price != 0:
                try:
                    resp = requests.get(url=prep_item["assortment"]['meta']['href'], headers=config.headers)
                    prep_item['price'] = resp['salePrices'][0]['value']
                except:
                    prep_item['price'] = 70000
        return prep_item
    elif 'адрес' in delivery:
        print('Здесь доставка' + delivery)
        logging.info(delivery)
        if payload_num == 2:
            prep_item["assortment"] = {
                "meta": {
                    "href": "https://api.moysklad.ru/api/remap/1.2/entity/product/" + config.delivery_address_item_sazh,
                    "type": 'product',
                    "mediaType": "application/json"
                }}
            if delivery_price != 0:
                try:
                    resp = requests.get(url=prep_item["assortment"]['meta']['href'], headers=config.headers)
                    prep_item['price'] = resp['salePrices'][0]['value']
                except:
                    prep_item['price'] = 100000
        else:
            logging.info('delivery_price ELSE')
            prep_item["assortment"] = {
                "meta": {
                    "href": "https://api.moysklad.ru/api/remap/1.2/entity/product/" + config.delivery_address_service_other,
                    "type": 'product',
                    "mediaType": "application/json"
                }}
            if delivery_price != 0:
                logging.info('delivery_price != 0')
                try:
                    url= prep_item["assortment"]['meta']['href']
                    logging.info(url)
                    resp = requests.get(url=prep_item["assortment"]['meta']['href'], headers=config.headers).json()
                    prep_item['price'] = resp['salePrices'][0]['value']
                    logging.info(str(resp))
                except:
                    prep_item['price'] = 70000
        return prep_item
    else:
        log_helper.log.error('Тип доставки не определен')
        return False
