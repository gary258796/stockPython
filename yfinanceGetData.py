import random
import ssl
import urllib
import yfinance as yf

ssl._create_default_https_context = ssl._create_unverified_context
response = urllib.request.urlopen('https://www.python.org')

proxies = ['', '61.220.204.25:3128', '52.140.242.103:3128', '60.251.40.84:1080']
# yahoo finance相關function( not useful now )
class myStock():
    def __init__(self, stockNum):
        self.stockNum = stockNum
        self.stock = yf.Ticker(stockNum)

    # Stock Num(股票號碼)
    def getMyStockNum(self):
        return self.stockNum

    # Stock Info(股票資訊)
    def getMyStockInfo(self):
        return self.stock.info

    # 不指定 period 就要給 start end time
    # 有指定period 就會忽略start end time
    # period	1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    # interval	   1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    # 7day > 1m, 60day > 2m 、5m ,  2 year > 60m ,
    # start	If period is not set- Download start date string (YYYY-MM-DD) or datetime	2020-03-18
    # end	If period is not set - Download end date string (YYYY-MM-DD) or datetime	2020-03-19
    # Stock History( period type = 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max )
    # prepost	Boolean value to include Pre and Post market data	Default is False
    # auto_adjust	Boolean value to adjust all OHLC	Default is True
    # actions	Boolean value download stock dividends and stock splits events	Default is True
    # start = dt.datetime(2020, 3, 20)
    # end = dt.datetime(2020, 3, 22)
    # 股價歷史(最高、最低、開盤、收盤、成交量)
    def getMyStockHistoryWithPeriodorTime(self, period, start, end, interval, bool_action, bool_proxyUse):
        if bool_proxyUse:
            proxy = random.choice(proxies)
        elif not bool_proxyUse:
            proxy = None

        print("Using Proxy : " + str(proxy) + "\n")
        if period == None:
            return self.stock.history(start=start, end=end, interval=interval, actions=bool_action, proxy=proxy)
        else:  # period is not null
            return self.stock.history(period=period, interval=interval, actions=bool_action, proxy=proxy)

    # 股票開盤價格
    def getMyStockOpenWithPeriodandInterval(self, seeperiod, interval):
        return self.stock.history(period=seeperiod, interval=interval)['Open']

    # 股票收盤價
    def getMyStockCloseWithPeriodandInterval(self, seeperiod, interval):
        return self.stock.history(period=seeperiod, interval=interval)['Close']

    # 股票最高價
    def getMyStockHighWithPeriodandInterval(self, seeperiod, interval):
        return self.stock.history(period=seeperiod, interval=interval)['High']

    # 股票最低價
    def getMyStockLownWithPeriodandInterval(self, seeperiod, interval):
        return self.stock.history(period=seeperiod, interval=interval)['Low']

    # 股票成交量
    def getMyStockVolumeWithPeriodandInterval(self, seeperiod, interval):
        return self.stock.history(period=seeperiod, interval=interval)['Volume']

    # 股票股利
    def getMyStockDividends(self):
        return self.stock.dividends;
        # 股票分割

    def getMyStockSplits(self):
        return self.stock.splits;

    # 股票主要持有者
    def getMyStockMajorHolders(self):
        return self.stock.major_holders;
        # 機構持有者

    def getMyStockInstitutionalHolders(self):
        return self.stock.institutional_holders;
        # 資產負債表

    def getMyStockBalanceSheet(self):
        return self.stock.balance_sheet;
        # 公司財務報表

    def getMyStockfinancials(self):
        return self.stock.financials;
        # 公司季節財務報表

    def getMyStockfinancials(self):
        return self.stock.quarterly_financials;

    # 股票市現率
    def getMyStockCashflow(self):
        return self.stock.cashflow;
        # 股票季節市現率

    def getMyStockQuarterCashflow(self):
        return self.stock.quarterly_cashflow;

    # 股票市盈率
    def getMyStockEarnings(self):
        return self.stock.earnings;
        # 股票季節市盈率

    def getMyStockQuarterEarnings(self):
        return self.stock.quarterly_earnings;
        # 股票股息

    def getMyStockSustainability(self):
        return self.stock.sustainability;
        # show next event (earnings, etc)

    def getMyStockCalender(self):
        return self.stock.calendar;

    def getMyStockRecommendations(self):
        return self.stock.recommendations;
#
# def get_host_ip():
#     try:
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         s.connect(('8.8.8.8', 8080))
#         ip = s.getsockname()[0]
#     finally:
#         s.close()
#
#     return ip
#
# def main():
#     # print(socket.gethostbyname(socket.gethostname()))
#
# if __name__ == '__main__':
#     main()
