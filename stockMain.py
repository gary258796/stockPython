import datetime as dt
import logging
import ssl
import sys
import time
import urllib.request
import pandas as pd
import pandas_datareader as pdr
import pymysql
from multiprocessing import Pool, Lock
import os
# own write python
import StockCodeHandler as stockCodeService
import googleDrive_IO as googleDrive_Api
import oneDrive_IO as oneDrive_API
import yfinanceGetData as yfcusGetData
import atexit

# ssl auth change to no need
ssl._create_default_https_context = ssl._create_unverified_context
response = urllib.request.urlopen('https://www.python.org')

# logging setting
LOGGING_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
DATE_FORMAT = '%Y%m%d %H:%M:%S'
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT,
                    datefmt=DATE_FORMAT,
                    handlers=[logging.FileHandler('Log/my.log', 'w', 'utf-8'), ])


def getDriveService(DriveName):
    if DriveName == "onedrive":
        service = oneDrive_API.getService()
    elif DriveName == "googledrive":
        service = googleDrive_Api.getService()
    else:
        print("This is not in Drive Service! We only provide google drive and one drive.")

    return service


# Global function
serviceorclient = getDriveService("onedrive")
lock = Lock()
noDataList = [["" for x in range(2)] for y in range(1)]
failUpdateDataList = [["" for x in range(2)] for y in range(1)]
hasData = True
db = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    passwd="gary258976",
    db='gary-python-stock')
_connection = None
load_type = None
tw_int = 0
jp_int = 0
us_int = 0

def exit_handler():
    if failUpdateDataList != None:
        store_to_mysql(failUpdateDataList)
    elif noDataList != None:
        store_to_mysql(noDataList)

    tw, jp, us, type = getInt()
    store_progress_mysql(tw, jp, us, type)


atexit.register(exit_handler)


def get_connection():
    global _connection
    global db
    if not _connection:
        _connection = db.cursor()
    return _connection


# store no success load data to mysql db
def store_to_mysql(data):

    cursor = get_connection()

    sql = "INSERT INTO no_success_Stock_code (stock_code, load_type) VALUES (%s, %s)"
    for data in data:
        cursor.execute(sql, (data[0], data[1]))
        db.commit()

    cursor.close()
    db.close()


# before app exit, store the progress
def store_progress_mysql(tw_int, jp_int, us_int, load_type):

    conn = get_connection()

    sql = "UPDATE run_to_where SET tw_progress = %s, jp_progress = %s, us_progress = %s WHERE load_type = %s"
    val = (tw_int, jp_int, us_int, load_type)
    conn.execute(sql, val)
    db.commit()
    conn.close()
    db.close()


# # before stop
# # store the
# def exit_handler():
#     print("Before app stop, store the progress")
#     store_progress_mysql(tw_int, jp_int, us_int, load_type)


# atexit.register(exit_handler)


def getStockHistorybyPDR(start_time, end_time, stockCode):
    global hasData
    adjust_start_time = start_time
    endtime = end_time
    clean_stock_str = stockCode

    while True:
        try:
            print("Processing stock: " + clean_stock_str + " from Time : " + str(adjust_start_time) + " ...\n")
            history = pdr.get_data_yahoo(clean_stock_str, adjust_start_time, endtime)
            print(clean_stock_str + " Success!\n")
            csvOfDataFrame(history)
            hasData = True
            break  # jump out the loop
        except KeyError:
            print("Stock : " + clean_stock_str + "not public yet at : " + str(adjust_start_time) + "\n")
            adjust_start_time = add_years(adjust_start_time, 1)
            if endtime < adjust_start_time:  # start time > end time , not allow
                noDataList.append(clean_stock_str)
                hasData = False
                break
        except:
            print("Unexpected error:", sys.exc_info()[0])
            logging.info("Unexpected error:", sys.exc_info()[0])
            hasData = False
            break


def getStockHistorybyYahoo(stockCode, period, start, end, interval, bool_action, bool_proxyUse):
    stock = yfcusGetData.myStock(stockCode)
    history = stock.getMyStockHistoryWithPeriodorTime(period=period, start=start, end=end, interval=interval,
                                                      bool_action=bool_action, bool_proxyUse=bool_proxyUse)
    # print(history)
    return history


