from selenium.webdriver.common.by import By
# A 'database' that selenium will call before taking a screenshot to remove elements from a page, like navigation headers and such
# Easily customizable, can manipulate webpage in anyway since executing JS
def removeApplicableElements(driver, pageUrl):
    if 'apnews.com' in pageUrl:
        # Remove header
        driver.execute_script("""
        var idElement = document.getElementById('Page-header-trending-zephr');
        idElement.remove();
        """)
        
        # Remove main headline
        driver.execute_script("""
        var classElement = document.getElementsByClassName('PageListStandardE-items');
        classElement[0].remove();
        """)
        
        # Remove ad below stories
        driver.execute_script("""
                var classElement = document.getElementsByClassName('SovrnAd Advertisement sovrn-curated-hub');
                classElement[0].remove();
                """)
        
    elif 'foxnews.com' in pageUrl:
        # Remove network wrapper
        driver.execute_script("""
        var classElement = document.getElementsByClassName('network-wrapper');
        classElement[0].remove();
        """)
        
        # Remove header
        driver.execute_script("""
                var classElement = document.getElementsByClassName('site-header');
                classElement[0].remove();
                """)
        
        # Remove sidebar 
        driver.execute_script("""
                var classElement = document.getElementsByClassName('sidebar desktop desktop-sm-min sidebar-primary');
                classElement[0].remove();
                """)
        
        # Remove ad container : 
        driver.execute_script("""
                var classElement = document.getElementsByClassName('ad-container desktop ad-h-250 ad-w-970');
                classElement[0].remove();
                """)
        
    elif 'cnn.com' in pageUrl:
        # Remove header
        driver.execute_script("""
        var classElement = document.getElementsByClassName('header__wrapper-outer');
        classElement[0].remove();
        """)
        
        # Remove trending 
        driver.execute_script("""
        var classElement = document.getElementsByClassName('product-zone__items layout--full-width');
        classElement[0].remove();
        """)