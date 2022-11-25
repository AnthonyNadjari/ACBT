from pickle import FALSE
from bs4 import BeautifulSoup as bs
import pandas as pd
from flask import Flask
from flask_restful import Resource, Api
from flask_ngrok import run_with_ngrok
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import numpy as np
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pandas.tseries.offsets import BDay

opts = webdriver.FirefoxOptions()
opts.headless = True


class Prices(Resource):
    def get(self, ticker, maturity):
        global driver
        global browser_launched

        # initialize variables
        browser_launched = False
        prices_histo = []
        ticker_file = ''
        mat_file = 0
        directory = 'HistoPrices'

        # convert a date like 'Nov 12 2022' to '11/12/22'
        def convert_date(date_string):
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            date_split = date_string.split(" ")
            dd = date_split[1]
            yyyy = date_split[2]
            yy = yyyy[2:]
            mm = months.index(date_split[0]) + 1
            return str(mm) + "/" + dd + "/" + yy

        # convert a date like '11/12/22' to 'Nov 12 2022'
        def convert_date_to_string(date_string):
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            date_split = date_string.split("/")
            day = date_split[1]
            if len(date_split[2]) < 3:
                year = "20" + date_split[2]
            else:
                year = date_split[2]
            month = months[int(date_split[0]) - 1]
            return month + " " + day + " " + year

        # retrieve prices for a period from browser
        def get_prices(dfrom="default", dto="default"):
            global driver
            # launch the selenium brower we will work on
            if not browser_launched:
                launch_browser()

            # determine default dates
            date_today = driver.find_element(By.CSS_SELECTOR, '#Date2').get_attribute("value")
            date_split = date_today.split("/")
            date_from = date_split[0] + "/" + date_split[1] + "/" + str(int(date_split[2]) - maturity)
            if dfrom == "default":
                dfrom = date_from
            if dto == "default":
                dto = date_today

            # input dates into brower with selenium
            driver.find_element(By.CSS_SELECTOR, '#Date1').clear()
            driver.find_element(By.CSS_SELECTOR, '#Date1').send_keys(dfrom)
            driver.find_element(By.CSS_SELECTOR, '#Date2').clear()
            driver.find_element(By.CSS_SELECTOR, '#Date2').send_keys(dto)
            driver.find_element(By.CSS_SELECTOR, '#submit-btn').click()

            dates = []
            prices = []
            i = 1
            # get prices with beautiful soup
            while True:
                html = driver.page_source
                soup = bs(html, 'lxml')
                elements = soup.find_all('tr', {"class": "result"})
                for element in elements:
                    date = element.find_all('td')[0].text
                    price = element.find_all('td')[1].text
                    dates.append(date)
                    prices.append(price)
                try:
                    # next page
                    driver.find_element(By.CSS_SELECTOR, '#next').click()
                except NoSuchElementException:
                    break
                i += 1

            # create and return dataframe with prices for specific period
            df = pd.DataFrame.from_dict({'Date': dates, 'Price': prices})
            return df

        # if needed, we launch the Firefox driver
        def launch_browser():
            global browser_launched
            global driver
            driver = webdriver.Firefox(executable_path=r'./driver/geckodriver')
            url = "https://www.advfn.com/stock-market/"
            driver.get(url)
            wait = WebDriverWait(driver, 10)
            # Enter ticker in search bar
            driver.find_element(By.CSS_SELECTOR, '#headerQuickQuoteSearch').send_keys(ticker)
            time.sleep(1)
            # focus on search bar to have suggestions
            driver.find_element(By.CSS_SELECTOR, '#headerQuickQuoteSearch').click()
            # wait until the first element in the list is clickable
            el = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '#headerQuickQuoteSearch-menu > table > tbody > tr:nth-child(1)')))
            # the exchange is plugged into the url to retrieve quotes
            # (we use the suggestion box because we assume user might not know the exchange)
            info = driver.find_element(By.CSS_SELECTOR, 'tr.autosuggest-result').text
            exchange_split = info.split(" ")
            exchange = exchange_split[len(exchange_split) - 1]
            if exchange == "EU":
                exchange = "EURONEXT"
            url = "https://www.advfn.com/stock-market/" + exchange + "/" + ticker + "/historical/more-historical-data"
            driver.get(url)
            browser_launched = True

        # because selenium webscraping in our case takes a significant amount of time
        # we decided that the user will store prices in a txt file that he can quickly retrieve next time
        for filename in os.listdir(directory):
            # get filenames in directory (ticker and time horizon)
            filename = filename[:len(filename) - 4]
            file_split = filename.split('_')
            ticker_file = file_split[0]
            mat_file = int(file_split[1])
            # if we get a match then we extract prices
            if ticker == ticker_file:
                text_prices = np.loadtxt('HistoPrices/' + filename + '.txt', delimiter=',', dtype="str")
                # have to pass by a dataframe to have prices in float and not string...
                prices_histo = pd.DataFrame.from_dict({'Date': text_prices[:, 0], 'Price': text_prices[:, 1]})
                prices_histo.head()
                # we will delete the file because a more complete version will be stored
                os.remove("HistoPrices/" + filename + ".txt")
                break

        if len(prices_histo) < 2:
            # if there is no prior txt file
            df_to_save = df_to_use = get_prices()
        else:
            # 1) check if more recent prices need to be added to the txt prices
            if prices_histo.iloc[0, 0] != convert_date_to_string(
                    datetime.strftime(datetime.now() - BDay(1), '%m/%d/%Y')):
                # if the last time we stored AAPL prices was a month ago, then we will add the prices from this month to the list
                latest_prices = get_prices(convert_date(prices_histo.iloc[0, 0]))
                # we join the new prices with the txt prices
                frames = [latest_prices, prices_histo]
                df_to_save = df_to_use = pd.concat(frames)
            else:
                # if the txt prices are already up to date
                df_to_save = df_to_use = prices_histo

            # 2) check if older prices need to be added to the txt prices (ie if we stored 5 years of prices and need 6)
            if mat_file < maturity:
                older_prices = get_prices("default", convert_date(prices_histo.iloc[len(prices_histo) - 1, 0]))
                frames = [df_to_save, older_prices]
                df_to_save = df_to_use = pd.concat(frames)
            else:
                # if we need 2Y of prices but have 5Y stored, we will extract only 2Y
                base_date = datetime.now() - relativedelta(years=maturity)
                date_to_find = convert_date_to_string(datetime.strftime(base_date, '%m/%d/%Y'))
                date_to_find_1 = convert_date_to_string(datetime.strftime(base_date - BDay(1), '%m/%d/%Y'))
                i = len(df_to_save) - 1
                while i > 0:
                    # we search from bottom so it will take latest date the 2
                    if df_to_save.iloc[i, 0] == date_to_find or df_to_save.iloc[i, 0] == date_to_find_1:
                        df_to_use = df_to_save.head(i + 1)
                        break
                    i -= 1

        # Drop duplicates (one date will be overlapping)
        df_to_use = df_to_use.drop_duplicates()
        df_to_save = df_to_save.drop_duplicates()

        # save prices to txt file to be used in the future
        if len(prices_histo) < 2:
            mat_saved = maturity
        else:
            mat_saved = max(mat_file, maturity)
        prices = np.array(df_to_save)
        np.savetxt('HistoPrices/' + ticker + '_' + str(mat_saved) + '.txt', prices, delimiter=',', fmt="%s")

        # strip data
        for col in df_to_use.columns:
            df_to_use[col] = df_to_use[col].apply(lambda x: x.strip())
        df_to_use.head()

        # convert to json
        hist_prices = [df_to_use.iloc[i].to_json() for i in range(len(df_to_use))]

        # close browser
        if browser_launched:
            driver.close()
            driver.quit()

        return hist_prices


app = Flask("My App")
api = Api(app)
api.add_resource(Prices, '/prices/<string:ticker>/<int:maturity>')


@app.route("/")
def home():
    return "<h1>Get Prices</h1>"


if __name__ == '__main__':
    run_with_ngrok(app)
    app.run()