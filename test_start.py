from playwright.sync_api import sync_playwright
import requests
import logging
import http.client
import time
import random
from concurrent.futures import ThreadPoolExecutor
from config import CONFIG
from datetime import datetime

class NewsWebsiteTest:
    def __init__(self):
        self.bot_token = CONFIG['bot_token']
        self.chat_id = CONFIG['chat_id']
        self.base_url = CONFIG['base_url']
        self.servers = CONFIG['servers']
        self.port = CONFIG['port']
        self.dev_mode = False
        self.enable_telegram = CONFIG['telegram_settings']['enable_messages']
        self.categories = []
        self.tags = []
        self.max_pages = CONFIG['scroll_settings']['max_pages']
        self.scroll_timeout = CONFIG['scroll_settings']['scroll_timeout']
        self.load_timeout = CONFIG['scroll_settings']['load_timeout']
        self.success_count = 0
        self.error_count = 0
        self.start_time = None

    def format_error_message(self, error, context=""):
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"❌ Error during testing oxu.az\n\n"
        message += f"🕐 Time: {current_time}\n"
        if context:
            message += f"📍 Location: {context}\n"
        message += f"⚠️ Error: {str(error)}\n"
        
        return message

    def send_test_report(self):
        
        duration = time.time() - self.start_time
        report = "📊 Test Report for oxu.az\n\n"
        report += f"✅ Successful checks: {self.success_count}\n"
        report += f"❌ Errors: {self.error_count}\n"
        report += f"⏱ Duration: {duration:.1f} sec\n"
        
        self.send_telegram_message(report)

    def send_telegram_message(self, message):
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }

            # Log the request data (without the token)
            if self.dev_mode:
                print(f"\nSending message to Telegram:")
                print(f"Chat ID: {self.chat_id}")
                print(f"Message: {message}")

            # Send the request
            response = requests.post(url, data=data, timeout=10)
            
            # Check the response
            if response.status_code == 200:
                if self.dev_mode:
                    print(f"✅ Message sent successfully")
                return True
            else:
                error_msg = f"Error sending: HTTP {response.status_code}, {response.text}"
                if self.dev_mode:
                    print(f"❌ {error_msg}")
                logging.error(error_msg)
                return False

        except Exception as e:
            error_msg = f"Error sending to Telegram: {str(e)}"
            logging.error(error_msg)
            if self.dev_mode:
                print(f"❌ {error_msg}")
            return False

    def safe_click(self, page, selector):
        try:
            element = page.wait_for_selector(selector, timeout=500)
            if element:
                element.click()
                return True
            return False
        except Exception:
            return False

    def make_screenshot(self, page, name):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screenshot_{name}_{timestamp}.png"
            page.screenshot(path=filename)
            return filename
        except Exception as e:
            logging.error(f"Error taking screenshot: {str(e)}")
            return None

    def get_categories(self, page):
        try:
            if self.dev_mode:
                print("Getting the list of categories...")
            
            # Click the menu button
            self.safe_click(page, '.custom-navbar-toggle')
            page.wait_for_timeout(500)

            # Wait for the menu to appear
            page.wait_for_selector('.custom-navbar-menu', timeout=1000)
            
            # Get all the links from the menu
            menu_links = page.query_selector_all('.custom-navbar-menu ul li a')
            
            categories = []
            excluded_categories = ['Home']
            
            for link in menu_links:
                category_span = link.query_selector('span')
                if category_span:
                    category_name = category_span.inner_text().strip()
                    if category_name and category_name not in excluded_categories:
                        href = link.get_attribute('href')
                        if href and 'oxu.az' in href:
                            category_path = href.split('oxu.az/')[1]
                            categories.append(category_path)

            # Close the menu
            self.safe_click(page, '.custom-navbar-toggle')
            page.wait_for_timeout(300)

            # Select random 3 categories
            random_categories = random.sample(categories, min(3, len(categories)))

            if self.dev_mode:
                print(f"Found categories: {random_categories}")
                
            return random_categories
                
        except Exception as e:
            screenshot = self.make_screenshot(page, "categories_error")
            error_msg = f"Error getting categories: {str(e)}"
            if screenshot:
                error_msg += f"\nScreenshot: {screenshot}"
            raise Exception(error_msg)
        

    def get_tags(self, page):
        try:
            if self.dev_mode:
                print("Getting the list of tags...")
        
            # Wait for the menu to appear
            page.wait_for_selector('.custom-navbar-tags', timeout=1000)
            
            # Get all the links from the menu
            menu_links = page.query_selector_all('.swiper ul li a')
            
            tags = []
            excluded_tags = ['Home']
            
            for link in menu_links:
                tag_span = link.query_selector('span')
                if tag_span:
                    tag_name = tag_span.inner_text().strip()
                    if tag_name and tag_name not in excluded_tags:
                        href = link.get_attribute('href')
                        if href and 'oxu.az' in href:
                            tag_path = href.split('oxu.az/')[1]
                            tags.append(tag_path)

            
            # Select random 3 tags
            random_tags = random.sample(tags, min(3, len(tags)))

            if self.dev_mode:
                print(f"Found tags: {random_tags}")
                
            return random_tags
                
        except Exception as e:
            screenshot = self.make_screenshot(page, "tags_error")
            error_msg = f"Error getting tags: {str(e)}"
            if screenshot:
                error_msg += f"\nScreenshot: {screenshot}"
            raise Exception(error_msg)

    def check_server(self, server_name, server_ip):
            try:
                if self.dev_mode:
                    print(f"\nChecking server {server_name} ({server_ip})...")

                conn = http.client.HTTPConnection(server_ip, self.port, timeout=10)
                conn.request("GET", "/", headers={"Host": "oxu.az"})
                response = conn.getresponse()

                status_code = response.status
                status_message = response.reason
                server_header = response.getheader('Server', 'Unknown')

                response.read()  # Ensure the response is read completely
                conn.close()

                result = {
                    'status_code': status_code,
                    'status_message': status_message,
                    'server': server_header,
                    'is_ok': 200 <= status_code < 400
                }

                if self.dev_mode:
                    print(f"Server {server_name}:")
                    print(f"  Status code: {status_code}")
                    print(f"  Status: {status_message}")
                    print(f"  Server: {server_header}")
                    print(f"  Working: {'Yes' if result['is_ok'] else 'No'}")

                return result
            except Exception as e:
                error_msg = f"Error checking server {server_name}: {str(e)}"
                if self.dev_mode:
                    print(error_msg)
                return {
                    'status_code': None,
                    'status_message': str(e),
                    'server': None,
                    'is_ok': False
                }


    def check_all_servers(self):
        try:
            if self.dev_mode:
                print("\nStarting server checks...")

            server_results = {}
            
            with ThreadPoolExecutor(max_workers=len(self.servers)) as executor:
                future_to_server = {
                    executor.submit(self.check_server, name, ip): name 
                    for name, ip in self.servers.items()
                }
                
                for future in future_to_server:
                    server_name = future_to_server[future]
                    try:
                        server_results[server_name] = future.result()
                    except Exception as e:
                        server_results[server_name] = {
                            'status_code': None,
                            'status_message': str(e),
                            'server': None,
                            'is_ok': False
                        }

            report = "📊 Server Status:\n\n"
            all_servers_ok = True

            for server_name, result in server_results.items():
                status_emoji = "✅" if result['is_ok'] else "❌"
                report += f"{status_emoji} {server_name}:\n"
                report += f"  Status code: {result['status_code']}\n"
                report += f"  Status: {result['status_message']}\n"
                report += f"  Server: {result['server']}\n\n"
                
                if not result['is_ok']:
                    all_servers_ok = False

            if not all_servers_ok:
                self.send_telegram_message(report)

            return server_results

        except Exception as e:
            error_msg = f"Error checking servers: {str(e)}"
            self.send_telegram_message(f"❌ {error_msg}")
            raise Exception(error_msg)

    def scroll_and_check_news(self, page, context=""):
        try:
            if self.dev_mode:
                print(f"\nStarting news check: {context}")

            analytics_requests = []
            url_change_times = {}

            def get_current_page(url):
                """Extract page number from URL"""
                if '/page/' in url:
                    try:
                        return int(url.split('/page/')[1].split('/')[0])
                    except:
                        return 1
                return 1

            # Set up analytics request interception
            def handle_analytics_request(route, request):
                if "www.google-analytics.com/g/collect" in request.url:
                    current_time = time.time()
                    matching_page = None
                    for page_num, change_time in url_change_times.items():
                        if 0 <= current_time - change_time <= 5:
                            matching_page = page_num
                            break

                    if matching_page:
                        if self.dev_mode:
                            print(f"✅ Detected Google Analytics request for page {matching_page}")
                        analytics_requests.append({
                            'url': request.url,
                            'page': matching_page,
                            'time': current_time
                        })
                route.continue_()

            page.route("**/*", handle_analytics_request)

            # Check initial news content
            initial_news = page.query_selector_all('.index-post-block')
            if not initial_news:
                raise Exception("No news found on initial page load")
            
            if self.dev_mode:
                print(f"Initial news count: {len(initial_news)}")

            def scroll_until_url_change(target_page):
                """
                Scroll until URL changes to target page or timeout occurs
                Returns: Boolean indicating if target page was reached
                """
                start_time = time.time()
                last_url = page.url
                last_page = get_current_page(last_url)
                scroll_count = 0
                max_scroll_attempts = 50
                
                while time.time() - start_time < self.scroll_timeout:
                    page.evaluate("""
                        window.scrollBy(0, 300);
                    """)
                    page.wait_for_timeout(100)
                    
                    current_url = page.url
                    current_page = get_current_page(current_url)
                    
                    if current_page != last_page:
                        url_change_times[current_page] = time.time()
                        if self.dev_mode:
                            print(f"URL changed to page {current_page}")
                        last_page = current_page

                    if current_page == target_page:
                        if self.dev_mode:
                            print(f"✅ Reached target page {target_page}")
                        page.wait_for_timeout(1000)
                        return True
                    
                    current_news_count = len(page.query_selector_all('.index-post-block'))
                    if current_news_count > len(initial_news):
                        scroll_count = 0
                    else:
                        scroll_count += 1
                    
                    if scroll_count > max_scroll_attempts:
                        if self.dev_mode:
                            print(f"⚠️ Scroll limit reached while looking for page {target_page}")
                        return False
                    
                    last_url = current_url
                
                if self.dev_mode:
                    print(f"⚠️ Timeout while looking for page {target_page}")
                return False

            if not scroll_until_url_change(2):
                raise Exception("Failed to reach page 2")
            
            page.wait_for_timeout(5000) 
            page_2_analytics = [req for req in analytics_requests if req['page'] == 2]
            if not page_2_analytics:
                raise Exception("No Google Analytics requests detected for page 2")

            if not scroll_until_url_change(3):
                raise Exception("Failed to reach page 3")
            
            page.wait_for_timeout(5000)
            page_3_analytics = [req for req in analytics_requests if req['page'] == 3]
            if not page_3_analytics:
                raise Exception("No Google Analytics requests detected for page 3")

            # Total news counting
            total_news = len(page.query_selector_all('.index-post-block'))
            
            if self.dev_mode:
                print(f"Total news found: {total_news}")
                print(f"Final URL: {page.url}")
                print("Analytics requests summary:")
                for page_num in sorted(set(req['page'] for req in analytics_requests)):
                    page_reqs = [req for req in analytics_requests if req['page'] == page_num]
                    print(f"Page {page_num}: {len(page_reqs)} requests")

            return total_news

        except Exception as e:
            raise Exception(f"Error during scroll check: {str(e)}")

    def check_main_page(self, page):
        try:
            if self.dev_mode:
                print("Checking the main page...")
            page.wait_for_selector('.main-slider', timeout=5000)
            
            # Check news by scrolling to the third page
            total_news = self.scroll_and_check_news(page, "Main page")
            
            if total_news == 0:
                raise Exception("No news on the main page")
            if self.dev_mode:
                print(f"Total news found on the main page: {total_news}")
                
        except Exception as e:
            screenshot = self.make_screenshot(page, "main_page_error")
            error_msg = f"Error checking the main page: {str(e)}"
            if screenshot:
                error_msg += f"\nScreenshot: {screenshot}"
            raise Exception(error_msg)

    def check_category(self, page, category):
        try:
            if self.dev_mode:
                print(f"\nChecking category: {category}")
            page.goto(f"{self.base_url}/{category}")
            page.wait_for_selector('.main-posts-title', timeout=5000)
            
            # Check news by scrolling to the third page
            total_news = self.scroll_and_check_news(page, f"Category {category}")
            
            if total_news == 0:
                raise Exception(f"No news in the {category} category")
            if self.dev_mode:
                print(f"Total news found in the {category} category: {total_news}")
                
        except Exception as e:
            screenshot = self.make_screenshot(page, f"category_{category}_error")
            error_msg = f"Error checking the {category} category: {str(e)}"
            if screenshot:
                error_msg += f"\nScreenshot: {screenshot}"
            raise Exception(error_msg)
        
    def check_tag(self, page, tag):
        try:
            if self.dev_mode:
                print(f"\nChecking category: {tag}")
            page.goto(f"{self.base_url}/{tag}")
            page.wait_for_selector('.main-posts-title', timeout=5000)
            
            # Check news by scrolling to the third page
            total_news = self.scroll_and_check_news(page, f"tag {tag}")
            
            if total_news == 0:
                raise Exception(f"No news in the {tag} tag")
            if self.dev_mode:
                print(f"Total news found in the {tag} tag: {total_news}")
                
        except Exception as e:
            screenshot = self.make_screenshot(page, f"tag_{tag}_error")
            error_msg = f"Error checking the {tag} tag: {str(e)}"
            if screenshot:
                error_msg += f"\nScreenshot: {screenshot}"
            raise Exception(error_msg)


    def check_search(self, page):
        try:
            if self.dev_mode:
                print("\nChecking the search...")
            
            # Open the search
            self.safe_click(page, '.custom-navbar-search-toggle')
            page.wait_for_timeout(300)
            
            # Enter the search query
            search_term = "ilham əliyev"
            page.fill('.custom-navbar-search-form form input', search_term)
            page.press('.custom-navbar-search-form form', 'Enter')
            
            page.wait_for_selector('.main-posts-title', timeout=5000)
            
            news_items = page.query_selector_all('.index-post-block')
            total_news = len(news_items)
            
            if total_news == 0:
                raise Exception("Search results is empty")
            
            if self.dev_mode:
                print(f"Search results first page: {total_news}")
                
        except Exception as e:
            screenshot = self.make_screenshot(page, "search_error")
            error_msg = f"Search error: {str(e)}"
            if screenshot:
                error_msg += f"\nScreenshot: {screenshot}"
            raise Exception(error_msg)




    def run_tests(self):
        self.start_time = time.time()

        # Отправка первого сообщения
        try:
            test_message = "🔄 Test start oxu.az\n\n" \
                        "📅 Date: {}\n" \
                        "🕐 Time: {}"
            current_time = datetime.now()
            formatted_message = test_message.format(
                current_time.strftime("%Y-%m-%d"),
                current_time.strftime("%H:%M:%S")
            )
            self.send_telegram_message(formatted_message)

        except Exception as e:
            logging.error(f"Ошибка при отправке первого сообщения: {str(e)}")
            return

        # Запуск браузера Playwright
        with sync_playwright() as p:
            browser_launch_options = {
                "headless": True if not self.dev_mode else False,
            }

            if self.dev_mode:
                browser_launch_options.update({"devtools": True})

            browser = p.chromium.launch(**browser_launch_options)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

            try:
                # Переход на сайт
                page.goto(self.base_url)

                # Получение категорий и тегов
                self.categories = self.get_categories(page)
                self.tags = self.get_tags(page)
                self.success_count += 1

                # Тест главной страницы
                self.check_main_page(page)
                self.success_count += 1

                # Тест категорий
                for category in self.categories:
                    try:
                        self.check_category(page, category)
                        self.success_count += 1
                    except Exception as e:
                        self.error_count += 1
                        error_message = self.format_error_message(e, f"Ошибка в категории: {category}")
                        self.send_telegram_message(error_message)

                # Тест тегов
                for tag in self.tags:
                    try:
                        self.check_tag(page, tag)
                        self.success_count += 1
                    except Exception as e:
                        self.error_count += 1
                        error_message = self.format_error_message(e, f"Ошибка в теге: {tag}")
                        self.send_telegram_message(error_message)

                # Тест поиска
                try:
                    self.check_search(page)
                    self.success_count += 1
                except Exception as e:
                    self.error_count += 1
                    error_message = self.format_error_message(e, "Ошибка в поиске")
                    self.send_telegram_message(error_message)

            except Exception as e:
                self.error_count += 1
                error_message = self.format_error_message(e, "Общая ошибка тестирования")
                self.send_telegram_message(error_message)
                logging.error(error_message)

            finally:
                # Отправка отчёта
                self.send_test_report()

                # Закрытие браузера
                if not self.dev_mode:
                    context.close()
                    browser.close()
                else:
                    input("Тест завершён. Нажмите Enter для закрытия.")
                    context.close()
                    browser.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='news_website_test.log'
    )
    
    test = NewsWebsiteTest()
    
    # telegram connect test
    

    test.run_tests()
