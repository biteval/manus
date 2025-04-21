from .browser import Chrome
from typing import Dict , Optional
import logging 
import tracemalloc
tracemalloc.start()

#Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

#Global name, browser dict
browser: Dict[str, Optional[Chrome|None]] = {}
NAME = "chrome"
browser[NAME] = None
BLANK="about:blank"


async def execute_javascript(script: str):
    """
    Execute JavaScript code in real-time browser using Playwright's evaluate method and return the script's result.
    Args:
        script (str): The JavaScript code to execute.
    """
    try:
        if browser[NAME] is not None:
            result = await browser[NAME].evaluate(script)
            return result
        else:
            return "The browser is not opened to execute javascript on it."
    except Exception as ex:
        return f"{ex}"


async def go_to_url(url: str) -> str:
    """
    Visit a target url in real-time browser if the browser is open.
    Arg:
        url (str) : the url you want to visit
    """
    if browser[NAME] is not None:
        try:
            await browser[NAME].go_to_url(url)
            return f"Navigated to {url} successfully."
        except Exception as ex:
            return f"go_to_url error: {ex}"
    return "No browser is opened currently."


async def get_curr_url():
    """
    Get the current visited url in the real-time browser.
    """
    try:
        curr_url =  browser[NAME].CURR_URL 
        return curr_url
    except Exception as ex:
        return f"Unable to get the current url: {ex}"



async def go_back():
    """
    Return back to the previous url or page in the real-time browser.
    """
    try:
        await browser[NAME].go_back()
        curr_url = browser[NAME].CURR_URL 
        return f"Returned back, you are now at {curr_url}"
    except Exception as ex:
        return f"Failed to return back with error: {ex}"


async def sleep_for(begin: float, end: float):
    """
    Sleep in real-time browser for a random seconds between begin and end 
    Args:
        begin: float value indicates the start time
        end: float value indicates the end time 
    Example: sleep_for(0.5, 1.5) sleeps between 0.5 seconds and 1.5 seconds in the current page before continue.
    """
    try:
        if browser[NAME] is not None:
            await browser[NAME].sleep_for(begin=begin, end=end)
            return f"Slept from {begin} to {end} seconds completed."
        else:
            return "No browser is opened to sleep for."
    except Exception as ex:
        return f"Sleep for {begin} to {end} seconds failed with error: {ex}"


async def close_browser():
    """
    Close the opened browser in real-time.
    """
    try:
        if browser[NAME] is not None:
            await browser[NAME].quit()
            browser[NAME] = None
            return f"{NAME} browser closed correctly."
        else:
            return "No browser is opened to close."
    except Exception as ex:
        return f"close_browser failed, error: {ex}"



async def open_browser(url:str=BLANK):
    """Open browser in real-time.
    Arg (optional):
        url (str) :  url to visit
    """
    try:
        if browser[NAME] is not None:
            return f"{NAME} browser already opened."
        else:
            browser[NAME] = await Chrome.create(chrome_version=None)  # Playwright doesn't need version
            msg = f"{NAME} browser opened"
            if not url==BLANK:
                await browser[NAME].go_to_url(url) #visit the url
                msg += f" with url: {url}"
            return msg
    except Exception as ex:
        return f"open_browser failed with error: {ex}"
        

async def take_browser_screenshot():
    """
        Capture a screenshot of the current browser page
        Returns:
            base64-encoded image string
    """
    try:
        if browser[NAME] is not None:
            result = await browser[NAME].screenshot() #base64 image
            return result
        else:
            return "No browser is open to capture a screenshot."
    except Exception as ex:
        return f"take_browser_screen_shot error: {str(ex)}"

