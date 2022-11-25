import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dateutil.relativedelta import *
import openpyxl
class short_leg:
    def __init__(self,barrier,leverage,strike):
        self.strike = strike
        self.barrier = barrier
        self.leverage = leverage
        def payoff(self,perf):
            return self.leverage*(perf<=self.barrier)*max(self.strike-perf,0)
class long_leg:  ##retenir le max pour one star
    def __init__(self,df,memory_effect,basket_type):
        self.df = df
        self.mem = memory_effect ## bool
        self.b_type = basket_type
    def payoff(self, stock_values,end_date): #contains : nb de barrieres +1 obs (de S0 a ST), stock values est undf
        coupon = 0
        ac_coupon = 0
        if self.b_type== 'Worst-of':
            stock_values = pd.DataFrame((stock_values.divide(stock_values.iloc[0]))[1:].min(axis=1),columns=['Values'])
        elif self.b_type=='Best-of':
            stock_values = pd.DataFrame((stock_values.divide(stock_values.iloc[0]))[1:].max(axis=1),columns=['Values'])
        elif self.b_type =="Equally-weighted":
            stock_values = pd.DataFrame((stock_values.divide(stock_values.iloc[0]))[1:].mean(axis=1),columns=['Values'])
        min_dates=min(len(stock_values.index),len(self.df.index))
        if (len(stock_values.index)==len(self.df.copy().index)):
            argmin_dates=0
        else:
            argmin_dates=1
        self.df=self.df.iloc[:min_dates,:]
        first_ac = (stock_values["Values"].reset_index(drop=True)>(self.df["Autocall Barrier"].reset_index(drop=True))).to_numpy().nonzero()[0]
        if len(first_ac)==0 and argmin_dates==1: #toujours en vie et matu < today
            ac_coupon="alive"
            first_ac="alive"
            return ac_coupon,first_ac
        elif len(first_ac)==0 and argmin_dates==0: #matu < today et pas d'ac
            ac_coupon=0
            first_ac=[999]
            last_coupon_barrier = len(self.df.index)
        elif len(first_ac)!=0:
            ac_coupon=self.df["Autocall Coupon"][first_ac[0]]
            last_coupon_barrier = first_ac[0]
        if not self.mem:
            coupon = (((stock_values["Values"].reset_index(drop=True)>(self.df["Coupon Barrier"].reset_index(drop=True)))[:last_coupon_barrier+1])).sum()
        elif self.mem:
            last_c_b_breach = (stock_values["Values"].reset_index(drop=True)>(self.df["Coupon Barrier"].reset_index(drop=True)))[last_coupon_barrier+1].to_numpy().nonzero()[0]
            if len(last_c_b_breach)!=0:
                last_c_b_breach = last_c_b_breach[-1]
                coupon = ((stock_values["Values"][last_c_b_breach]>self.df["Coupon Barrier"][last_c_b_breach])*self.df["Coupon"][:last_c_b_breach+1]).sum()
        return (coupon+ac_coupon),first_ac
def backtest_single(df,stock_values,memory,basket_type,end_date,pdi_barrier,pdi_leverage,pdi_strike):
    ac = long_leg(df,memory,basket_type)
    ac_result = ac.payoff(stock_values,end_date) ## contient T+1
    coupon = ac.result[0]
    pdi_result = 0
    if ac_result[1][0] == [999]:
        pdi = short_leg(pdi_barrier,pdi_leverage,pdi_strike)
        if basket_type == "Worst-of":
            perf = (stock_values.iloc[-1,:].divide(stock_values.iloc[0])).min()
        if basket_type == "Best-of":
            perf = (stock_values.iloc[-1,:].divide(stock_values.iloc[0])).max()
        if basket_type == "Equally-Weighted":
            perf = (stock_values.iloc[-1,:].divide(stock_values.iloc[0])).mean()
        pdi_result = pdi.payoff(perf)
    return "alive" if coupon == "alive" else 1+coupon-pdi_result

def nearest_neighbors_sorted(x,y): #function used to offset the dates by a certain amount of months and take the nearest in the available dates
    x,y = map(np.asarray,(x,y))
    y_idx = np.argsort(y)
    len_y = len(y.copy())
    y=y[y_idx]
    nearest_neighbor =  np.empty((len(x),),dtype = np.intp)
    for j,xj in enumerate(x):
        idx = np.searchsorted(y,xj)
        if idx == len(y) or idx !=0 and y[idx]-xj<xj-y[y_idx-1]:
            idx-=1
        if idx == len(y)-1:
            nearest_neighbor[j] = len_y-1
        else:
            nearest_neighbor[j]=y[y_idx]
        y = np.delete(y,idx)
        y_idx = np.delete(y_idx,idx)
    return nearest_neighbor

def backtest_global (df_param,freq,tickers,maturity,start_date,end_date,memory,basket_type,pdi_barrier,pdi_leverage,pdi_strike):
    global_stocks = orochi.blp.bdh(tickers,px last,start_date,end_date).dropna(how="any",axis=0)
    global_stocks.index = pd.to_datetime(global_stocks.index)
    start_date = global_stocks.index[0]
    end_date = global_stocks.index[-1]
    nb_obs = int(maturity/freq)
    global L
    L=[]
    i=0
    coupon_dates  =pd.to_datetime(np.array([start_date+i*relativedelta(months=1*freq) for i in range(len(df_param.index)+1)]))
    coupon_dates =  global_stocks.index[nearest_neighbors_sorted(np.array(coupon_dates),global_stocks.index)]
    sample_data = global_stocks[global_stocks.index.isin(coupon_dates)].iloc[:nb_obs+1]
    while True:
        i+=1
        result = backtest_single(df = df_param,
                                 stock_values=sample_data,
                                 memory=memory,
                                 end_date=end_date,
                                 basket_type=basket_type,
                                 pdi_barrier=pdi_barrier,
                                 pdi_leverage=pdi_leverage,
                                 pdi_strike=pdi_strike)
        if result != "alive":
            L.append([result,start_date])
            start_date = global_stocks.index[i]
            coupon_dates = pd.to_datetime(np.array([start_date+i*relativedelta(months=1*feq) for i in range(len(df_param.index)+1)]))
            coupon_dates=global_stocks.index[nearest_neighbors_sorted(np.array(coupon_dates),global_stocks.index)]
        if coupon_dates[1]==end_date:
            break
        sample_data = global_stocks[global_stocks.index.isin(coupon_dates)].iloc[:nb_obs+1]
    plt.scatter([x[1] for x in L],[x[0] for x in L])
    return L


