import requests
from jsonclass import Json
import datetime
import time
import random
import hashlib
import hmac
import urllib.parse
import decimal
from secret_encryptor import AESCipher
def stop_price(price,b,t):
    less = price * t
    tick,min = b.get_tickSize()
    dec_point = decimal.Decimal(str(tick))
    dec_point = dec_point.as_tuple().exponent
    price = less - (less % tick)
    return round(price,abs(dec_point))

def convert_time(date):
    curr = datetime.datetime.now()
    after = curr - datetime.timedelta(date)
    return int(time.mktime(after.timetuple()))

def remove_null(params):
    no_null = {}
    for key,value in params.items():
        if value == None:
            pass
        else:
            no_null[key] = value
    return no_null

def avg_spread(spread):
    bid_list = []
    for bid in spread['bids']:
        bid_list.append(float(bid[0]))
    avg_bid = sum(bid_list) / len(bid_list)
    ask_list = []
    for ask in spread['asks']:
        ask_list.append(float(ask[0]))
    avg_ask = sum(ask_list) / len(ask_list)
    return {'bid':avg_bid,'ask':avg_ask}

def symbol_to_curr(asset):
    if CONSTANTS.CURR in asset:
        return asset
    else:
        return asset + CONSTANTS.CURR

def balance_calc(account):
    # print(account)
    assets = curr_calc(account)
    for dictionary in account['balances']:
        free = float(dictionary['free'])
        if free > 0:
            symbol = symbol_to_curr(dictionary['asset'])
            if symbol != CONSTANTS.CURR:
                b = binance(ticker=symbol)
                assets += free * b.get_depth(avg=True)['bid']
    return assets



def curr_calc(account):
    assets = 0
    for dictionary in account['balances']:
        if dictionary['asset'] == CONSTANTS.CURR:
            assets += float(dictionary['free'])
    return assets

def get_lot(fil):
    for i in fil:
        if i['filterType'] == 'LOT_SIZE':
            return i['stepSize']


