import pandas as pd
import pickle
import requests
import bs4 as bs


# r'csvFile/data_e.xls'
def getJpStockCode(filePath):
    file = filePath
    df = pd.read_excel(file)
    ret_list = []
    for i in range(df.shape[0]):
        #if df['Section/Products'][i] == "First Section (Domestic)":
            # print(df['Local Code'][i])
        ret_list.append(str(df['Local Code'][i]) + ".T")

    return ret_list


def getTwStockCode(filePath):
    file = filePath
    df = pd.read_excel(file)
    ret_list = []
    for i in range(df.shape[0]):
        ret_list.append(str(df['code'][i][0:4])+".TW")
    return ret_list


# 抓 sp500的股票代號
def get_sp500_tickers():
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies', verify=False)

    soup = bs.BeautifulSoup(resp.text)
    table = soup.find('table', {'class': 'wikitable sortable'})  # specify which table we want from the url we set
    tickers = []
    for row in table.findAll('tr')[1:]:  # skip the first table row cuz its not what we want
        ticker = row.findAll('td')[0].text  # symbol column is at 0
        ticker = ticker.strip()
        tickers.append(ticker)
    with open("sp500tickers.pickle", "wb") as f:
        pickle.dump(tickers, f)
    # print(tickers)
    return tickers
