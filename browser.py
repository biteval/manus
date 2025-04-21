import sys
import random
import os
import asyncio
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import time
import platform
import logging

class Chrome:
    def __init__(self, chrome_version=None, incognito=True, hidden=False, profile=""):
        self.INCOGNITO = incognito
        self.CURR_URL = None
        self.BLANK = "about:blank"
        self.IS_HIDDEN = hidden
        self.PROFILE_PATH = profile
        self._init_complete = asyncio.Event()
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.chrome_version = chrome_version
    
    @classmethod
    async def create(cls, chrome_version=None, incognito=True, hidden=False, profile=""):
        """Async factory to construct and initialize the Chrome object."""
        self = cls(chrome_version, incognito, hidden, profile)
        # Start initialization in the background
        asyncio.create_task(self._background_init())
        return self
    
    async def _background_init(self):
        try:
            await self.init()
        finally:
            self._init_complete.set()  # Signal initialization is complete

    async def log(self, msg: str):
        logging.info(msg)

    def clear_terminal(self):
        os.system("cls" if sys.platform == "win32" else "clear")

    async def close(self):
        """Close current page but keep browser running"""
        await self._init_complete.wait()  # Wait for initialization to complete
        if self.page:
            await self.page.close()
            self.page = None

    async def quit(self):
        """Close everything: page, context, browser and playwright"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            return True
        except Exception as ex:
            await self.log(f"Error during quit: {str(ex)}")
            return False

    async def init(self):
        """Initialize playwright, browser, context and page"""
        await self.quit()  # Ensure any previous instance is closed
        
        try:
            # Launch playwright - fully async
            self.playwright = await async_playwright().start()
            
            # Configure browser options with undetected settings
            browser_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-popup-blocking",
                "--disable-extensions",
                f"--window-size=1280,800",
                "--start-maximized"
            ]
            
            # Launch browser
            browser_type = self.playwright.chromium
            launch_options = {
                "headless": self.IS_HIDDEN,
                "args": browser_args,
                "ignore_default_args": ["--enable-automation"]
            }
            
            # Add user data directory if profile is specified
            if self.PROFILE_PATH:
                launch_options["user_data_dir"] = self.PROFILE_PATH
            
            self.browser = await browser_type.launch(**launch_options)
            
            # Create context with custom properties to avoid detection
            context_options = {
                "viewport": {"width": 1280, "height": 800},
                "user_agent": self._generate_user_agent(),
                "has_touch": True,
                "locale": "en-US",
                "timezone_id": "America/New_York",
                "permissions": ["geolocation", "notifications"],
                "is_mobile": False
            }
            
            # If using incognito and not a profile
            if self.INCOGNITO and not self.PROFILE_PATH:
                # We continue with isolated context settings above
                pass
                
            self.context = await self.browser.new_context(**context_options)
            
            # Override automation-related JavaScript properties
            await self._apply_stealth_settings()
            
            # Create page
            self.page = await self.context.new_page()
            
        except Exception as ex:
            await self.log(f"Initialization error: {str(ex)}")
            await self.quit()
            raise

    async def _apply_stealth_settings(self):
        """Apply stealth settings to avoid detection"""
        # Create script to modify navigator and WebDriver properties
        stealth_script = """
        () => {
            // Overwrite the automation property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
            
            // Overwrite chrome property
            if (window.chrome === undefined) {
                window.chrome = {};
                window.chrome.runtime = {};
            }
            
            // Overwrite permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
            
            // Webdriver fix
            delete navigator.__proto__.webdriver;
            
            // Plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [
                        {
                            0: {type: "application/pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        }
                    ];
                }
            });
            
            // Languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        }
        """
        # Add the script to all pages in the context
        await self.context.add_init_script(stealth_script)

    def _generate_user_agent(self):
        """Generate a realistic user agent string"""
        os_version = ""
        if platform.system() == "Windows":
            os_version = "Windows NT 10.0; Win64; x64"
        elif platform.system() == "Darwin":
            os_version = "Macintosh; Intel Mac OS X 10_15_7"
        else:
            os_version = "X11; Linux x86_64"
            
        chrome_version = self.chrome_version or "135.0.7049.52"
        
        return f"Mozilla/5.0 ({os_version}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"

    async def sleep_for(self, begin: float, end: float):
        # Sleep asynchronously for a random duration between begin and end seconds.
        await asyncio.sleep(random.uniform(begin, end))

    async def die_with_code(self, code: int):
        await self.quit()
        sys.exit(code)

    async def get(self):
        # Wait for initialization to complete
        await self._init_complete.wait()
        if not self.page:
            await self.init()
        return self

    async def refresh(self):
        # Make sure browser is initialized before using it
        await self.get()
        try:
            await self.page.reload()
            return True
        except Exception as ex:
            await self.log(f"Refresh error: {str(ex)}")
            return False

    async def go_to_url(self, url: str):
        # Make sure browser is initialized before using it
        await self.get()
        try:
            await self.page.goto(url, wait_until="domcontentloaded")
            self.CURR_URL = url
            
            # Add random delay to simulate human behavior
            await self.sleep_for(0.5, 2.0)
            
            # Perform random mouse movements to appear more human-like
            await self._simulate_human_behavior()
            
            return True
        except Exception as ex:
            await self.log(f"Navigation error while moving to {url}: {str(ex)}")
            return False

    async def _simulate_human_behavior(self):
        """Simulate human-like behavior with mouse movements"""
        try:
            # Get page dimensions
            dimensions = await self.page.evaluate("""
                () => {
                    return {
                        width: window.innerWidth,
                        height: window.innerHeight
                    }
                }
            """)
            
            # Perform some random mouse movements
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, dimensions['width'] - 200)
                y = random.randint(100, dimensions['height'] - 200)
                await self.page.mouse.move(x, y)
                await self.sleep_for(0.1, 0.3)
                
            # Scroll a bit
            await self.page.mouse.wheel(0, random.randint(100, 300))
            await self.sleep_for(0.2, 0.5)
                
        except Exception as ex:
            await self.log(f"Error simulating human behavior: {str(ex)}")

    async def go_back(self):
        # Make sure browser is initialized before using it
        await self.get()
        try:
            await self.page.go_back()
            self.CURR_URL = self.page.url
            await self.sleep_for(0.5, 1.0)  # Add random delay for human-like behavior
            return True
        except Exception as ex:
            await self.log(f"Navigation error while moving back: {str(ex)}")
            return False
            
    # Additional helpful methods that Playwright enables

    async def get_content(self):
        """Get the HTML content of the current page"""
        await self.get()
        return await self.page.content()
        
    async def screenshot(self, path=None, return_base64=True):
        """
        Take a screenshot of the current page
        
        Args:
            path (str, optional): Path to save the screenshot. 
            return_base64 (bool, optional): If True, returns base64 encoded image instead of saving to file.
        
        Returns:
            str: Path to saved image file or base64-encoded image string
        """
        await self.get()
        
        if return_base64:
            import base64
            # Capture screenshot as base64
            img_bytes = await self.page.screenshot(type='png')
            base64_screenshot = base64.b64encode(img_bytes).decode('utf-8')
            return base64_screenshot
        else:
            # Save to file
            if not path:
                path = f"screenshot_{int(time.time())}.png"
            await self.page.screenshot(path=path)
            return path
    
        
    async def evaluate(self, js_code):
        """Run JavaScript code on the page and return the result"""
        await self.get()
        return await self.page.evaluate(js_code)
        