import time
from urllib import parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

URL = ''
LOGIN = ''
PASSWORD = ''

# Search keywords
KW = ('Python', 'Web', 'Wordpress')

# Desired work experience
EXPERIENCE = ('between1And3', 'noExperience', 'doesNotMatter')

# All search filters
REQUEST_PARAMS = {
    'text': '',
    'experience': '',
    'search_period': '0',
    'schedule': 'remote',
    'items_on_page': '100',
    'search_field': 'name'
}

# All ID of suitable vacancies
_vacancy_id = []

# ID of vacancies for which it was not possible to send a response due to the requirement of a preliminary test
no_response_vacancy_id = []


def response_vacancy(driver) -> bool:
    """ Collects all job IDs and then applies for them

    :param driver: webdriver Chrome
    :return: None
    """
    try:
        # Gets all ids for the current request
        links = driver.find_elements(By.XPATH, '//a[contains(@href, "vacancy_response?vacancyId=")]')
        for link in links:
            _vacancy_id.append(
                parse.parse_qs(parse.urlparse(link.get_attribute('href')).query)['vacancyId'][0]
            )

        try:
            # Go to the next page and repeat the same
            driver.find_element(By.XPATH, '//a[@data-qa="pager-next"]').click()
            return response_vacancy(driver)

        # If there is no next page, then we respond to vacancies
        except NoSuchElementException:
            for vacancy_id in _vacancy_id:
                driver.get(f'{URL}/applicant/vacancy_response?vacancyId={vacancy_id}')

                # If you need to confirm the response
                try:
                    driver.find_element(By.XPATH, '//button[@data-qa="relocation-warning-confirm"]').click()
                except NoSuchElementException:
                    pass

                # Check if the response succeeded
                try:
                    driver.find_element(By.XPATH, f'//p[@data-qa="employer-asking-for-test"]')
                    no_response_vacancy_id.append(vacancy_id)
                except NoSuchElementException:
                    pass

                try:
                    error_un_click = driver.find_element(By.XPATH, f'//div[@class="bloko-translate-guard"]')
                    if 'В течение 24 часов можно совершить не более 200 откликов.' in error_un_click.text:
                        return False
                except NoSuchElementException:
                    pass
    except NoSuchElementException:
        return True


def main():
    # Opening the browser
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()

    try:
        # Authorization
        driver.get(f'{URL}/account/login')
        driver.find_element(By.XPATH, '//button[@data-qa="expand-login-by-password"]').click()
        driver.implicitly_wait(10)
        driver.find_element(By.XPATH, '//input[@name="username"][@type="text"]').send_keys(LOGIN)
        driver.find_element(By.XPATH, '//input[@type="password"]').send_keys(PASSWORD)
        driver.find_element(By.XPATH, '//button[@data-qa="account-login-submit"]').click()

        driver.switch_to.new_window('tab')
        driver.get(URL)

        # Search for vacancies by relevant keywords
        for kw in KW:
            for exp in EXPERIENCE:
                REQUEST_PARAMS['text'] = kw
                REQUEST_PARAMS['experience'] = exp

                driver.get(f'{URL}/search/vacancy?{parse.urlencode(REQUEST_PARAMS)}')

                if not response_vacancy(driver):
                    driver.quit()
                    break
            else:
                continue
            break

    # The browser closes and displays the id of vacancies with a failed application
    finally:
        print(set(no_response_vacancy_id))


if __name__ == '__main__':
    main()