class binance:
    def __init__(self,api_key=None,secret=None,ticker=None,time=None) -> None:
        self.api_key = api_key
        self.secret = secret
        self.sess = requests.Session()
        self.url = 'https://api.binance.com/api/v3'
        self.ticker = ticker if ticker is not None else None
        self.header = self.get_header()
        self.time = time if time is not None else self.get_server_time()
    def ohlc(self,interval,startTime=None,endTime=None,limit=None):
        parameter = {
            'symbol':self.ticker,
            'interval':interval,
            'startTime':startTime,
            'endTime':endTime,
            'limit':limit
        }
        return self._url_get('klines',parameter=parameter)
    
    def buy(self,type='MARKET',timeInForce=None,price=None,quantity=None,recvWindow=5000,timestamp=None,stopPrice=None):
        timestamp = timestamp if timestamp is not None else self.time
        parameter = {
            'symbol':'BTCcurr',
            'side':'BUY',
            'type':'LIMIT',
            'timeInForce':'GTC',
            'quantity':'1',
            'price':'61809',
            'recvWindow':'5000',
            'timestamp':self.time,
        }
        parameter = self.get_order('BUY',type,timeInForce,price,quantity,recvWindow,timestamp,stopPrice)
        return self._url_post('order',parameter=parameter,header=self.get_header(),signature=True)



    def sell(self,quantity,type='MARKET',timeInForce=None,price=None,recvWindow=5000,timestamp=None,stopPrice=None):
        timestamp = timestamp if timestamp is not None else self.time
        parameter = self.get_order('SELL',type,timeInForce,price,quantity,recvWindow,timestamp,stopPrice)
        return self._url_post('order',parameter=parameter,header=self.get_header(),signature=True)


    def get_avg_price(self,ticker):
        '''{
  "mins": 5,
  "price": "9.35751834"
}'''
        parameter = {
            'symbol':ticker
        }
        return self._url_get('avgPrice',parameter=parameter)

    def get_order(self,sell_buy,type,timeInForce,price,quantity,recvWindow,timestamp,stopPrice):
        timestamp = timestamp if timestamp is not None else self.time
        parameter = {
            'symbol':self.ticker,
            'side':sell_buy,
            'type':type,
            'timeInForce':timeInForce,
            'quantity':quantity,
            'price':price,
            'recvWindow':recvWindow,
            'timestamp':timestamp,
            'stopPrice':stopPrice
        }
        return parameter

    def get_book_ticker(self):
        parameter = {
            'symbol':self.ticker
        }
        return self._url_get('ticker','bookTicker',parameter=parameter)
    def acc_info(self):
        parameter = {
            'timestamp':self.time
        }
        return self._url_get('account',parameter=parameter,header=self.header,signature=True)
    
    def get_trade_hist(self,ticker,orderId=None,startTime=None,endTime=None,fromId=None,limit=None,recvWindow=None,timestamp=None):
        timestamp = timestamp if timestamp is not None else self.time
        parameters = {
            'symbol':ticker,
            'orderId':orderId,
            'startTime':startTime,
            'endTime':endTime,
            'fromId':fromId,
            'limit':limit,
            'recvWindow':recvWindow,
            'timestamp':timestamp
        }
        return self._url_get('myTrades',parameter=parameters,header=self.header,signature=True)
    def get_depth(self,limit=100,avg=True):
        parameter = {
            'symbol': self.ticker,
            'limit': limit
        }
        if avg == False:
            return self._url_get('depth',parameter=parameter)
        else:
            bid_ask = self._url_get('depth',parameter=parameter)
            return avg_spread(bid_ask)
    


    def get_balance(self):
        account = self.acc_info()
        return balance_calc(account)
    def get_curr(self):
        account = self.acc_info()
        return curr_calc(account)
    def get_signature(self,params):
        params = remove_null(params)
        parameter = urllib.parse.urlencode(params)
        params['signature'] = hmac.new(self.secret.encode('utf-8'),parameter.encode('utf-8'), hashlib.sha256).hexdigest()
        return params

    def get_all_orders(self,orderId,startTime=None,endTime=None,fromId=None,limit=None,recvWindow=None,timestamp=None):

        parameter = {
            'symbol':self.ticker,
            'orderId':orderId,
            'startTime':startTime,
            'endTime':endTime,
            'fromId':fromId,
            'limit':limit,
            'recvWindow':recvWindow,
            'timestamp':self.time

        }
        return self._url_get('myTrade',parameter=parameter,header=self.header,signature=True)

    def get_test_order(self,buy_sell='BUY',type='MARKET',timeInForce=None,price=None,quantity=None,recvWindow=5000,timestamp=None,stopPrice=None):
        timestamp = timestamp if timestamp is not None else self.time
        parameter = self.get_order(buy_sell,type,timeInForce,price,quantity,recvWindow,timestamp,stopPrice)
        return self._url_post('order','test',parameter=parameter,header=self.get_header(),signature=True)



    def get_server_time(self):
        return self._url_get('time')['serverTime']

    def _url_get(self,*attributes,parameter=None,header=None,signature=False):
        parameter = parameter if parameter is not None else None
        header = header if header is not None else None
        if signature == True:
            parameter = self.get_signature(parameter)
        url = self.url
        for attribute in attributes:
            url += '/' + attribute

        r = self.sess.get(url,params=parameter,headers=header)
        # print(r.json(),self.ticker)
        return r.json()
    def _url_post(self,*attributes,parameter=None,header=None,signature=False):
        parameter = parameter if parameter is not None else None
        header = header if header is not None else None
        if signature == True:
            parameter = self.get_signature(parameter)
        url = self.url
        for attribute in attributes:
            url += '/' + attribute

        r = self.sess.post(url,params=parameter,headers=header)
        return r.json()
    def get_header(self):
        header = {
            'X-MBX-APIKEY':self.api_key,
        }
        return header
    
    def get_tickSize(self,notional=True):
        parameter = {
            'symbol':self.ticker
        }
        filters = self._url_get('exchangeInfo',parameter=parameter)['symbols'][0]['filters']
        if notional == True:
            # print(filters)
            return float(filters[0]['tickSize']), float(filters[3]['minNotional'])
        else:
            return float(filters[0]['tickSize'])

    def get_exchangeInfo(self):
        parameter = {
            'symbol':self.ticker
        }
        return self._url_get('exchangeInfo',parameter=parameter)


    def get_percent_price(self):
        ex = self.get_exchangeInfo()
        print(ex)

    def post_oco(self,**kwargs):
        kwargs['symbol'] = self.ticker
        '''symbol, listClientOrderId, side, quantity, limitClientOrderId,price,limitClientOrderId
        price,limitIcebergQty,stopClientOrderId,stopPrice,stopLimitPrice,stopIcebergQty,stopLimitTimeInForce
        newOrderRespType,recvWindow'''
        kwargs['timestamp'] = self.time
        return self._url_post('order','oco',parameter=kwargs,header=self.get_header(),signature=True)

    def all_orders(self,recvWindow=None):
        parameter = {
            'recvWindow':recvWindow,
            'timestamp':self.time
        }
        return self._url_get('rateLimit','order',parameter=parameter,header=self.header,signature=True)



    def get_lot_size(self,min=False):
        parameter = {
            'symbol':self.ticker
        }
        filters = self._url_get('exchangeInfo',parameter=parameter)['symbols'][0]['filters']
        if min == False:
            return get_lot(filters)
        else:
            return get_lot(filters),float(filters[3]['minNotional'])
