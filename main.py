from flask import Flask, request, make_response
import config
import grequests
import requests
import json
import sys
import datetime
import asyncio
import delivery_controller as dc
import log_helper

app = Flask(import_name=__name__)

if __name__ == "__main__":
    # log_helper.init_log_file()
    app.run()


@app.route("/api/make_order", methods=['POST'])
def make_order(data=None):
    try:
        if data:
            req_data = data
        else:
            req_data = request.json
        if 'test' in req_data:
            return make_response('good', 200)
        auth_check = False
        if req_data['Authorization'] == config.authorization_token or req_data[
            'Authorization'] == config.authorization_token_sazh:
            auth_check = True
        if auth_check:
            log_helper.log.info('Информация по заказу\n' + str(req_data))
            address = ''
            if 'formid' in req_data:
                if req_data['formid'] == 'form743975566':
                    log_helper.log.info('Отзыв')
                    return make_response('Это отзыв', 200)
            if str(req_data['payment']['delivery']).startswith('Доставка до адрес'):
                if 'adress' in req_data:
                    address = req_data['adress']
                else:
                    req_data['adress'] = 'Адрес отсутствует'
                    address = req_data['adress']
                try:
                    if req_data['Authorization'] == config.authorization_token_sazh:
                        min_del_price = requests.get(url=config.min_price_delivery_sazh, headers=config.headers)
                    else:
                        min_del_price = requests.get(url=config.min_price_delivery, headers=config.headers)
                    if min_del_price.status_code == 200:
                        amount = 0
                        if 'discount' in req_data['payment']:
                            amount = int(float(req_data['payment']['subtotal']) * 100) - int(
                                float(req_data['payment']['discount']) * 100)
                        else:
                            amount = int(float(req_data['payment']['amount']) * 100)
                        if amount >= int(min_del_price.json()['name']) * 100:
                            req_data['payment']['delivery_price'] = 0
                except:
                    print('не получается получить минимальную цену доставки')
                # try:
                #     address = address.replace('RU: ', '').replace('Point: ', '')
                # except:
                #     print(str(str(datetime.datetime.now()))) print('нечего удалять')
            client = create_client_in_mc(phone=req_data['Phone'], email=req_data['Email'], name=req_data['Name'],
                                         address=address)
            print('plfhjd')
            if not client:
                make_response('Не удалось найти/создать клиента phone=' + req_data['Phone'], 500)
            else:
                descr = make_comment_for_order(req_data)
                print('sda')
                payload = make_payload_for_order(req_data, client)
                print('sda222')
                print(payload)
                for item in payload:
                    item['description'] = descr
                    payload_json = json.dumps(item)

                    headers = config.headers
                    order = requests.post(url=config.mc_host + '/api/remap/1.2/entity/customerorder', headers=headers,
                                          data=payload_json)
                    del payload_json
                    print('dfffff')
                    print(order.json())
                    if order.status_code != 200:
                        log_helper.log.error('Произошла ошибка при создании заказа\n' + str(order.json()))
                        return make_response('Произошла ошибка при создании заказа\n' + str(order.json()))
                    else:
                        requests.get(
                            url='https://alarma.msapps.ru/notifications/webhook/379fe835-473c-11ea-0a80-04bd00002ed4/416/?type={type}&id={id}'.format(
                                type='customerorder', id=order.json()['id']))
            return make_response('Успешно создан заказ!', 200)
        else:
            log_helper.log.error('Неккоректный токен')
            return make_response('Неккоректный токен', 500)
    except:
        print(sys.exc_info())
        log_helper.log.error('Произошла ошибка' + str(sys.exc_info()))
        return make_response('Произошла ошибка при создании заказа', 500)


def get_last_order_name():
    url = config.mc_host + '/api/remap/1.2/entity/customerorder' + '?order=name,desc&limit=1'
    try:
        resp = requests.get(url=url, headers=config.headers)
        if resp.status_code == 200:
            try:
                name1 = '0' + str(int(resp.json()['rows'][0]['name']) + 1)
                name2 = '0' + str(int(resp.json()['rows'][0]['name']) + 2)

                return name1, name2
            except:
                print('hey')
                print(sys.exc_info())
                return False
        else:
            return False
    except:
        print('heye')
        print(sys.exc_info())
        return False


def exception_handlerr(request, exception):
    print("Request failed", request.url)