def csvOfDataFrame(dataFrame, createPath):
    dataFrame.to_csv(createPath)  # if to excel , datasource ---> xlsx


def getStockHistorybyPDRandStore2Drive(stockCodeList, driveName, start, end):
    serviceorclient = getDriveService(driveName)
    start_time = start  # dt.datetime(start_year, start_month, start_date)
    end_time = end  # dt.datetime.today()

    for i in range(len(stockCodeList)):
        need_info_dict = getFilePathandDriverFileId_Dictionary(stockCodeList[i])
        getStockHistorybyPDR(start_time, end_time,
                             need_info_dict['stock_str'])  # get stock history and store to history folder
        if not hasData:  # no stock data
            print("Stock : " + need_info_dict['stock_str'] + " no Data at all.")
            logging.info("Stock : " + need_info_dict['stock_str'] + " no Data at all.")
            continue  # skip current loop
        else:  # has data, store it to drive
            if driveName is "onedrive":
                print("Writing csv to OneDrive : " + need_info_dict['stock_str'] + ".csv\n")
                oneDrive_API.uploadFile(client=serviceorclient, Uplaodname=need_info_dict['stock_str'] + '.csv'
                                        , filePathinLocal=(r'/Users/liaoyushao/PycharmProjects/stock/' + "temp.csv"),
                                        uploadFolderId=dict['onedriveFolderId'])
            elif driveName is "googledrive":
                print("Writing csv to Google Drive : " + need_info_dict['stock_str'] + ".csv\n")
                googleDrive_Api.uploadFile(service=serviceorclient, Uplaodname=need_info_dict['stock_str'] + '.csv',
                                           filePathinLocal=(r'/Users/liaoyushao/PycharmProjects/stock/' + "temp.csv")
                                           , mimetype='text/csv',
                                           uploadFolderId=dict['googledriveFolderId'])  # store to google Drive
            print("\nFinished !\n")


def clearLastRowIfTwandJp(stockCode, history):
    if stockCode[-2:] == "TW":
        history.drop(history.tail(1).index, inplace=True)
    elif stockCode[-2:] == ".T":
        history.drop(history.tail(1).index, inplace=True)


def getStockHistorybyYahooandStore2Drive(stockCodeList, driveName, period, start, end, interval,
                                         bool_action):
    print('child process : {}'.format(os.getpid()))
    global serviceorclient
    for i in range(len(stockCodeList)):
        setInt(stockCodeList[i], i)
        bool_proxy = False
        # get all need info for storage and scathing
        need_info_dict = getFilePathandDriverFileId_Dictionary(stockCodeList[i], interval)
        for retry in range(10):  # at most retry 10 times
            try:  # try get history and store to csv in local path
                history = getStockHistorybyYahoo(stockCodeList[i], period, start, end, interval, bool_action,
                                                 bool_proxy)
                # clearLastRowIfTwandJp(stockCodeList[i], history)
                # print(history)
                # store to csv in local file
                csvOfDataFrame(history, need_info_dict['createPath'])
            except:  # have error
                logging.info("Catch exception.", exc_info=True)
                print("Unexpected error in line 154:", sys.exc_info()[0])

                if retry < 9:
                    logging.info("Retry the %d time." % (retry + 1))
                    print("Retry the %d time." % (retry + 1))
                if (retry + 1) > 5:
                    bool_proxy = False  # fail over five times, cancel using proxy and use myself
                if retry == 9:
                    logging.error("Stock code: " + stockCodeList[i] + " load failed !")
                    noDataList.append([stockCodeList[i], interval])
            else:  # if no error
                # store to drive
                try:
                    if driveName == "onedrive":
                        print("Writing csv to OneDrive : " + need_info_dict['stock_str'] + ".csv\n")
                        oneDrive_API.uploadFile(client=serviceorclient, Uplaodname=need_info_dict['stock_str'] + '.csv'
                                                , filePathinLocal=need_info_dict['createPath']
                                                , uploadFolderId=need_info_dict['onedriveFolderId'])
                        logging.info("success")
                    elif driveName == "googledrive":
                        print("Writing csv to Google Drive : " + need_info_dict['stock_str'] + ".csv\n")
                        googleDrive_Api.uploadFile(service=serviceorclient,
                                                   Uplaodname=need_info_dict['stock_str'] + '.csv',
                                                   filePathinLocal=need_info_dict['createPath']
                                                   , mimetype='text/csv',
                                                   uploadFolderId=need_info_dict['googledriveFolderId'])
                        # store to google Drive
                except:  # have error
                    logging.info("Catch exception.", exc_info=True)
                    logging.error("ERROR when upload : " + need_info_dict['stock_str'] + " ,  with type : " + interval + "\n")
                    print("Unexpected error in line 154:", sys.exc_info()[0])
                else:
                    break
            finally:  # no matter what , wait 0.5 sec until do next try
                time.sleep(0.5)


