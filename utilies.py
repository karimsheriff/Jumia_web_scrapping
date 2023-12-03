from config import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import urllib.parse
from time import sleep
from datetime import datetime
from math import *

escaped_user = urllib.parse.quote_plus(mongo_user)
uri =  (f"mongodb+srv://{escaped_user}:{mongo_password}@{mongo_url}")
client = MongoClient(uri,server_api=ServerApi('1'))
db=client.jumia

try:
    current_path = os.path.dirname(os.path.abspath(__file__))
except:
    current_path = '.'


def init_driver(gecko_driver='', user_agent='', load_images=True, is_headless=False):
    firefox_profile = webdriver.FirefoxProfile()
    
    firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', False)
    firefox_profile.set_preference("media.volume_scale", "0.0")
    firefox_profile.set_preference("dom.webnotifications.enabled", False)
    if user_agent != '':
        firefox_profile.set_preference("general.useragent.override", user_agent)
    if not load_images:
        firefox_profile.set_preference('permissions.default.image', 2)

    options = Options()
    options.headless = is_headless

    service = Service(executable_path=f'{current_path}/{geco_driver_url}')

    
    
    driver = webdriver.Firefox(options=options,
                               service = service,)
                            
    return driver

def get_url(page_url,driver):
    driver.get(page_url)
    sleep(30)
    buttons = driver.find_elements(By.CLASS_NAME, 'cls')
    action = ActionChains(driver)
    if len(buttons) > 0:
       wait = WebDriverWait(driver, 3)  
       action.move_to_element(buttons[0]).click().perform()
    else: return True    


def get_products(driver):
    products = driver.find_elements(By.CSS_SELECTOR, 'div.-paxs .prd')
    products_info =[]
    for element in products:
        product_title = ''
        if len(element.find_elements(By.CSS_SELECTOR,'div.info h3.name')) > 0:
           product_title = element.find_elements(By.CSS_SELECTOR,'div.info h3.name')[0].text
        product_url = ''
        if len(element.find_elements(By.CSS_SELECTOR,'a.core')) > 0:
            product_url = element.find_elements(By.CSS_SELECTOR,'a.core')[0].get_attribute('href') 
        current_price = 0 
        if len(element.find_elements(By.CSS_SELECTOR,'div.info div.prc'))>0:
            current_price = element.find_elements(By.CSS_SELECTOR,'div.info div.prc')[0].text 
            current_price = ceil(float(current_price.split()[1].replace(',','')))
        old_price = 0 
        if len(element.find_elements(By.CSS_SELECTOR,'div.info div.s-prc-w div.old'))>0:
            old_price = element.find_elements(By.CSS_SELECTOR,'div.info div.s-prc-w div.old')[0].text     
            old_price = ceil(float(old_price.split()[1].replace(',','')))
        
        product_info =  {
            'product_title' : product_title,
            'product_url' : product_url , 
            'current_price' : current_price,
            'old_price' :old_price     
        }
        if db.products.count_documents( { '$or': [ {'product_title': product_title}, {'product_url':product_url} ]  } ) == 0:
             db.products.insert_one( product_info )
        else:
            pd = db.products.find_one( { '$or': [ {'product_title': product_title}, {'product_url':product_url} ]  } )
            if pd['current_price'] != current_price or pd['old_price'] != old_price:
                # update prices
                db.products.update_one( {'_id': pd['_id'] },{'$set': 
                                                             {'current_price': current_price,
                                                             'old_price': old_price,
                                                             'updated_at': datetime.now(),
                                                             'published_at': False} }  )
        products_info.append(product_info)
    return products_info