def make_payload_for_order(data, client_id):
    if not data:
        return False
    headers = config.headers
    del_address = ''
    attribute_for_sms = ''
    print('привеееетииккии')
    if data['payment']['delivery'].startswith('Доставка до адреса'):
        del_address = data['adress']
    elif 'Выдач' in data['payment']['delivery']:
        if 'pwz' in data:
            attribute_for_sms = config.attribute_delivery_addr_pwz
            attribute_for_sms['value'] = data['pwz']
        # try:
        #     address = address.replace('RU: ', '').replace('Point: ', '')
        # except:
        #     print(str(str(datetime.datetime.now()))) print('нечего удалять')
    # Для всего остального
    payload1 = {
        "organization": {
            "meta": {
                "href": "https://api.moysklad.ru/api/remap/1.2/entity/organization/" + config.organization_id,
                "type": "organization",
                "mediaType": "application/json"
            }
        },
        "agent": {
            "meta": {
                "href": "https://api.moysklad.ru/api/remap/1.2/entity/counterparty/" + client_id,
                "type": "counterparty",
                "mediaType": "application/json"
            }
        },
        "store": {
            "meta": {
                "href": "https://api.moysklad.ru/api/remap/1.2/entity/store/" + config.store_id,
                "type": "store",
                "mediaType": "application/json"
            }
        },
        "shipmentAddressFull": {
            "addInfo": del_address,
            "comment": "Адрес электронной почты: " + data['Email'] + "\nИмя: " + data['Name']
        },
        "attributes": [],
        "positions": [
        ]
    }
    if attribute_for_sms != '':
        payload1['attributes'].append(attribute_for_sms)
    # Для саженцев
    payload2 = {
        "organization": {
            "meta": {
                "href": "https://api.moysklad.ru/api/remap/1.2/entity/organization/" + config.organization_id,
                "type": "organization",
                "mediaType": "application/json"
            }
        },
        "agent": {
            "meta": {
                "href": "https://api.moysklad.ru/api/remap/1.2/entity/counterparty/" + client_id,
                "type": "counterparty",
                "mediaType": "application/json"
            }
        },
        "store": {
            "meta": {
                "href": "https://api.moysklad.ru/api/remap/1.2/entity/store/" + config.store_id,
                "type": "store",
                "mediaType": "application/json"
            }
        },
        "shipmentAddressFull": {
            "addInfo": del_address,
            "comment": "Адрес электронной почты: " + data['Email'] + "\nИмя: " + data['Name']
        },
        "attributes": [],
        "positions": [
        ]
    }

    # добавляем order_id для дальнейшей идентификации на робокассе
    order_id1 = config.attribute_order_id
    order_id2 = config.attribute_order_id
    order_id1['value'] = data['payment']['orderid']
    order_id2['value'] = data['payment']['orderid']
    payload2['attributes'].append(order_id1)
    payload1['attributes'].append(order_id2)

    if 'promocode' in data['payment']:
        promocode_value = config.attribute_promocode
        promocode_value['value'] = data['payment']['promocode']
        payload2['attributes'].append(promocode_value)
        payload1['attributes'].append(promocode_value)

    # присваиваем корректный номер заказа
    # name1, name2 = get_last_order_name()
    # if name1 and name2:
    #     payload1['name'] = name1
    #     payload2['name'] = name2
    if 'pwz' not in data or del_address != '':
        data['pwz'] = None
    attr = dc.append_delivery(addre=data['payment']['delivery'], pwz=data['pwz'])
    if attr:
        payload1["attributes"].append(attr)
        payload2["attributes"].append(attr)

    products_arr = []
    for item in data['payment']['products']:
        try:
            if 'externalid' in item:
                print(item['quantity'])
                url = config.mc_host + '/api/remap/1.2/entity/product' + '?filter=externalCode=' + item['externalid']
                products_arr.append({'url': url, 'quantity': item['quantity'], 'price': item['price'],
                                     'external_id': item['externalid'], 'item': {}})
        except:
            print(str(str(datetime.datetime.now())))
            print(sys.exc_info())
    rs = (grequests.get(url=u['url'], headers=headers) for u in products_arr)
    for idx, t in enumerate(grequests.map(rs, exception_handler=exception_handlerr, size=5)):
        print(t.status_code)
        if t.status_code == 200 and len(t.json()['rows']) != 0:
            products_arr[idx]['item'] = t.json()

    discount = 0
    if 'discountvalue' in data['payment'] and data['payment']['discountvalue'] != '0%':
        try:
            discount = int(str(data['payment']['discountvalue'])[:-1])
        except:
            discount = 0
    for idx in products_arr:
        prep_item = {
            "quantity": idx['quantity'],
            "reserve": idx['quantity'],
            "price": float(idx['price']) * 100,
            "discount": discount,
            "vat": 0,
            "assortment": {
                "meta": {
                    "href": "https://api.moysklad.ru/api/remap/1.2/entity/product/" +
                            idx['item']['rows'][0]['id'],
                    "type": 'product',
                    "mediaType": "application/json"
                }}}
        if 'productFolder' in idx['item']['rows'][0]:
            if idx['item']['rows'][0]['productFolder']['meta']['href'][-36:] == config.seedling_product_folder_id:
                payload2['positions'].append(prep_item)
            else:
                payload1['positions'].append(prep_item)
        else:
            payload1['positions'].append(prep_item)
        prep_item = {}
    payload_arr = []
    if not payload1['positions']:
        if not payload2['positions']:
            payload1['positions'].append(
                dc.append_delivery_item(data['payment']['delivery'], 1, data['payment']['delivery_price']))
            payload_arr.append(payload1)
            print('вот тут вот')
        else:
            payload2['positions'].append(
                dc.append_delivery_item(data['payment']['delivery'], 2, data['payment']['delivery_price']))
            payload_arr.append(payload2)
            print('вот тут вот2')
    else:
        print(payload1['positions'])
        payload1['positions'].append(
            dc.append_delivery_item(data['payment']['delivery'], 1, data['payment']['delivery_price']))
        payload_arr.append(payload1)
        if payload2['positions']:
            payload2['positions'].append(
                dc.append_delivery_item(data['payment']['delivery'], 2, data['payment']['delivery_price']))
            payload_arr.append(payload2)
            print('вот тут вот4')
    return payload_arr