def getOriginalDataId(folderId, stockCode):
    try:
        originalDataId = oneDrive_API.getFileIdByNameUnderID(serviceorclient, stockCode, folderId)
    except:
        print("Unexpected error when get original data id : ", sys.exc_info()[0])
        logging.info("Catch exception.", exc_info=True)
    else:
        return originalDataId


def updateHistoryandStore2Drive(stockCodeList, driveName, period, start, end, interval, bool_action):
    for i in range(len(stockCodeList)):
        setInt(stockCodeList[i], i)
        bool_proxy = False
        # get all need info for storage and scathing
        need_info_dict = getFilePathandDriverFileId_Dictionary(stockCodeList[i], interval)
        originalDataId = getOriginalDataId(need_info_dict['onedriveFolderId'], need_info_dict['stock_str'] + '.csv')

        if originalDataId == None:
            logging.error("Stock : " + need_info_dict['stock_str'] + " fail to update in folder : " + need_info_dict['onedriveFolderId'])
            failUpdateDataList.append([stockCodeList[i], interval])
            break

        oneDrive_API.downloadFile(serviceorclient, originalDataId, './original_Data.csv')
        originalData = pd.read_csv("original_Data.csv")
        for retry in range(10):  # at most retry 10 times
            try:  # try get history and store to csv in local path
                # new data
                newHistory = getStockHistorybyYahoo(stockCodeList[i], period, start, end, interval, bool_action,
                                                    bool_proxy)
                csvOfDataFrame(newHistory, r'/Users/liaoyushao/PycharmProjects/stock/new.csv')
                newData = pd.read_csv("new.csv")
                # combine old and new
                final_Data = pd.concat([originalData, newData], ignore_index=True)
                csvOfDataFrame(final_Data, need_info_dict['createPath'])
            except:  # have error
                logging.info("Catch exception.", exc_info=True)

                print("Unexpected error in line 194:", sys.exc_info()[0])

                if retry < 9:
                    logging.info("Retry the %d time." % (retry + 1))
                    print("Retry the %d time." % (retry + 1))
                if (retry + 1) > 5:
                    bool_proxy = False  # fail over five times, cancel using proxy and use myself
                if retry == 9:
                    failUpdateDataList.append([stockCodeList[i], interval])
            else:  # if no error
                # store to drive
                if driveName == "onedrive":
                    print("Writing csv to OneDrive : " + need_info_dict['stock_str'] + ".csv\n")
                    oneDrive_API.uploadFile(client=serviceorclient, Uplaodname=need_info_dict['stock_str'] + '.csv'
                                            , filePathinLocal=need_info_dict['createPath']
                                            , uploadFolderId=need_info_dict['onedriveFolderId'])
                    logging.info("success")
                elif driveName == "googledrive":
                    print("Writing csv to Google Drive : " + need_info_dict['stock_str'] + ".csv\n")
                    googleDrive_Api.uploadFile(service=serviceorclient, Uplaodname=need_info_dict['stock_str'] + '.csv',
                                               filePathinLocal=need_info_dict['createPath']
                                               , mimetype='text/csv',
                                               uploadFolderId=need_info_dict['googledriveFolderId'])
                    # store to google Drive
                break
            finally:  # no matter what , wait 0.5 sec until do next try
                time.sleep(0.5)


def add_years(original_time, add_years):
    try:
        return original_time.replace(year=original_time.year + add_years)
    except ValueError:
        return original_time + (dt(original_time.year + add_years, 1, 1) - dt(original_time.year, 1, 1))


