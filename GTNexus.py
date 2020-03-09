import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging
import pdb
import shutil
import os

download_folder = "D:\ProjectGTNexus"

profile = {"plugins.always_open_pdf_externally": True, 
            "download.default_directory": download_folder,
}


class PoTracker:
    
    def __init__(self):
        
        self.logger = logging.getLogger('GT-Nexus')
        self.logger.setLevel(logging.DEBUG)
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        
        self.logger.addHandler(ch)
        self.logger.propagate = False

        #xpaths

        self.searchType = "//*[@id='row1']/td[3]/nobr/select"
        self.searhField = "//*[@id='row1']/td[5]/nobr/input"
        self.searchButton = "//*//input[@class='qstext']"
        self.tableRows = "//*[@id='ext-gen6']/table[1]/tbody/tr/td[2]/table[2]/tbody/tr[6]/td/table"
        self.tableLink = "//*[@id='ext-gen6']/table[1]/tbody/tr/td[2]/table[2]/tbody/tr[6]/td/table/tbody/tr[2]/td[31]/a"
        self.docLink = "//*[@id='ext-gen6']/table[3]/tbody/tr[7]/td/table/tbody/tr[2]/td[1]/a"
        self.poSummary = "//*[@id='layoutheaderdiv']/table/tbody/tr/td[3]/table/tbody/tr[2]/td/form/select"
       
        self.finalResult = []
        
        # application setting
        
        self.url = "https://network.gtnexus.com/en/trade/ulogin"
        
        # input settings
        self.inputFile = "D:\EliasCheckGtNexus\GTinput.xlsx"
        self.inputs = pd.read_excel(self.inputFile)
        print(self.inputs)
        
    def setupChrome(self):

        # Contains all chrome settings
        self.logger.info("Setting-up Chrome")
        self.settings = webdriver.ChromeOptions()
        #self.settings.add_argument("--incognito")
        self.settings.add_argument("--incognito")
        #self.settings.add_argument('--ignore-ssl-errors')
        #self.settings.add_argument('--ignore-certificate-errors')
        #self.settings.add_argument('–-disable-web-security')
        #self.settings.add_argument('–-allow-running-insecure-content')
        #self.settings.add_argument('--browser.download.folderList=2')
        #self.settings.add_argument('--browser.helperApps.neverAsk.saveToDisk=application/pdf,application/x-pdf')
        self.settings.add_experimental_option('prefs',profile)
            

    def wait_for_class_to_be_available(self,browser,elementXpath, total_wait=100):
        try:
            element = WebDriverWait(self.browser, total_wait).until(EC.presence_of_all_elements_located((By.XPATH, elementXpath)))
            return element
        except Exception as e:
            print("Wait Timed out")
            print(e)
            total_wait -= 1
            time.sleep(1)
            if total_wait > 1: 
                self.wait_for_class_to_be_available(self.browser,elementXpath, total_wait)


    def loadBrowser(self):
        
        #pdb.set_trace()
        self.setupChrome()

        try:
            #self.browser = webdriver.Chrome("D:\\DataScrapping\\ProjectBigSchedules\\chromedriver.exe")
            self.browser = webdriver.Chrome(chrome_options=self.settings, executable_path=r"D:\EliasCheckGtNexus\chromedriver.exe")
            self.browser.maximize_window()

        except Exception as e:
            self.logger.critical("Unable to load chrome driver. " + str(e))
        
        #Entering the URL
        
        self.browser.get(self.url)
        inputElement = self.browser.find_element_by_id("login")
        inputElement.send_keys('zohaibismail')

        passwardField = self.browser.find_element_by_id('password')
        passwardField.send_keys('eikhi121')

        submitButton = self.browser.find_element_by_id('loginButton')
        submitButton.click()

                                        
    def setupPage(self):

        self.setupChrome()
        self.loadBrowser()
                                            
    def getDataAndDownloadDocs(self,po):
        
        #pdb.set_trace()
        searchButton = self.wait_for_class_to_be_available(self.browser,self.searchButton)

        searchType = self.wait_for_class_to_be_available(self.browser,self.searchType)

        searchField = self.wait_for_class_to_be_available(self.browser,self.searhField)
        
        self.browser.find_element_by_xpath("//select[@name='searchtype']/option[text()='Orders']").click()
        self.browser.find_element_by_xpath("//select[@name='searchfieldrow1']/option[text()='Order#']").click()
        
        poField = self.browser.find_element_by_css_selector(".qstext.searchVal")
        
        poField.clear()
            
        time.sleep(1)
        poField.send_keys(po)

        searchButton[0].click()
        
        time.sleep(3)

        #summary = self.wait_for_class_to_be_available(self.browser,self.poSummary)
        #if summary:
            #self.browser.find_element_by_xpath("//select[@name='layoutId']/option[text()='PO Shipment Summary']").click()
        
        try:
            tableRows = self.browser.find_elements_by_xpath("//*[@id='ext-gen6']/table[1]/tbody/tr/td[2]/table[2]/tbody/tr[6]/td/form/table")
        except Exception as e:
            self.logger.info("Found no data for po number = " + str(po))
            return
        time.sleep(3)
        #pdb.set_trace()
        fullTableHtml = tableRows[0].get_attribute('outerHTML')
        df = pd.read_html(fullTableHtml)

        print(df[0][5])
        self.header = df[0].columns

        print(self.header)

        #df[0].to_csv(str(po) + ".csv", index=False,index_label = False)

        self.finalResult.append(df[0].iloc[1].tolist())
        
        # existance of check for view doc link
        
        try:
            tableLinks = self.browser.find_elements_by_xpath("//*[@id='ext-gen6']/table[1]/tbody/tr/td[2]/table[2]/tbody/tr[6]/td/form/table/tbody/tr[2]/td[11]/a")
        
        except Exception as e:
            self.logger.info("Found no link for viewing docs for po = " + str(po))
            return

        time.sleep(1)

        tableLinks[0].click()
        
        
        # existance of check for download doc link
        
        try:
            viewDocLink = self.browser.find_elements_by_xpath("//*[@id='ext-gen6']/table[3]/tbody/tr[7]/td/table/tbody/tr[2]/td[1]/a")
        
        except Exception as e:
            self.logger.info("Found no link for downlaoding docs for po = " + str(po))
            return

        viewDocLink[0].click()
        
        time.sleep(1)

        file_name = ''

        while file_name.lower().endswith('.pdf') is False:
            time.sleep(.25)
            try:
                file_name = max([os.path.join(download_folder,'') + f for f in os.listdir(download_folder)], key=os.path.getctime)

                print(file_name)
                newName = viewDocLink[0].text + ".pdf"
                old_file = os.path.join(download_folder, file_name)
                new_file = os.path.join(download_folder, newName)
                os.rename(old_file, new_file)

            except Exception as e:
                self.logger.info("Unable to rename the file with PO Number")
        
    def iterateOverInputs(self):
        
        for i in self.inputs['PO Number']:
            
            self.po = i
            
            time.sleep(1)
            self.getDataAndDownloadDocs(self.po)
        
        print(self.finalResult)


        data = pd.DataFrame(self.finalResult, columns=['check1','check2','Order','Dept','Department','Division','Brand','BrandDesc','ChannelDesc','Style','PrepackBulk','AgentName','BillTo','ShipTo','DestinationCountry','ExporterName','FactoryName','Status','POType','Transfer PointCountry','PlannedMode','OriginCountry','SalesTerms','FreightPaymentTerms','TransferPoint','AnticipatedShipDate','PlannedStockedDate','OrderPaymentMethod','OrderQty','GarmentType','Docs'])
        data.to_csv('final.csv', index_label=False, index=False)

if __name__ == '__main__':
    obj = PoTracker()
    obj.setupPage()
    #pdb.set_trace()c
    
    obj.iterateOverInputs()
    