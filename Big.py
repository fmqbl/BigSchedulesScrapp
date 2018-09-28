import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import time
import pdb
import logging
import traceback
import os
from openpyxl import load_workbook


class bigs:

    def __init__(self):
        # logging settings
        # create logger
        self.logger = logging.getLogger('Biglogg')
        self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.logger.propagate = False

        # application settings
        self.url = "https://www.bigschedules.com"
        self.cookieBtnClass = "//*[@class='csck-btn csck-btn-solid']"
        self.carrierOpt = "//div[@class='row route-switch-carrier ng-scope']"
        self.searchBtn = "//a[@class='searchAction']"
        # self.carriers = ["//label/input[contains(..,'APL')]","//label/input[contains(..,'COSCO SHIPPING Lines')]","//label/input[contains(..,'Hyundai')]","//label/input[contains(..,'Maersk')]"]
        self.orignTxtbox = "targetOriginal"
        self.destinationTxtbox = "targetDestination"
        self.columns = ['Transit Time', 'Carrier', 'CY Cutoff', 'Departure', 'Arrival', 'Service/Vessel']

        # input settings
        self.inputFile = "Data.xlsx"
        self.inputs = pd.read_excel(self.inputFile)
        self.origins = self.inputs.Origins.dropna()
        print(self.origins)

        self.destinations = self.inputs.Destinations.dropna()
        print(self.destinations)
        self.carriers = self.inputs.Carriers.dropna()
        self.listOfCarriers = ["//label/input[contains(..,'" + i + "')]" for i in self.carriers]
        print(self.listOfCarriers)
        # self.destinations = self.destinations.dropna()

    def setupChrome(self):

        # Contains all chrome settings
        self.logger.info("Setting-up Chrome")
        self.settings = webdriver.ChromeOptions()
        #self.settings.add_argument("--incognito")
        self.settings.add_argument('--ignore-ssl-errors')
        self.settings.add_argument('--ignore-certificate-errors')
        self.settings.add_argument('–-disable-web-security')
        self.settings.add_argument('–-allow-running-insecure-content')

    def loadBrowser(self):
        self.setupChrome()

        try:
            #self.browser = webdriver.Chrome("C:\\Users\\lhe-faisalm\\DataScrapping\\BigSchedules\\chromedriver.exe")
            self.browser = webdriver.Chrome(chrome_options=self.settings,
                                            executable_path="D:\\chromedriver.exe")
            self.browser.maximize_window()

        except Exception as e:
            self.logger.critical("Unable to load chrome driver. " + str(e))
        self.browser.get(self.url)

    def waitForCookieLoading(self, max_wait=5):
        self.logger.info("Accepting cookies")

        def checkCookieBtn(a):
            try:
                button = self.browser.find_element_by_xpath(self.cookieBtnClass)
                return button
            except Exception as e:
                self.logger.error("Unable to accept cookies" + str(e))
                return False

        try:
            cookieBtn = WebDriverWait(self.browser, max_wait).until(checkCookieBtn)
            cookieBtn.click()
            self.logger.info("Cookies set")
            return True
        except TimeoutException as e:
            self.logger.error("Unable to set cookies")
            return False

    def checkInputFields(self):

        try:
            origin_Textbox = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, 'targetOriginal')))
            dest_Textbox = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, 'targetDestination')))
            self.logger.info("Loaded input fields")
            return True

        except TimeoutException:
            self.logger.error("Unable to load input fields")
            return False

    def setupPage(self):

        self.setupChrome()
        self.loadBrowser()

        if self.waitForCookieLoading() and self.checkInputFields():
            self.logger.info("Brower ready to use")
            return self.browser
        else:
            self.logger.error("Unable to load browser")
            return False


    #Finding Next pages

    #def nextPageExists(self):

    def nextPageExists(self):
        #pdb.set_trace()
        # self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("====Checkig next pages")

        pagination = self.browser.find_element_by_xpath("//ul[@class='pagination']")

        try:
            next = pagination.find_element_by_xpath("//li[contains(@class,'ng-scope disabled') and contains(@title,'Next Page')]")
            print("No Next PAge")
            is_clicable = False
            return is_clicable
        except NoSuchElementException:
            print("Page Available")
            is_clicable = True
            return is_clicable


    def getData(self):
        time.sleep(40)

       #pdb.set_trace()
        #gettingPAges

        #pdb.set_trace()
        try:
            pagination = self.browser.find_element_by_xpath("//ul[@class='pagination']")
            self.pages = pagination.find_elements_by_tag_name("li")
            #print(len(self.pages))
            listofLi = pagination.find_elements_by_tag_name("li")
            next = listofLi[-2]
            link = next.find_element_by_tag_name("a")
            newdf = pd.DataFrame()
            #link.click()

        except NoSuchElementException:
            self.logger.debug("No pagination links found for " + self.origin + " ---> " + self.destination)
            return

        while (True):

            all_shipments_dataframe = []
            td_list = []
            html_list = self.browser.find_element_by_xpath("//ul[@class='list-group list-result']")

            all_li = html_list.find_elements_by_tag_name("li")

            all_li = all_li[1:]
            all_li = all_li[:-len(self.pages) or None]

            for each_li in all_li:
                try:
                    table = each_li.find_element_by_tag_name("table")
                    table_trs = table.find_elements_by_tag_name("tr")
                    for each_tr in table_trs:
                        td_list = []
                        tr_tds = each_tr.find_elements_by_tag_name("td")
                        for td in tr_tds:
                            td_list.append(td.text)
                        all_shipments_dataframe.append(td_list)

                    empty_list = ['', '', '', '', '', '']
                    all_shipments_dataframe.append(empty_list)
                except Exception as e:
                    self.logger.critical("Unable to fetch table data" + str(e))
                    break
            try:

                df = pd.DataFrame(all_shipments_dataframe, columns=self.columns)
                print("====Data gathered")
            #                 print df

            except Exception as e:
                self.logger.critical("Unable to save data:" + str(e))

            if self.nextPageExists():
                #pdb.set_trace()
                #print(df)
                #print(newdf)
                resultDf = newdf.append(df)
                #print(resultDf)
                newdf = resultDf
                print("===Clinking next")
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                link.click()

                time.sleep(2)
            else:
                filename = self.origin + "To" + self.destination + ".xlsx"
                resultDf = newdf.append(df)
                newdf = resultDf
                newdf.to_excel("Data/" + filename, sheet_name='AllShipments')
                self.pages = []
                print("===Exiting")
                #print df
                break

    def sendInputsToPage(self, firstCall=True):

        if firstCall == False:
            self.logger.info("Entering new Origin & Destination")
            originTextBoxId = "login_routes_input_origin"
            destinationTextBoxId = "login_routes_input_destination"
        else:
            self.logger.info("Started fetching data")
            originTextBoxId = self.orignTxtbox
            destinationTextBoxId = self.destinationTxtbox

        try:
            origin = browser.find_element_by_id(originTextBoxId)
            origin.clear()
            origin.send_keys(self.origin)
            time.sleep(2)
            origin.send_keys(Keys.RETURN)
            time.sleep(2)

            self.logger.info("Origin added: " + str(self.origin))

            destination = browser.find_element_by_id(destinationTextBoxId)
            destination.clear()
            destination.send_keys(self.destination)
            time.sleep(2)
            destination.send_keys(Keys.RETURN)
            time.sleep(2)
            self.logger.info("Destination added: " + str(self.destination))
        except Exception as e:
            self.logger.critical("Unable to send input keys:" + str((e)))

        try:
            if firstCall:
                browser.find_element_by_xpath(self.carrierOpt).click()
                time.sleep(1)
                self.logger.info("Checking Carriers")
                self.browser.find_element_by_xpath("//label/input[contains(..,'All')]").click()

                for carrier in self.listOfCarriers:
                    browser.find_element_by_xpath(carrier).click()

            self.browser.find_element_by_xpath(self.searchBtn).click()  # clcik search
            time.sleep(4)
        except Exception as e:
            self.logger.critical("Unable to choose carriers:" + str(e))

    def iterateOverInputs(self):
        firstCall = True
        for o in self.origins:
            for d in self.destinations:
                time.sleep(2)
                self.origin = o
                self.destination = d
                self.logger.debug("Fetching Data " + o + " ---> " + d)

                self.sendInputsToPage(firstCall)
                self.getData()
                firstCall = False


        self.logger.info("Got Data for given Origin-Destination. Exiting Now...... !")

if __name__ == '__main__':
    obj = bigs()
    browser = obj.setupPage()
    #pdb.set_trace()
    obj.iterateOverInputs()
