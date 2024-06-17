import math 
import pandas as pd
import numpy as np 
import yfinance as yf 
import datetime as dt 
import talib
from pandas_datareader import data as pdr 
from tkinter import Tk
from tkinter.filedialog import askopenfilename 
import os 
# remember to convert csv into pd dataframe first 

csvfilename1 = "3B_Total.csv"
csvfilename2 ="20B_HKEX.csv"

# Read the CSV files into pandas dataframes
df1 = pd.read_csv(csvfilename1)
df2 = pd.read_csv(csvfilename2)

# Concatenate the dataframes
stocklist = pd.concat([df1, df2])

yf.pdr_override()
start=dt.datetime.now()-dt.timedelta(days=200)
now = dt.datetime.now()

def get_suffix(stock_symbol):
    if '=' in stock_symbol:
        parts= stock_symbol.split('=')
        return parts[-1]
    
    elif '.' in stock_symbol:
        parts = stock_symbol.split('.')
        return parts[-1]
    
    return None

def enough_amount(data, i, stock_symbol):
    amount = data['Volume'].iloc[-i] * data['Close'].iloc[-i]
    suffix = get_suffix(stock_symbol)

    threshold = 1e7 # this local varaible is necessary to be here otherwise -> UnboundLocalError: local variable 'threshold' referenced before assignment -> or you can define as global outside
    if suffix == 'T':
        threshold = 1.4e9
    
    elif suffix == 'L':
        threshold = 7.8e6
        
    elif suffix == 'T0':
        threshold = 1.34e7
    
    elif suffix == 'SI':
        threshold = 1.34e7

    elif suffix ==  'HK':
        threshold = 1.25e6

    elif suffix == 'X' or suffix == 'F' :
        threshold = 0
   
    if amount > threshold:
        return True 
    
    else :
        return False 
    

def calculate_ma_slope(data, ma_window, bar_number):
    ma = data.rolling(ma_window).mean()
    ma_slope = (ma[-1]- ma[-bar_number])/ (bar_number-1) # y2-y1/x2-x1
    return ma, ma_slope

def calculate_hma(data, period): # Hull Moving average
    wma_right_half_period = data.rolling(window = int (period/2)).mean()*2
    wma_full_period = data.rolling(window = period).mean()
    raw_hma= wma_right_half_period - wma_full_period
    return raw_hma.rolling(window = int(np.sqrt(period))).mean() # smooth the raw HMA with another WMA, this one with the square root of the specified number of periods.

'''detect a peak-trough-peak pattern within a given price series, ensuring the trough is 3 days aways from the beginning, ie: using HMA3 
Parameters:
- data: Pandas dataframe with HMA 
- begin, end: Indices to define search window, with a positive direction from the end of the series
- peak allowance: the allowed deviation percentage from the left peak and the right peak 
- peak_trough_ratio: Minimum ratio of trough to left peak 
Returns:
- Tuple (bool, int or None): Presence of pattern, and index of the left peak (or None if not found)'''
def peak_trough_peak_hma(data, begin, end, peak_allowance, peak_trough_ratio): # stage 2 analysis
    data['HMA3'] = calculate_hma(data['Close'], 3)  
    if end <= begin :    #begin has to be lower than the end for the trough
        return False, None
    right_peak = data['HMA3'].iloc[-begin]              # begin is the more recent index such that we loop from begin to end (right to left ) -> right peak here is the RHS
    for i in range (begin+3, end):
        left_peak = data['HMA3'].iloc[-i]               # at least 3 days fromt the RHS 
        for j in range (i-1, begin+3,-1):
            trough = data['HMA3'].iloc[-j]
            if (1-peak_allowance)*left_peak <= right_peak <= (1+peak_allowance)*left_peak and peak_trough_ratio <= left_peak/ trough :            #deeper trough better -> stronger momentum when break out 
                return True, -i # for consistency
    return False, None


cupAndHandle=[]
for i in range (len(stocklist)):
    stock = str(stocklist.iloc[i]['Symbol'])
    print(f"processing stock {i+1}/{len(stocklist)}:{stock}")
    try:
        df=yf.download(stock, start, now) # returning a data frame but need to specify to column so as to be useful
    
    except Exception as e:
        print (f"Error processing {stock}: {e}")
        continue
    if len(df) < 110 :
        print (f"not enough data for {stock}, skip it ")
        continue 
    if not enough_amount(df,2 , stock):
        print (f"turnover too low for {stock}, skip it")
        continue 

    ma60, ma60_slope = calculate_ma_slope(df['Close'], 60, 3)
    if ma60_slope < 0:
        print (f"downward trend for {stock}, skip")
        continue # to check whehether the stock with cup and handle is in the upward trend -> CNH with upward trend is better : 1. the trend is your fd 2. to avoid 蟹貨
    # finding stock with the handle 

    ptp1, ptp_index1 = peak_trough_peak_hma(data=df, begin=2, end=15, peak_allowance= 0.01, peak_trough_ratio=1.05 )
    if not ptp1:
        continue 
    else:
        print(f"inner rim index@ {ptp_index1}; handle length = {ptp_index1 -2}")

    # find stock with cup after handle
    ptp2, ptp_index2 = peak_trough_peak_hma(data=df, begin= ptp_index1, end=100, peak_allowance=0.01, peak_trough_ratio=1.3)
    if ptp2:
        print (f"outer rim index at {ptp_index2}; cup width {ptp_index2 - ptp_index1} ")
        cupAndHandle.append(stock)
        print (f"cup and handle pattern detected at {ptp_index2} for {stock} ")
    else:
    #optional
        print (f"handle found at {ptp_index1}, but no cup found for {stock}")

    print("n\ Cup and handle _HMA")
    for stock in cupAndHandle:
        print (stock)

# together using with ATR line and hunt by the eyes to judge the entry and exist point 

    


    
    





    
    
    

    


