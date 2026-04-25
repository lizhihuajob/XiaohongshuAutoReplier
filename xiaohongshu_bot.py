import time
import random
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class XiaohongshuBot:
    def __init__(self, headless: bool = False, wait_time: int = 10):
        self.headless = headless
        self.wait_time = wait_time
        self.driver = None
        self.is_logged_in = False
        
    def init_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.driver.implicitly_wait(5)
        
    def random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        time.sleep(random.uniform(min_sec, max_sec))
        
    def open_xiaohongshu(self):
        if not self.driver:
            self.init_driver()
        self.driver.get('https://www.xiaohongshu.com/')
        self.random_delay(2, 4)
        
    def check_login_status(self) -> bool:
        try:
            # 方法1：检查是否存在登录元素（旧方法）
            login_elements = self.driver.find_elements(
                By.XPATH, 
                "//*[contains(text(), '登录') or contains(text(), '扫码')]"
            )
            
            # 方法2：检查是否存在登录后才有的元素，如用户头像、个人中心等
            logged_in_elements = []
            
            # 尝试多种可能的登录后元素
            try:
                # 检查用户头像（通常在顶部导航栏）
                user_avatar = self.driver.find_elements(
                    By.XPATH, "//img[contains(@class, 'avatar') or contains(@src, 'avatar')]"
                )
                logged_in_elements.extend(user_avatar)
            except:
                pass
            
            try:
                # 检查个人中心入口
                profile_links = self.driver.find_elements(
                    By.XPATH, "//a[contains(@href, '/profile/') or contains(@href, '/account/')]"
                )
                logged_in_elements.extend(profile_links)
            except:
                pass
            
            try:
                # 检查消息通知（登录后才会有）
                notifications = self.driver.find_elements(
                    By.XPATH, "//*[contains(@class, 'notification') or contains(@class, 'message')]"
                )
                logged_in_elements.extend(notifications)
            except:
                pass
            
            # 综合判断：如果没有登录元素，或者存在登录后元素，则认为已登录
            has_login_elements = len(login_elements) > 0
            has_logged_in_elements = len(logged_in_elements) > 0
            
            self.is_logged_in = not has_login_elements or has_logged_in_elements
            return self.is_logged_in
        except:
            return False
            
    def search_by_keyword(self, keyword: str) -> List[Dict]:
        if not self.driver:
            self.init_driver()
            
        try:
            search_input = WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@placeholder='搜索你感兴趣的内容']")
                )
            )
            search_input.clear()
            search_input.send_keys(keyword)
            self.random_delay(0.5, 1)
            
            search_btn = self.driver.find_element(
                By.XPATH, "//button[contains(@class, 'search-btn') or .//*[name()='svg']]"
            )
            search_btn.click()
            self.random_delay(2, 4)
            
            notes = self._extract_search_results()
            return notes
            
        except TimeoutException:
            print("搜索超时，请检查页面元素")
            return []
            
    def _extract_search_results(self) -> List[Dict]:
        notes = []
        try:
            note_cards = self.driver.find_elements(
                By.XPATH, "//a[contains(@href, '/explore/')]"
            )
            
            for card in note_cards[:20]:
                try:
                    title = card.get_attribute('title') or ''
                    href = card.get_attribute('href') or ''
                    note_id = href.split('/')[-1] if href else ''
                    
                    if title and note_id:
                        notes.append({
                            'title': title,
                            'url': href,
                            'note_id': note_id
                        })
                except:
                    continue
                    
        except Exception as e:
            print(f"提取搜索结果出错: {e}")
            
        return notes
        
    def get_note_comments(self, note_url: str) -> List[Dict]:
        if not self.driver:
            self.init_driver()
            
        self.driver.get(note_url)
        self.random_delay(2, 4)
        
        comments = []
        try:
            self._scroll_to_load_comments()
            
            comment_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'comment-item')]"
            )
            
            for elem in comment_elements:
                try:
                    author_elem = elem.find_element(
                        By.XPATH, ".//a[contains(@class, 'author')]"
                    )
                    author = author_elem.text
                    
                    content_elem = elem.find_element(
                        By.XPATH, ".//div[contains(@class, 'content')]"
                    )
                    content = content_elem.text
                    
                    like_elem = elem.find_elements(
                        By.XPATH, ".//span[contains(@class, 'like')]"
                    )
                    likes = like_elem[0].text if like_elem else "0"
                    
                    comments.append({
                        'author': author,
                        'content': content,
                        'likes': likes,
                        'element': elem
                    })
                except:
                    continue
                    
        except Exception as e:
            print(f"获取评论出错: {e}")
            
        return comments
        
    def _scroll_to_load_comments(self):
        scroll_pause_time = 1.5
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(3):
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(scroll_pause_time)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
    def reply_comment(self, comment_element, reply_text: str) -> bool:
        try:
            reply_btn = comment_element.find_element(
                By.XPATH, ".//span[contains(text(), '回复')]"
            )
            reply_btn.click()
            self.random_delay(1, 2)
            
            reply_input = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//textarea[@placeholder='回复']")
                )
            )
            reply_input.clear()
            reply_input.send_keys(reply_text)
            self.random_delay(0.5, 1)
            
            submit_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), '发送')]"
            )
            submit_btn.click()
            self.random_delay(1, 2)
            
            return True
            
        except Exception as e:
            print(f"回复评论出错: {e}")
            return False
            
    def auto_reply_comments(
        self, 
        note_url: str, 
        reply_template: str,
        keywords_filter: Optional[List[str]] = None,
        max_replies: int = 5
    ) -> List[Dict]:
        comments = self.get_note_comments(note_url)
        replied_comments = []
        reply_count = 0
        
        for comment in comments:
            if reply_count >= max_replies:
                break
                
            if keywords_filter:
                if not any(kw in comment['content'] for kw in keywords_filter):
                    continue
                    
            reply_text = reply_template.replace(
                '{author}', comment['author']
            ).replace(
                '{content}', comment['content']
            )
            
            success = self.reply_comment(comment['element'], reply_text)
            if success:
                replied_comments.append({
                    'author': comment['author'],
                    'original_content': comment['content'],
                    'reply': reply_text,
                    'status': 'success'
                })
                reply_count += 1
                self.random_delay(2, 4)
                
        return replied_comments
        
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            
    def __del__(self):
        self.close()