def make_comment_for_order(data):
    descr = ''
    if 'delivery_comment' in data['payment']:
        if data['payment']['delivery_comment'] != '':
            descr += '\nКомментарий: ' + data['payment']['delivery_comment']
    if 'comment' in data:
        if data['comment'] != '':
            descr += '\nКомментарий: ' + data['comment']
    return descr


def create_client_in_mc(phone, name, email, address):
    client = find_client_in_mc(phone)
    print('нашли')
    if not client:
        try:
            url_part = config.mc_host + '/api/remap/1.2/entity/counterparty'
            headers = config.headers
            payload = {
                'name': name,
                'phone': str(phone),
                'email': email,
                'description': 'Лид с сайта',
                'actualAddress': address
            }
            response = requests.request("POST", url_part, data=json.dumps(payload), headers=headers)
            print(datetime.datetime.now())
            print(response.status_code)
            agent_id = response.json()['id']
            return agent_id
        except:

            print(sys.exc_info())
            return False
    else:
        if address == '':
            return client
        else:
            print('мы здеся')
            try:
                url_part = config.mc_host + '/api/remap/1.2/entity/counterparty/' + client
                headers = config.headers
                payload = {
                    'actualAddress': address,
                    'email': email
                }
                response = requests.request("PUT", url_part, data=json.dumps(payload), headers=headers)
                print(response.status_code)
                if response.status_code == 200:
                    return client
                else:
                    return client
            except:
                print(sys.exc_info())
                print('Не удалось обновить информацию по клиенту')
                return client


def find_client_in_mc(phone):
    try:
        url = config.mc_host + '/api/remap/1.2/entity/counterparty?search=' + phone
        headers = config.headers
        req = requests.get(url=url, headers=headers)
        req_json = req.json()
        if len(req_json['rows']) > 0:
            return req_json['rows'][0]['id']
        else:
            return False
    except:
        return False


def find_orders_with_id(order_id):
    url = config.mc_host + '/api/remap/1.2/entity/customerorder?filter=' + config.attribute_order_id['meta'][
        'href'] + '=' + order_id
    orders_arr = []
    try:
        headers = config.headers
        req = requests.get(url=url, headers=headers)
        if req.status_code == 200:
            req_json = req.json()
            if req_json['meta']['size'] != 0:
                return req_json
            else:
                print('Нет заказов с таким order_id')
                return False
        else:
            print('Запрос в МС неуспешен на получение заказов с order_id')
            return False
    except:
        print(sys.exc_info())
        print('Произошла ошибка при запросе заказво с order_id')
        return False


def create_invoice(client_id, sum, operations, order_id, mc_orders, total, phone, name):
    url = config.mc_host + '/api/remap/1.2/entity/paymentin'
    headers = {
        'Accept': 'application/json;charset=utf-8',
        'Authorization': 'Bearer ' + config.moysklad_token_prod,
        'Content-Type': 'application/json'
    }
    orders_name = ''
    for item in mc_orders['rows']:
        orders_name += ' ' + str(item['name'])
    print(sum)
    payload = json.dumps({
        "organization": {
            "meta": {
                "href": "https://api.moysklad.ru/api/remap/1.2/entity/organization/" + config.organization_id,
                "type": "organization",
                "mediaType": "application/json"
            }
        },
        "agent": {
            "meta": {
                "href": client_id,
                "type": "counterparty",
                "mediaType": "application/json"
            }
        },
        "sum": sum,
        "description": "Заказ(-ы) " + orders_name + ' оплачен\n(Тильда: ' + str(
            order_id) + ')' + '\n\nСумма заказа(-ов): ' + str(
            total / 100) + '\nСумма оплаты: ' + str(sum / 100),
        "operations": operations
    })

    log_helper.log.info('Создаем такой платеж:  ' + str(payload))
    try:
        res = requests.post(url=url, headers=headers, data=payload)
        if res.status_code == 200:
            return res.json()['id']
        else:
            log_helper.log.error('Запрос на создание платежа неудачный. Код ответа ' + str(res.status_code))
            print('Запрос на создание платежа неудачный')
            return False
    except:

        print(sys.exc_info())
        print('Запрос на создание платежа неудачный')
        return False