def getFilePathandDriverFileId_Dictionary(stockCode, interval):
    stock_str = stockCode[:4]
    dict = {'stock_str': stock_str}

    if interval == "1m":
        if stockCode[-2:] == "TW":
            dict['onedriveFolderId'] = '5A0F35AAEC914ADB!18186'
        elif stockCode[-2:] == ".T":
            dict['onedriveFolderId'] = '5A0F35AAEC914ADB!18181'
        else:
            dict['onedriveFolderId'] = '5A0F35AAEC914ADB!18193'
    elif interval == "2m":
        if stockCode[-2:] == "TW":
            dict['onedriveFolderId'] = '5A0F35AAEC914ADB!18187'
        elif stockCode[-2:] == ".T":
            dict['onedriveFolderId'] = '5A0F35AAEC914ADB!18182'
        else:
            dict['onedriveFolderId'] = '5A0F35AAEC914ADB!18192'
    elif interval == "1h":
        if stockCode[-2:] == "TW":
            dict['onedriveFolderId'] = '5A0F35AAEC914ADB!18188'
        elif stockCode[-2:] == ".T":
            dict['onedriveFolderId'] = '5A0F35AAEC914ADB!18183'
        else:
            dict['onedriveFolderId'] = '5A0F35AAEC914ADB!18191'
    elif interval == "1d":
        if stockCode[-2:] == "TW":
            dict['onedriveFolderId'] = '5A0F35AAEC914ADB!18189'
        elif stockCode[-2:] == ".T":
            dict['onedriveFolderId'] = '5A0F35AAEC914ADB!18184'
        else:
            dict['onedriveFolderId'] = '5A0F35AAEC914ADB!18190'

    if stockCode[-2:] == "TW":
        dict['createPath'] = r'/Users/liaoyushao/PycharmProjects/stock/tw_temp.csv'
    elif stockCode[-2:] == ".T":
        dict['createPath'] = r'/Users/liaoyushao/PycharmProjects/stock/jp_temp.csv'
    else:
        dict['createPath'] = r'/Users/liaoyushao/PycharmProjects/stock/us_temp.csv'

    return dict


def findUsStockIndexbyName(stockCodeList, target_name):
    for i in range(len(stockCodeList)):
        if stockCodeList[i] == target_name:
            return i
    return None


def getStockList():
    try:
        tw_stock_list = stockCodeService.getTwStockCode(r'csvFile/twStock_data.xls')
        jp_stock_list = stockCodeService.getJpStockCode(r'csvFile/data_e.xls')
        us_stock_list = stockCodeService.get_sp500_tickers()
    except:
        logging.info("Unexpected error when get stock code list : ", sys.exc_info()[0])
        print("Unexpected error when get stock code list :", sys.exc_info()[0])
    else:
        return tw_stock_list, jp_stock_list, us_stock_list