def fiveyears(symbol):
    iter_date = 83.333333333333333333333
    diff_time = 250
    curr_time = convert_time(0)
    end_time = convert_time(diff_time)
    candle = {}
    b = binance(ticker=symbol)
    while end_time < curr_time:
        # ohlc = b.ohlc('2h',startTime=end_time,limit=1000)
        ohlc = 2
        print(datetime.datetime.utcfromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S'))
        candle[end_time] = ohlc
        diff_time -= iter_date
        end_time = convert_time(diff_time)
        # time.sleep(2)     
    J = Json(symbol + '.txt')
    J.createDump(candle)
def get_pass():
    j = Json('keys.txt').readByte()
    password = str(input('enter a password to decrypt your keys: '))
    a = AESCipher(password)
    public = a.decrypt(j['public'])
    private = a.decrypt(j['secret'])
    return public, private
if __name__ == '__main__':
    symbol = 'AVAXUSDT'
    
    public,private = get_pass()
    b = binance(api_key=public,secret=private)
    # print(b.buy('LIMIT',timeInForce='GTC',price=1.8500,quantity=70.2))
    # print(round(time.time(),0))
    A = b.get_trade_hist('')
    print(A,len(A))
    # b = 0
    # for i in A:
    #     f = float(i['quoteQty'])
    # p = float(b.get_avg_price()['price'])
    # stop_loss = stop_price(p,b,0.75)
    # p = stop_price(p,b,1)
    # s,qty = b.get_tickSize()
    # a = b.get_test_order(type='STOP_LOSS_LIMIT',quantity=qty,timeInForce='GTC',price=p,stopPrice=stop_loss)
    # print(a)
    # print(b.get_test_order(
    #     buy_sell='BUY',type='LIMIT',price=float(b.get_avg_price()['price'])*0.95,quantity=1,timeInForce='GTC'
    # ))
    # oh = b.ohlc('2h',limit=1000)
    # J = Json(symbol + '.txt',r'C:\Users\Erik\Desktop\crypto_database\ohlc')
    # J.createDump(oh)
    # fiveyears('BTCcurr')