def change_order_state(ord_id, state_id):
    url = config.mc_host + '/api/remap/1.2/entity/customerorder/' + ord_id
    headers = config.headers
    payload = json.dumps({
        "attributes": [
            config.attribute_place_payment
        ],
        "state": {
            "meta": {
                "href": "https://api.moysklad.ru/api/remap/1.2/entity/customerorder/metadata/states/" + state_id,
                "metadataHref": "https://api.moysklad.ru/api/remap/1.2/entity/customerorder/metadata",
                "type": "state",
                "mediaType": "application/json"
            }}
    })
    try:
        resp = requests.put(url=url, headers=headers, data=payload)
        if resp.status_code == 200:
            return True
        else:
            print('Не удалось изменить статус заказа')
            try:
                print(resp.json())
            except:
                print(resp.status_code)
            return False
    except:
        print('Не удалось изменить статус заказа')
        print(sys.exc_info())
        return False


@app.route("/api/submit_payment", methods=['POST'])
def submit_order():
    req_data = request.json
    if 'test' in req_data:
        return make_response('good', 200)
    auth_check = False
    if 'Authorization' in req_data:
        if req_data['Authorization'] == config.authorization_token or req_data['Authorization'] == config.authorization_token_sazh:
            auth_check = True
    if 'paymentsystem' in req_data:
        if req_data['paymentsystem'] == 'cash':
            print('Оплата не по карте')
            return make_response('Оплата не по карте', 200)
    if auth_check and 'sys' in req_data['payment']:
        if req_data['payment']['sys'] == 'robokassa':
            orders = find_orders_with_id(req_data['payment']['orderid'])
            if not orders:
                make_order(data=req_data)
                orders = find_orders_with_id(req_data['payment']['orderid'])
                if not orders:
                    return make_response(
                        'Ошибка при создании оплаты по заказу - заказ не был найден' + str(datetime.datetime.now()),
                        200)

            orders_arr = []
            sum = 0
            client_id = orders['rows'][0]['agent']['meta']['href']
            diff = int(float(req_data['payment']['amount']) * 100)
            if len(orders['rows']) == 2:
                try:
                    if int(orders['rows'][0]['name']) > int(orders['rows'][1]['name']):
                        if int(orders['rows'][0]['sum']) > diff:
                            print('сумма платежа больше ')
                        else:
                            temp_item = orders['rows'][1]
                            orders['rows'][1] = orders['rows'][0]
                            orders['rows'][0] = temp_item
                except:
                    print('сортировка не требуется')
            for item in orders['rows']:
                sum += int(item['sum'])
                if diff - int(item['sum']) >= 0:
                    orders_arr.append({'meta': item['meta'], 'linkedSum': int(item['sum'])})
                    diff = diff - int(item['sum'])
                    change_order_state(item['id'], config.state_approve_id)
                else:
                    orders_arr.append({'meta': item['meta'], 'linkedSum': diff})
                    change_order_state(item['id'], config.state_new_id)
            invoice = create_invoice(client_id=client_id, sum=int(float(req_data['payment']['amount']) * 100),
                                     operations=orders_arr, order_id=req_data['payment']['orderid'], mc_orders=orders,
                                     total=sum, phone=req_data['Phone'], name=req_data['Name'])
            if invoice:
                requests.get(
                    url='https://alarma.msapps.ru/notifications/webhook/379fe835-473c-11ea-0a80-04bd00002ed4/418/?type={type}&id={id}'.format(
                        type='paymentin', id=invoice))
                return make_response('Входящий платеж успешно создан', 200)
            else:
                for idx in orders['rows']:
                    change_order_state(idx['id'], config.state_error_payment_id)
                return make_response('Не удалось создать входящий платеж', 200)
        else:
            print('Оплата не по карте')
            return make_response('Оплата не по карте', 200)
    else:
        print('Нет информации от робокассы')
        log_helper.log.error('Не удалось создать входящий платеж из-за отсутствия sys или неккоретного ключа')
        return make_response('Не удалось создать входящий платеж из-за отсутствия sys или неккоретного ключа', 500)