def getAllorUpdatebyPool(getAll):
    tw_stock_list, jp_stock_list, us_stock_list = getStockList()
    #
    begin = time.time()
    # # MultiProcessing

    pool = Pool()
    if getAll:
        print("\nStart get 1m data. \n\n")
        pool.starmap(getStockHistorybyYahooandStore2Drive,
                     [(tw_stock_list, "onedrive", "7d", None, None, "1m", False),
                      (jp_stock_list, "onedrive", "7d", None, None, "1m", False),
                      (us_stock_list, "onedrive", "7d", None, None, "1m", False)])
        ##
        print("\nStart get 2m data. \n\n")
        end = dt.datetime().today()
        days = dt.timedelta(59)
        start = str(end - days)
        end = str(end)
        pool.starmap(getStockHistorybyYahooandStore2Drive,
                     [(tw_stock_list, "onedrive", None, start, end, "2m", False),
                      (jp_stock_list, "onedrive", None, start, end, "2m", False),
                      (us_stock_list, "onedrive", None, start, end, "2m", False)])
        ##
        print("\nStart get 1h data. \n\n")
        pool.starmap(getStockHistorybyYahooandStore2Drive,
                     [(tw_stock_list, "onedrive", "2y", None, None, "1h", False),
                      (jp_stock_list, "onedrive", "2y", None, None, "1h", False),
                      (us_stock_list, "onedrive", "2y", None, None, "1h", False)])
        # ##
        # pool.starmap(getStockHistorybyYahooandStore2Drive,
        #                      [(tw_stock_list, "onedrive", "20y", None, None, "1d", True),
        #                       (jp_stock_list, "onedrive", "20y", None, None, "1d", True),
        #                       (us_stock_list, "onedrive", "20y", None, None, "1d", True)])

        # # 7 day one min  1m (要把資料貼上 )
        # # 60 day 2m （要把資料貼上）
        # # 2 year 1h (要把資料貼上)
        # # 兩年以上 需要再撈
    elif not getAll:
        pool.starmap(updateHistoryandStore2Drive,
                     [(tw_stock_list, "onedrive", "1d", None, None, "1m", False),
                      (jp_stock_list, "onedrive", "1d", None, None, "1m", False),
                      (us_stock_list, "onedrive", "1d", None, None, "1m", False)])
        ##
        end = dt.datetime().today()
        days = dt.timedelta(59)
        start = str(end - days)
        end = str(end)
        pool.starmap(updateHistoryandStore2Drive,
                     [(tw_stock_list, "onedrive", "1d", None, None, "2m", False),
                      (jp_stock_list, "onedrive", "1d", None, None, "2m", False),
                      (us_stock_list, "onedrive", "1d", None, None, "2m", False)])
        ##
        pool.starmap(updateHistoryandStore2Drive,
                     [(tw_stock_list, "onedrive", "1d", None, None, "1h", False),
                      (jp_stock_list, "onedrive", "1d", None, None, "1h", False),
                      (us_stock_list, "onedrive", "1d", None, None, "1h", False)])
        # ##
        # pool.starmap(getStockHistorybyYahooandStore2Drive,
        #                      [(tw_stock_list, "onedrive", "20y", None, None, "1d", True),
        #                       (jp_stock_list, "onedrive", "20y", None, None, "1d", True),
        #                       (us_stock_list, "onedrive", "20y", None, None, "1d", True)])

        # # 7 day one min  1m (要把資料貼上 )
        # # 60 day 2m （要把資料貼上）
        # # 2 year 1h (要把資料貼上)
        # # 兩年以上 需要再撈

    end = time.time()
    logging.info("execute time : " + str(end - begin))

    print("Store error stockCode to db....")
    store_to_mysql(noDataList)


def initInt(type):
    global tw_int
    global jp_int
    global us_int
    global load_type
    tw_int = 0
    jp_int = 0
    us_int = 0
    load_type = type


def setInt(stockCode, num):
    global tw_int
    global jp_int
    global us_int
    if stockCode[-2:] == "TW":
        tw_int = num
    elif stockCode[-2:] == ".T":
        jp_int = num
    else:
        us_int = num


def getInt():
    global tw_int
    global jp_int
    global us_int
    global load_type
    return tw_int, jp_int, us_int, load_type


