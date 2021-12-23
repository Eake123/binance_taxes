# binance_taxes
calculates your taxes from x time. Also shows you all the trades you've made since x date, and the gain/loss on it in gross terms


It uses FIFO to calculate your taxes.

to get the requirements enter "pip install -r requirements.txt" into your terminal

The script creates an xlsx. The taxes tab shows you the net amount you've made/lossed since x date. The trade_sheet shows all the trades you've made since x date. And the other sheets show you each coin you've traded and the profit/loss on it.

When you run get_all_trades.py you're prompted with some user inputs. The first is the pairs. You have to enter in all the pairs you've ever used. so if you've bought BTC with USDT and BUSD then you'd only enter USDT and BUSD into it.

You'll then be prompted with the start date for the calculations. So if you want to calculate the net amount you've made trading since november 1st you'd enter 2021-11-01. You can also enter 1 and the start date will be current year - 01 - 01

After you'll have to enter in your api key and secret key. https://www.binance.com/en/support/faq/360002502072

You can save your keys if you want and they will be encrypted using AES and the key is the hash of the password you enter.

The script takes a few minutes to run because binance only lets you make a certain amount of requests.
