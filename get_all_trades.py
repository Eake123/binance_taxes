from bin import binance
from jsonclass import Json
import time
import operator
import datetime
from secret_encryptor import AESCipher
from do_taxes import get_all_trades
import os
import logging
from getpass import getpass
class user_pref:
    def __init__(self) -> None:
        pass
    
    def main(self):
        pairs = self.get_pairs()
        start = self.start_date()
        # end = self.end_date()
        public,secret = self.api_main()
        dic = {'pairs':pairs,'start':start,'public':public,'secret':secret}
        return dic




    # def end_date(self):
    #     s = str(input('what date do you want to end at Y-M-D (ex. 2021-12-20), or enter 1 to start at current time: '))
    #     if s == '1':
    #         return int(time.time() - 20)
    #     else:

    #         return self.date_to_unix(s)
    def api_main(self):
        try:
            public,secret = self.get_pass()
        except:
            public = str(getpass('input your api key: '))
            secret = str(getpass('input your secret: '))
            self.api(public,secret)
        os.environ['public'] = public
        os.environ['private'] = secret
        return public,secret

    def api(self,public,secret):
        yn = str(input('do you want to save your key with AES encryption (Y/N): '))
        if yn == 'Y':
            password = str(getpass('enter a password to use as encryption: '))
            a = AESCipher(password)
            dic = {'public':a.encrypt(public),
            'secret':a.encrypt(secret)}
            Json('keys.txt').createByte(dic)


    def get_pass(self):
        j = Json('keys.txt').readByte()
        password = str(getpass('enter a password to decrypt your keys: '))
        a = AESCipher(password)
        public = a.decrypt(j['public'])
        private = a.decrypt(j['secret'])


        return public,private
    def start_date(self):
        s = str(input('what date do you want to start at Y-M-D (ex. 2021-12-20), or enter 1 to start at january first of the current year: '))
        if s == '1':
            now = datetime.datetime.now()
            s = str(now.year) + '-01-01'
        else:
            s = s
        return self.date_to_unix(s)

    def date_to_unix(self,t):
        d = datetime.datetime.strptime(t, '%Y-%m-%d')
        return int(time.mktime(d.timetuple()))



    def get_pairs(self):
        pair_list = []
        while True:
            pair = str(input('enter the pairs youve used, ex. USDT, when done enter 1: '))
            if pair == '1':
                break
            else:
                pair_list.append(pair.upper())
        return pair_list


class death_and_taxes:
    def __init__(self) -> None:
        self.pairs,self.start,api_key,secret = self.get_pref()
        self.binance = binance(api_key,secret)
        self.acc_info = self.get_acc_info(self.binance.acc_info())
        self.all_tickers = self.acc_info['balances']
        self.weight_limit = {'time':{time.time():10}}
        self.time = self.binance.time
        self.weight_total = 1100
    
    def get_acc_info(self,acc):
        if isinstance(acc,dict):
            if acc.get('code') == -1022 or acc.get('code') == -1099 or acc.get('code') == -1002 or acc.get('code') == -2014:
                raise ValueError('wrong api key or secret')
        return acc


    def get_pref(self):
        u = user_pref()
        dic = u.main()
        return  dic['pairs'],dic['start'],dic['public'],dic['secret']


    def main(self):
        trade_list = self.iter_trades()
        return trade_list


    def iter_trades(self):
        total_list = []
        for ticker in self.all_tickers:
            trade_list = self.ticker_check(ticker)
            if len(trade_list) > 0:
                total_list.append(trade_list)
        return total_list

    
    def ticker_check(self,ticker):
        ticker = ticker['asset']
        trade_list = []
        for pair in self.pairs:
            new_ticker = ticker + pair
            if self.good_ticker(new_ticker):
                check = self.check_trade(new_ticker)
                if check != False:
                    trade_list.append(check)
        return trade_list
    
    def good_ticker(self,ticker):
        j = Json('bad_ticker.txt')
        if ticker in j.readKey():
            return False
        else:
            return True


    def update_weight(self,time_dict):
        new_dict = {}
        sum_weight = 0
        minute_ago = time.time() - 60
        for key,value in time_dict.items():
            if key >= minute_ago:
                new_dict[key] = value
                sum_weight += value
        self.weight_limit = {'time':new_dict}
        return new_dict,sum_weight


    def get_start(self,time_dict,value):
        v = 0
        cd = sorted(time_dict.items(),key=operator.itemgetter(0),reverse=False)
        for i in cd:
            v += i[1]
            if v >= value:
                return i[0]


    def _weight(self,value):
        key = time.time()
        if self.weight_limit.get('time') is None:
            print(self.weight_limit)
        time_dict,sum_weight = self.update_weight(self.weight_limit['time'])
        start = self.get_start(time_dict,value)
        if value + sum_weight >= self.weight_total:
            time.sleep(start+60-key)
        if key in time_dict.keys():
            time_dict[key] += value
        else:
            time_dict[key] = value
            self.weight_limit = {'time':time_dict}



    # def _weight(self,value):
    #     if time.time() - self.weight_limit['time'] >= 60:
    #         self.weight_limit = {'time':time.time(),'requests':1}
    #     else:
    #         request = self.weight_limit['requests']
    #         if request + value >= 1200:
    #             s = self.weight_limit['time'] + 60 - time.time()
    #             time.sleep(s)
    #             self._weight(0)
    #         else:
    #             self.weight_limit['requests'] += value

    def add_bad(self,ticker):
        j = Json('bad_ticker.txt')
        j.dualDump(ticker)


    def check_trade(self,ticker,debug=False):
        self._weight(10)
        r = self.binance.get_trade_hist(ticker,timestamp=self.time,startTime=self.start)
        if debug:
            print(r,ticker)
        if isinstance(r,list):
            if len(r) > 0:
                check = r
            else:
                check = False
        elif isinstance(r,dict):
            if r['code'] == -1021:
                self.time = self.binance.get_server_time()
                self._weight(11)
                return self.check_trade(ticker,False)
            elif r['code'] == -1121:
                self.add_bad(ticker)
            elif r['code'] == -1003:
                logging.warning('over the weight limit')
            check = False

        else:
            check = False
        return check
if __name__ == '__main__':
    d = death_and_taxes()
    trades = d.main()

    g = get_all_trades(trades)
    g.excel()