def getAllorUpdate(getAll):
    # tw_stock_list, jp_stock_list, us_stock_list = getStockList()
    #
    begin = time.time()
    # # MultiProcessing

    jp_stock_list = []
    jp_stock_list.append("3462.T")
    jp_stock_list.append("6762.T")
    jp_stock_list.append("4755.T")
    jp_stock_list.append("2698.T")
    jp_stock_list.append("3197.T")
    jp_stock_list.append("2730.T")
    jp_stock_list.append("3073.T")
    jp_stock_list.append("3047.T")
    jp_stock_list.append("2914.T")
    jp_stock_list.append("8897.T")


    if getAll:
        print("\nStart get 1m data. \n\n")
        initInt("1m")
        # getStockHistorybyYahooandStore2Drive(tw_stock_list, "onedrive", "7d", None, None, "1m", False)
        getStockHistorybyYahooandStore2Drive(jp_stock_list, "onedrive", "7d", None, None, "1m", False)
        # getStockHistorybyYahooandStore2Drive(us_stock_list, "onedrive", "7d", None, None, "1m", False)

        ##

        # print("\nStart get 2m data. \n\n")
        # end = dt.date.today()
        # days = dt.timedelta(59)
        # start = str(end - days)
        # end = str(end)
        # initInt("2m")
        # getStockHistorybyYahooandStore2Drive(tw_stock_list, "onedrive", None, start, end, "2m", False)
        # getStockHistorybyYahooandStore2Drive(jp_stock_list, "onedrive", None, start, end, "2m", False)
        # getStockHistorybyYahooandStore2Drive(us_stock_list, "onedrive", None, start, end, "2m", False)
        # ##
        # print("\nStart get 1h data. \n\n")
        # initInt("1h")
        # getStockHistorybyYahooandStore2Drive(tw_stock_list, "onedrive", "2y", None, None, "1h", False)
        # getStockHistorybyYahooandStore2Drive(jp_stock_list, "onedrive", "2y", None, None, "1h", False)
        # getStockHistorybyYahooandStore2Drive(us_stock_list, "onedrive", "2y", None, None, "1h", False)
        #
        # print("Store error stockCode to db....")
        # store_to_mysql(noDataList)

        # ##
        # pool.starmap(getStockHistorybyYahooandStore2Drive,
        #                      [(tw_stock_list, "onedrive", "20y", None, None, "1d", True),
        #                       (jp_stock_list, "onedrive", "20y", None, None, "1d", True),
        #                       (us_stock_list, "onedrive", "20y", None, None, "1d", True)])

        # # 7 day one min  1m (要把資料貼上 )
        # # 60 day 2m （要把資料貼上）
        # # 2 year 1h (要把資料貼上)
        # # 兩年以上 需要再撈
    # elif not getAll:
    #     initInt("1m")
    #     updateHistoryandStore2Drive(tw_stock_list, "onedrive", "1d", None, None, "1m", False)
    #     updateHistoryandStore2Drive(jp_stock_list, "onedrive", "1d", None, None, "1m", False)
    #     updateHistoryandStore2Drive(us_stock_list, "onedrive", "1d", None, None, "1m", False)
    #     ##
    #     end = dt.date.today()
    #     days = dt.timedelta(59)
    #     start = str(end - days)
    #     end = str(end)
    #     initInt("2m")
    #     updateHistoryandStore2Drive(tw_stock_list, "onedrive", "1d", None, None, "2m", False)
    #     updateHistoryandStore2Drive(jp_stock_list, "onedrive", "1d", None, None, "2m", False)
    #     updateHistoryandStore2Drive(us_stock_list, "onedrive", "1d", None, None, "2m", False)
    #     ##
    #     initInt("1h")
    #     updateHistoryandStore2Drive(tw_stock_list, "onedrive", "1d", None, None, "1h", False)
    #     updateHistoryandStore2Drive(jp_stock_list, "onedrive", "1d", None, None, "1h", False)
    #     updateHistoryandStore2Drive(us_stock_list, "onedrive", "1d", None, None, "1h", False)
    #
    #     print("Store error stockCode to db....")
    #     store_to_mysql(failUpdateDataList)
    #     # ##
    #     # pool.starmap(getStockHistorybyYahooandStore2Drive,
    #     #                      [(tw_stock_list, "onedrive", "20y", None, None, "1d", True),
    #     #                       (jp_stock_list, "onedrive", "20y", None, None, "1d", True),
    #     #                       (us_stock_list, "onedrive", "20y", None, None, "1d", True)])
    #
    #     # # 7 day one min  1m (要把資料貼上 )
    #     # # 60 day 2m （要把資料貼上）
    #     # # 2 year 1h (要把資料貼上)
    #     # # 兩年以上 需要再撈

    end = time.time()
    logging.info("execute time : " + str(end - begin))


def main():
    getAll = True
    upDate = False
    getAllorUpdate(getAll)  # get history all data by 1m, 2m, 1hr, 1day
    #getAllorUpdate(getAll)


def mainn():
    # jp stock     5A0F35AAEC914ADB!18178
    # tw stock     5A0F35AAEC914ADB!18179
    # us stock     5A0F35AAEC914ADB!18180
    # print( oneDrive_API.getrootAllFileID(serviceorclient))
    # print(oneDrive_API.getFileIdBy(serviceorclient, '5A0F35AAEC914ADB!18186'))
    us_stock_list = stockCodeService.get_sp500_tickers()
    jp_stock_list = stockCodeService.getJpStockCode(r'csvFile/data_e.xls')
    tw_stock_list = stockCodeService.getTwStockCode(r'csvFile/twStock_data.xls')

    do = True
    if do:
        # print(findUsStockIndexbyName(tw_stock_list, "1906.TW"))
        originalDataId = getOriginalDataId('5A0F35AAEC914ADB!18186', '1906.csv')
        oneDrive_API.downloadFile(serviceorclient, originalDataId, './original_Data.csv')

if __name__ == '__main__':
    main()
