from typing import Callable
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import *
from selenium.webdriver.support.expected_conditions import *
from webdriver_manager.core.manager import *
from selenium.webdriver.common.service import *
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import random

def try_find_element(driver: WebDriver, by=By.ID, value: Optional[str] = None) -> WebElement:
    try:
        result = driver.find_element(by, value)
    except NoSuchElementException as e:
        result = None
    return result

def chk_element_not_found(by=By.ID, value: Optional[str] = None) -> Callable[[Any], bool]:

    def _predicate(driver):
        if try_find_element(driver, by, value):
            return False
        return True

    return _predicate

def chk_element_found(by=By.ID, value: Optional[str] = None) -> Callable[[Any], bool]:

    def _predicate(driver):
        if try_find_element(driver, by, value):
            return True
        return False

    return _predicate

def try_click(element: WebElement) -> Callable[[Any], bool]:

    def _predicate(driver):
        try:
            element.click()
            return True
        except Exception as e:
            return False
    
    return _predicate

class DrvTypes:
    DT_CHROME: str = 'Chrome'
    DT_UNDETECTEDCHROME: str = 'UChrome'

class XPilot:

    X_HOME: str = 'https://x.com/'

    def __init__(self, driver_type: str = DrvTypes.DT_UNDETECTEDCHROME, headless: bool = True, login: str = None, password: str = None, secure_seed: str = None, sandbox: bool = True, max_random_delays: int = 30, proxies: list[str] = None):

        def is_value_among_constants(value: str, my_class, case_insensitive: bool = False):
            class_attributes = [attr for attr in dir(my_class) if isinstance(getattr(my_class, attr), str)]
            if case_insensitive:
                return value.lower().strip() in [getattr(my_class, attr).lower() for attr in class_attributes]
            else:
                return value in [getattr(my_class, attr) for attr in class_attributes]

        self.__login = login
        self.__password = password
        self.__secure_seed = secure_seed   
        self.__random_delays: int = max_random_delays
        if self.__random_delays < 0:
            self.__random_delays = 0
        self.__proxies: list[str] = proxies
        self.__last_proxy_index: int = -1
        self.__headless: bool = headless
        self.__sandbox: bool = sandbox
        if not is_value_among_constants(driver_type, DrvTypes):
            raise Exception("Wrong driver type name.")        
        self.__logged: bool = False
        self.__last_error: str = None
        self.__driver_type: str = driver_type
        self.__browser = None
        if not self.__create_browser():
            raise Exception(self.__last_error)        

    def __create_browser(self):
        try:
            if self.__browser:
                self.__close_and_quit()
                del(self.__browser)
                self.__browser = None
            proxy: str = self.__get_proxy()
            self.__logged = False
            from selenium.webdriver import ChromeOptions
            options = ChromeOptions()
            options.add_argument("--disable-notifications")
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
            options.add_argument(f'user-agent={user_agent}')
            if self.__driver_type == DrvTypes.DT_CHROME:
                from selenium.webdriver import Chrome
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                self.__web_driver = Chrome
                self.__driver_manager = ChromeDriverManager
                self.__service = Service
                prefs = {
                            "profile.default_content_setting_values.notifications" : 2,
                            "credentials_enable_service": False,
                            "password_manager_enabled": False
                        }
                options.add_experimental_option("prefs", prefs)
                if proxy:
                    options.add_argument(f'--proxy-server={proxy}')
                if self.__headless:
                    options.add_argument("--no-sandbox")
                    options.add_argument("--headless")
                    options.add_argument("--disable-gpu")
                else:
                    if not self.__sandbox:
                        options.add_argument("--no-sandbox")
                options.add_argument('--disable-dev-shm-usage')
                self.__driver = self.__driver_manager().install()
                self.__browser = self.__web_driver(service=self.__service(self.__driver), options=options, use_subprocess=False)
            elif self.__driver_type == DrvTypes.DT_UNDETECTEDCHROME:
                import undetected_chromedriver as uc
                self.__web_driver = uc
                self.__driver_manager = None
                self.__service = None
                self.__driver = None
                self.__browser = self.__web_driver.Chrome(headless=self.__headless, use_subprocess=False, options=options)
            self.__wait = WebDriverWait(self.__browser, 10)
            self.__browser.implicitly_wait(30)
            self.__browser.get(self.X_HOME)
            cookies_btn = try_find_element(self.__browser, By.XPATH, '//div[@data-testid="BottomBar"]')
            if cookies_btn:
                try:
                    cookies_btn = cookies_btn.find_elements(By.TAG_NAME, 'span')[5]
                except Exception as e:
                    cookies_btn = None
            if cookies_btn:
                self.__rnd_wait()
                cookies_btn.click()
            login_btn = try_find_element(self.__browser, By.XPATH, '//a[@data-testid="loginButton"]')
            if not login_btn:
                self.__logged = True
            self.__currenturl = self.X_HOME
            return True
        except Exception as e:
            self.__last_error = str(e)
            return False

    def __del__(self):
        self.__close_and_quit()

    def __close_and_quit(self):
        self.Close()
        try:
            if self.__browser:
                self.__browser.quit()
        except Exception as e:
            ...

    def Close(self):
        try:
            if self.__browser:
                if self.__browser.window_handles: 
                    if len(self.__browser.window_handles) < 1:
                        return
                    for window_handle in self.__browser.window_handles[:]:
                        self.__browser.switch_to.window(window_handle)
                        self.__browser.close()
                else:
                    self.__browser.close()
        except Exception as e:
            ...

    def __safe_send_keys(self, element: WebElement, text: str):
        sleep(random.uniform(0.2,0.5))
        for character in text:
            actions = ActionChains(self.__browser)
            actions.move_to_element(element)
            actions.click()
            actions.send_keys(character)
            actions.perform()
            sleep(random.uniform(0.2,0.5))

    def Login(self, login: str = None, password: str = None, secure_seed: str = None):
        try:
            if not login:
                login = self.__login
            if not password:
                password = self.__password
            if not (login and password):
                return None
            if not secure_seed:
                secure_seed = self.__secure_seed
            if self.__logged:
                if not self.Logout():
                    self.__last_error = str(self.__last_error + " *** Logout failed ***").strip()
                    return None
            if self.__proxies and len(self.__proxies):
                if not self.__create_browser():
                    self.__last_error = str(self.__last_error + " *** Logout failed ***").strip()
                    return None
            self.__browser.get(self.X_HOME)
            self.__rnd_wait()
            cookies_btn = try_find_element(self.__browser, By.XPATH, '//div[@data-testid="BottomBar"]')
            if cookies_btn:
                try:
                    cookies_btn = cookies_btn.find_elements(By.TAG_NAME, 'span')[5]
                except Exception as e:
                    cookies_btn = None
            if cookies_btn:
                cookies_btn.click()
                self.__rnd_wait()
            login_btn = try_find_element(self.__browser, By.XPATH, '//a[@data-testid="loginButton"]')
            self.__wait.until(try_click(login_btn))
            self.__rnd_wait()
            login_input = try_find_element(self.__browser, By.NAME, 'text')
            input_act_container = login_input.find_element(By.XPATH, "./..").find_element(By.XPATH, "./..").find_element(By.XPATH, "./..").find_element(By.XPATH, "./..")
            input_act_container.click()
            sleep(random.uniform(1,3))
            login_input = input_act_container.find_element(By.TAG_NAME, "input")
            self.__safe_send_keys(login_input, login)
            sleep(random.uniform(0.5,3))        
            login_input.send_keys(Keys.RETURN)
            self.__rnd_wait()
            password_input = try_find_element(self.__browser, By.NAME, 'password')
            input_act_container = password_input.find_element(By.XPATH, "./..").find_element(By.XPATH, "./..").find_element(By.XPATH, "./..").find_element(By.XPATH, "./..")
            input_act_container.click()
            sleep(random.uniform(1,3))
            password_input = input_act_container.find_element(By.NAME, "password")
            self.__safe_send_keys(password_input, password)
            sleep(random.uniform(0.5,3))        
            current_url = self.__browser.current_url
            password_input.send_keys(Keys.RETURN)
            try:
                self.__wait.until(EC.url_changes(current_url))
            except Exception as e:
                ...
            sleep(5)        
            current_url = self.__browser.current_url
            close_btn = try_find_element(self.__browser, By.XPATH, '//div[@data-testid="app-bar-close"]')
            if close_btn:
                self.__rnd_wait()
                close_btn.click()
            if 'home' in current_url:
                self.__logged = True
                return self
            else:
                return None
        except Exception as e:
            self.__last_error = str(e)
            return None
        finally:
            self.__currenturl = self.__browser.current_url

    def Logout(self):

        def url_until_last_slash(url):
            idx = url.rfind('/')
            if idx != -1:
                return url[:idx]
            else:
                return url

        try:
            if self.__logged:
                logout_url = url_until_last_slash(self.__currenturl) + '/logout'
                self.__browser.get(logout_url)
                self.__rnd_wait()
                logout_btn = try_find_element(self.__browser, By.XPATH, '//div[@data-testid="confirmationSheetConfirm"]')
                if logout_btn:
                    logout_btn.click()
                    try:
                        self.__wait.until(EC.url_changes(self.__currenturl))
                    except Exception as e:
                        ...
                    self.__logged = False
                    return self
                else:
                    return None
            return self
        except Exception as e:
            self.__last_error = str(e)
            return None
        finally:
            self.__currenturl = self.__browser.current_url

    def GetCurrentAccountName(self, include_at_sign: bool = False) -> str:
        try:
            if self.__require_logged():
                account_btn = try_find_element(self.__browser, By.XPATH, '//div[@data-testid="SideNav_AccountSwitcher_Button"]')
                if account_btn:
                    account_label = account_btn.find_elements(By.TAG_NAME, "span")[4]
                    if account_label:
                        result = account_label.text
                        if not include_at_sign:
                            result = result[1:]
                        if result.strip():
                            return result
            return None
        except Exception as e:
            self.__last_error = str(e)
            return None

    def __get_scroll_height(self):
        new_height = self.__browser.execute_script("return document.body.scrollHeight")
        return new_height
        
    def __scroll_down(self, n) -> bool:
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        try:
            html_element = self.__browser.find_element(By.TAG_NAME, 'html')
            actions = ActionChains(self.__browser)
            for i in range(n):
                actions.move_to_element(html_element).send_keys(Keys.PAGE_DOWN).perform()
                self.__rnd_wait()
            return True            
        except Exception as e:
            self.__last_error = str(e)
            return False
        
    def __scroll_up(self, n) -> bool:
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        try:
            html_element = self.__browser.find_element(By.TAG_NAME, 'html')
            actions = ActionChains(self.__browser)
            for i in range(n):
                actions.move_to_element(html_element).send_keys(Keys.PAGE_UP).perform()
                self.__rnd_wait()
            return True            
        except Exception as e:
            self.__last_error = str(e)
            return False

    def __require_logged(self) -> bool:
        try:
            if not self.__logged:
                raise Exception("User not logged in.") 
            return True
        except Exception as e:
            self.__last_error = str(e)
            return False

    def __rnd_wait(self, min: int = 5):
        if self.__random_delays:
            d = self.__random_delays
            if d <= min:
                min = 1
            timewait = float(random.randint(min, d))
            sleep(timewait)

    def __get_proxy(self) -> str:
        if self.__proxies and len(self.__proxies):
            self.__last_proxy_index = self.__last_proxy_index + 1
            if self.__last_proxy_index >= len(self.__proxies):
                self.__last_proxy_index = 0
            return self.__proxies[self.__last_proxy_index]
        else:
            return None

    def GetCurrentURL(self) -> str:
        return self.__currenturl
    
    def GetIsLoggedIn(self) -> bool:
        return self.__logged
    
    def GetLastError(self) -> str:
        return self.__last_error
    