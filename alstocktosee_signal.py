
#best
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import pytz
from datetime import datetime, timedelta
from datetime import date
import numpy as np
import ta
import asyncio
import aiohttp
import nest_asyncio
#from allstocks import symbols
from variable import s


st.set_page_config(layout="wide")
st.title('Stock Trading for signal macd stochiastic')




buystock = []
sellstock = []
interval = st.number_input(label='Time interval',min_value=5,max_value=43800,value=60)
st.write('Default value for 1 hr .. enter 15,60,240,1440,10080,43800')
dayback = st.number_input(label='Daysback',min_value=1,max_value=3000,value=100)
st.write('Enter the number of days to get data .. 100 for 1 hr interval  500 for 1 day interval')
# interval = 1440 # enter 15,60,240,1440,10080,43800
# dayback = 500 #100
ed = datetime.now()
stdate = ed - timedelta(dayback)


day_to_getdata = st.number_input(label='Daysback for macd and stochiastic',min_value=-20,max_value=0,value=-1)
st.write('Enter the number of days to get data in -1,-2 ,-3')
macd_getdata = day_to_getdata - 5
#st.write('Enter the number of days to get data in -1,-2 ,-3 ... should be less than dayback -5 ')


def conv(x):

    timestamp = int(x.timestamp() * 1000)
    timestamp_str = str(timestamp)[:-4] + '0000'
    final_timestamp = int(timestamp_str)
    return  final_timestamp

ist_timezone = pytz.timezone('Asia/Kolkata')

fromdate = conv(stdate)
todate = conv(ed)


