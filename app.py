from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

@app.route('/')
def index():
    """
    Render the input form.
    """
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """
    Perform Selenium scraping and return styled results.
    """
    input_code = request.form.get('course_code', '').upper().replace(" ", "")
    formatted_input = input_code[0:4] + " " + input_code[4:] if len(input_code) >= 5 else None

    if not formatted_input:
        return render_template('results.html', error="Invalid course code. Please try again.")

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')  
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)
    url = "https://cab.brown.edu/"
    driver.get(url)

    free_sections = {}
    try:
        wait = WebDriverWait(driver, 10)
        search_input = wait.until(
            EC.visibility_of_element_located((By.XPATH, '//input[@class="form-control"]'))
        )
        search_input.send_keys(formatted_input[:4])
        search_input.send_keys(Keys.RETURN)

        xpath_string = '//div[@class="panel panel--kind-results panel--visible"]//div[@class="panel__body"]//div[@class="result result--group-start"]'
        wait.until(EC.visibility_of_element_located((By.XPATH, xpath_string)))
        courses = driver.find_elements(By.XPATH, xpath_string)

        course_found = False
        for course in courses:
            course_code = course.find_element(
                By.XPATH, 
                './/a//span[@class="result__headline"]//span[@class="result__code"]'
            ).text

            if course_code == formatted_input:
                course_found = True
                course.click()
                wait.until(
                    EC.visibility_of_element_located(
                        (By.XPATH, '//div[@class="course-sections"]//a[@class="course-section course-section--matched"]')
                    )
                )
                sections = driver.find_elements(
                    By.XPATH, 
                    '//div[@class="course-sections"]//a[@class="course-section course-section--matched"]'
                )

                for section in sections:
                    try:
                        section.find_element(By.XPATH, './/i[@class="fa fa-fw icon--warn"]')
                    except:
                        section_string = section.find_element(
                            By.XPATH, './/div[@class="course-section-section"]'
                        ).text[-3:]
                        time_string = section.find_element(
                            By.XPATH, './/div[@class="course-section-all-sections-meets"]'
                        ).text.replace('Meets:\n', '')
                        free_sections[section_string] = time_string

        if not course_found:
            return render_template('results.html', error="Course not found.")

    except Exception as e:
        return render_template('results.html', error=f"An error occurred: {str(e)}")

    finally:
        driver.quit()

    return render_template('results.html', free_sections=free_sections, course_code=formatted_input)

if __name__ == '__main__':
    app.run(debug=True)