button_clicked = st.button('Get Data')
if button_clicked:
    st.write('Getting data')

    async def getdata(session, stock):


        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            #'Accept-Encoding': 'gzip, deflate, br'
        }
        url = f'https://groww.in/v1/api/charting_service/v2/chart/exchange/NSE/segment/CASH/{stock}?endTimeInMillis={todate}&intervalInMinutes={interval}&startTimeInMillis={fromdate}'
        async with session.get(url, headers=headers) as response:
            try:
                
                resp = await response.json()
                candle = resp['candles']
                dt = pd.DataFrame(candle)
                fd = dt.rename(columns={0: 'datetime', 1: 'Open', 2: 'High', 3: 'Low', 4: 'Close', 5: 'Volume'})
                
                
                fd['symbol'] = stock
                pd.options.mode.chained_assignment = None
                final_df = fd
                

                final_df['Open'] = final_df['Open'].astype(float)
                final_df['Close'] = final_df['Close'].astype(float)
                final_df['High'] = final_df['High'].astype(float)
                final_df['Low'] = final_df['Low'].astype(float)
                final_df['Volume'] = final_df['Volume'].astype(float)
                final_df['datetime1'] = pd.to_datetime(final_df['datetime'], unit='s', utc=True)
                final_df['datetime1'] = final_df['datetime1'].dt.tz_convert(ist_timezone)
                
                

    # Format the datetime to 'dd:mm:yyyy hh:mm:ss'
                #final_df['datetime1'] = final_df['datetime1'].dt.strftime('%d:%m:%Y %H:%M:%S')

                final_df.set_index(final_df.datetime1, inplace=True)
                final_df.drop(columns=['datetime'], inplace=True)

                final_df['prevopen'] = final_df['Open'].shift(1)
                final_df['prevhigh'] = final_df['High'].shift(1)
                final_df['prevlow1'] = final_df['Low'].shift(2)
                final_df['prevhigh1'] = final_df['High'].shift(2)
                final_df['prevlow2'] = final_df['Low'].shift(3)
                final_df['prevhigh2'] = final_df['High'].shift(3)
                final_df['prevclose'] = final_df['Close'].shift(1)
                
                
            
                final_df['time_column'] = final_df.datetime1.dt.time
                
                time_string = "09:15:00"            
    #----------------------
                final_df['st'] = round(
                    ta.momentum.stoch(high=final_df['High'], low=final_df['Low'], close=final_df['Close'], window=14,
                                    smooth_window=3),
                    2)
                
                final_df['macd_ind'] = ta.trend.macd_diff(close=final_df['Close'], window_slow=26, window_fast=12,
                                                        window_sign=9,
                                                        fillna=False)
                final_df['prevmacd'] = final_df['macd_ind'].shift(1)
                final_df['ma200'] = round(ta.momentum._ema(series=final_df['Close'],periods=200))
                final_df['stbelow20'] = np.where(final_df['st'] < 20, 1, 0)
                final_df['stabove80'] = np.where(final_df['st'] > 80, 1, 0)
                final_df['macd_ind_above_zero'] = np.where(final_df['macd_ind'] > 0, 1, 0)
                final_df['macd_ind_below_zero'] = np.where(final_df['macd_ind'] < 0, 1, 0)
                dfmacdmax=final_df.macd_ind.iloc[macd_getdata:].max()
                
                dfmacdmin=final_df.macd_ind.iloc[macd_getdata:].min()
                dfstmax=final_df.stabove80.iloc[macd_getdata:].max()
                
                dfstmin=final_df.stbelow20.iloc[macd_getdata:].min()
                pd.set_option('display.max_columns', None)
                final_df['time915']= np.where((final_df.index.time == pd.to_datetime(time_string).time()),1,0)
                final_df['ma200buy'] = np.where(final_df['ma200'] < final_df['Close'], 1, 0)
                final_df['ma200sell'] = np.where(final_df['ma200'] > final_df['Close'], 1, 0)
                final_df['macdbuysignal'] = np.where((final_df['prevmacd'] < 0) & (final_df['prevmacd'] == dfmacdmin), 1, 0)
                final_df['macdsellsignal'] = np.where((final_df['prevmacd'] > 0) & (final_df['prevmacd'] == dfmacdmax), 1, 0)
                final_df['stbuysignal'] = np.where(dfstmin == 1, 1, 0)
                final_df['stsellsignal'] = np.where(dfstmax == 1, 1, 0)
                final_df['buy'] = final_df['macdbuysignal'] + final_df['stbuysignal'] + final_df['ma200buy']
                final_df['sell'] = final_df['macdsellsignal'] + final_df['stsellsignal'] + final_df['ma200sell']
                

                
                newdf = final_df.iloc[-100:]
                last_candle = newdf.iloc[day_to_getdata]
                if last_candle['buy'] == 3:
                    buystock.append(last_candle['symbol'])
                    st.title("Candlestick and MACD Chart for Buy" )
                    st.write(last_candle['symbol'])

    # Create subplots
                    fig = make_subplots(
                        rows=2, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.02,
                        row_heights=[0.7, 0.3],
                        subplot_titles=("Candlestick Chart", "MACD Histogram")
                    )

                    # Add candlestick to first row
                    fig.add_trace(
                        go.Candlestick(
                            x=newdf.index,
                            open=newdf["Open"],
                            high=newdf["High"],
                            low=newdf["Low"],
                            close=newdf["Close"],
                            name= "Candlestick"
                        ),
                        row=1, col=1
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=newdf.index,
                            y=newdf["ma200"],
                            line=dict(color="red", width=2),
                            name="MA200"
                        ),
                        row=1, col=1
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=newdf[newdf["buy"] == 3].index,
                            y=newdf[newdf["buy"] == 3]["Low"],
                            mode="markers",
                            marker=dict(symbol="triangle-up", size=20, color="green"),
                            name="Buy Signal"
                        ),
                        row=1, col=1
                    )
                    try:
                        fig.add_trace(
                            go.Scatter(
                                x=newdf[newdf["time915"] == 1].index,
                                y=newdf[newdf["time915"] == 1]["Low"],
                                mode="markers",
                                marker=dict(symbol="triangle-up", size=10, color="blue"),
                                name="day change"
                            ),
                            row=1, col=1
                        )
                    except:
                        pass

                    # Add MACD histogram to second row
                    fig.add_trace(
                        go.Bar(
                            x=newdf.index,
                            y=newdf["macd_ind"],
                            name="MACD Histogram",
                            marker_color="green"
                        ),
                        row=2, col=1)
                   
                    

                    # Update layout
                    fig.update_layout(
                        height=800,
                        title="Candlestick Chart and MACD",
                        xaxis=dict(type="category"),  # Set x-axis to category type
                        xaxis2=dict(type="category", title="Date"),
                        # X-axis for the second row
                        yaxis=dict(title="Price"),
                        yaxis2=dict(title="MACD"),
                        xaxis_rangeslider_visible = False,
                        showlegend=False
                    )
                    #fig.layout.xaxis.type = 'category'

                    # Display the plot in Streamlit
                    st.plotly_chart(fig)



                    


                    # fig = go.Figure(data=[go.Candlestick(x=newdf.index, open=newdf.Open, close=newdf.Close, high=newdf.High,low=newdf.Low,name=stock),
                    #                       go.Scatter(x=newdf.index, y=newdf.ma200, line=dict(color='red', width=2),name='ma200')
                    #                       ])
                    # fig.add_trace(
                    #     go.Scatter(x=newdf[newdf['buy']==3].index, y=newdf[newdf['buy']==3]['Low'], mode='markers', marker_symbol='triangle-up',
                    #                marker_size=25,marker_color='green',name='buy'))
                

                    # fig.update_layout(autosize=False, width=1800, height=800, xaxis_rangeslider_visible=False)
                    # fig.layout.xaxis.type = 'category'
                    
                    # st.write(' macd buy stratergy')
                    # st.plotly_chart(fig)
                
                

                

                # newdf = newdf.iloc[-100:]
            
                # newdf1 = final_df[final_df.index.time == pd.to_datetime(time_string).time()].reset_index(drop=True)
                
                # last_candle = newdf1.iloc[day_to_getdata]

                
                
                if last_candle['sell'] == 3:
                    sellstock.append(last_candle['symbol'])
                    
                    st.title("Candlestick and MACD Chart" )
                    st.write(last_candle['symbol'])

    # Create subplots
                    fig = make_subplots(
                        rows=2, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.02,
                        row_heights=[0.7, 0.3],
                        subplot_titles=("Candlestick Chart", "MACD Histogram")
                    )

                    # Add candlestick to first row
                    fig.add_trace(
                        go.Candlestick(
                            x=newdf.index,
                            open=newdf["Open"],
                            high=newdf["High"],
                            low=newdf["Low"],
                            close=newdf["Close"],
                            name= "Candlestick"
                        ),
                        row=1, col=1
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=newdf.index,
                            y=newdf["ma200"],
                            line=dict(color="red", width=2),
                            name="MA200"
                        ),
                        row=1, col=1
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=newdf[newdf["sell"] == 3].index,
                            y=newdf[newdf["sell"] == 3]["High"],
                            mode="markers",
                            marker=dict(symbol="triangle-down", size=20, color="red"),
                            name="Sell Signal"
                        ),
                        row=1, col=1
                    )

                    # Add MACD histogram to second row
                    fig.add_trace(
                        go.Bar(
                            x=newdf.index,
                            y=newdf["macd_ind"],
                            name="MACD Histogram",
                            marker_color="red"
                        ),
                        row=2, col=1
                    )
                    # Add day separators to the candlestick chart
                    
                    try:
                        fig.add_trace(
                            go.Scatter(
                                x=newdf[newdf["time915"] == 1].index,
                                y=newdf[newdf["time915"] == 1]["Low"],
                                mode="markers",
                                marker=dict(symbol="triangle-up", size=10, color="blue"),
                                name="day change"
                            ),
                            row=1, col=1
                        )
                    except:
                        pass
                    

                    # Update layout
                    fig.update_layout(
                        height=800,
                        title="Candlestick Chart and MACD",
                        xaxis=dict(type="category"),  # Set x-axis to category type
                        xaxis2=dict(type="category", title="Date"),
                        # X-axis for the second row
                        yaxis=dict(title="Price"),
                        yaxis2=dict(title="MACD"),
                        xaxis_rangeslider_visible = False,
                        showlegend=False
                    )
                    #fig.layout.xaxis.type = 'category'

                    # Display the plot in Streamlit
                    st.plotly_chart(fig)



                    

                    

                # if last_candle['rsibreakdown'] == 1:#2
                #     sellstock.append(last_candle['symbol'])
                    #st.write(last_candle['symbol'])

                    

                    # fig = go.Figure(data=[go.Candlestick(x=newdf.index, open=newdf.Open, close=newdf.Close, high=newdf.High,low=newdf.Low,name=stock),
                    #                       go.Scatter(x=newdf.index, y=newdf.ma200, line=dict(color='red', width=2),name='ma200')
                    #                       ])
                    # fig.add_trace(
                    #     go.Scatter(x=newdf[newdf['rsibreakdown']==1].index, y=newdf[newdf['rsibreakdown']==1]['High'], mode='markers', marker_symbol='triangle-down',
                    #                marker_size=25,marker_color='red'))
                

                    # fig.update_layout(autosize=False, width=1800, height=800, xaxis_rangeslider_visible=False)
                    # fig.layout.xaxis.type = 'category'
                    
                    # st.write(' rsi sell stratergy')
                    # st.plotly_chart(fig)

                # if last_candle['rsibreakup'] == 1:#3

                #     buystock.append(last_candle['symbol'])
                    # fig = go.Figure(data=[go.Candlestick(x=newdf.index, open=newdf.Open, close=newdf.Close, high=newdf.High,low=newdf.Low,name=stock),                                     
                    #                       go.Scatter(x=newdf.index, y=newdf.ma200, line=dict(color='blue', width=2),name='ma200')])
                    # fig.add_trace(
                    #     go.Scatter(x=newdf[newdf['rsibreakup']==1].index, y=newdf[newdf['rsibreakup']==1]['Low'], mode='markers', marker_symbol='triangle-up',
                    #                marker_size=25,marker_color='green'))
                    

                    # fig.update_layout(autosize=False, width=1800, height=800, xaxis_rangeslider_visible=False)
                    # fig.layout.xaxis.type = 'category'
                    
                    # st.write(' rsi buy stratergy')
                    # st.plotly_chart(fig)



                return
            except:
                print('no data')
                pass


    async def main():
        async with aiohttp.ClientSession() as session:

            tasks = []
            for stocks in s:
                try:
                    stock = stocks

                    task = asyncio.ensure_future(getdata(session, stock))

                    tasks.append(task)
                except:
                    pass
            df = await asyncio.gather(*tasks)
            # print(df)


    nest_asyncio.apply()
    asyncio.run(main())





    st.write('buy')
    st.write(pd.DataFrame(buystock))
    st.write('sell')
    st.write(pd.DataFrame(sellstock))

    #''' 1 day IRCTC GUJGASLTD BPCL TATASTEEL RBLBANK IGL DELTACORP'''

