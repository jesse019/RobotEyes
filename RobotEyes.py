from PIL import Image
import subprocess
import os, shutil, time
from robot.libraries.BuiltIn import BuiltIn


class RobotEyes(object):

    def __init__(self, mode):
        self.mode = mode
        self.root_path = os.path.dirname(os.path.abspath(__file__))

    def open_eyes(self):
        try:
            s2l = BuiltIn().get_library_instance('Selenium2Library')
            self.driver = s2l._current_browser()
        except:
            try:
                appiumlib = BuiltIn().get_library_instance('AppiumLibrary')
                self.driver = appiumlib._current_application()
            except:
                raise ValueError('Browser/App is not open')

        self.test_name = BuiltIn().replace_variables('${TEST NAME}')
        self.count = 1
        test_name = self.test_name.replace(' ', '_')

        if self.mode.lower() == 'test':
            if os.path.exists(self.root_path + '/actual/' + test_name):
                shutil.rmtree(self.root_path + '/actual/' + test_name)

            if os.path.exists(self.root_path + '/diff/' + test_name):
                shutil.rmtree(self.root_path + '/diff/' + test_name)
        elif self.mode.lower() == 'baseline':
            if os.path.exists(self.root_path + '/baseline/' + test_name):
                shutil.rmtree(self.root_path + '/baseline/' + test_name)
        else:
            raise ValueError('Browser/App is not open')

    def capture_full_screen(self):
        test_name = self.test_name.replace(' ', '_')

        if self.mode.lower() == 'baseline':
            path = self.root_path + '/baseline/' + test_name
        elif self.mode.lower() == 'test':
            path = self.root_path + '/actual/' + test_name

        if not os.path.exists(path):
            os.makedirs(path)

        print 'Capturing page...'
        self.driver.save_screenshot(path + '/img' + str(self.count) + '.png')
        self.count += 1

    def capture_element(self, selector):
        test_name = self.test_name.replace(' ', '_')

        if self.mode.lower() == 'baseline':
            path = self.root_path + '/baseline/' + test_name
        elif self.mode.lower() == 'test':
            path = self.root_path + '/actual/' + test_name

        if selector.startswith('//'):
            prefix = 'xpath'
            locator = selector
        else:
            selector_parts = selector.partition('=')
            prefix = selector_parts[0].strip()
            locator = selector_parts[2].strip()
            if not locator:
                raise ValueError('Please prefix locator type.')

        if prefix.lower() == 'xpath':
            search_element = self.driver.find_element_by_xpath(locator)
        elif prefix.lower() == 'id':
            search_element = self.driver.find_element_by_id(locator)
        elif prefix.lower() == 'class':
            search_element = self.driver.find_element_by_class_name(locator)
        elif prefix.lower() == 'css':
            search_element = self.driver.find_element_by_css_selector(locator)

        location = search_element.location
        size = search_element.size

        if not os.path.exists(path):
            os.makedirs(path)

        print 'Capturing element...'
        self.driver.save_screenshot(path + '/img' + str(self.count) + '.png')

        im = Image.open(path + '/img' + str(self.count) + '.png')
        left = int(location['x'])
        top = int(location['y'])
        right = int(location['x'] + size['width'])
        bottom = int(location['y'] + size['height'])
        im = im.crop((left+left, top+top, right+right, bottom+bottom))  # defines crop points
        im.save(path + '/img' + str(self.count) + '.png')
        self.count += 1

    def scroll_to_element_and_capture(self, xpath):
        test_name = self.test_name.replace(' ', '_')

        if self.mode.lower() == 'baseline':
            path = self.root_path + '/baseline/' + test_name
        elif self.mode.lower() == 'test':
            path = self.root_path + '/actual/' + test_name

        if not os.path.exists(path):
            os.makedirs(path)

        search_element = self.driver.find_element_by_xpath(xpath)
        self.driver.execute_script("return arguments[0].scrollIntoView();", search_element)
        time.sleep(2)
        self.driver.save_screenshot(path + '/img' + str(self.count) + '.png')
        xpath = xpath.replace('"', "'")
        cmd = "var e = document.evaluate(\"{0}\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null)" \
              ".singleNodeValue;return e.getBoundingClientRect();".format(xpath)
        coord = self.driver.execute_script(cmd)
        left = coord['left']
        top = coord['top']
        right = coord['right']
        bottom = coord['bottom']

        im = Image.open(path + '/img' + str(self.count) + '.png')
        im = im.crop((left + left, top + top, right + right, bottom + bottom))  # defines crop points
        im.save(path + '/img' + str(self.count) + '.png')
        self.count += 1

    def compare_images(self):
        if self.mode.lower() == 'test':
            test_name = self.test_name.replace(' ', '_')
            baseline_path = self.root_path + '/baseline/' + test_name
            actual_path = self.root_path + '/actual/' + test_name
            diff_path = self.root_path + '/diff/' + test_name

            # compare actual and baseline images and save the diff image
            for filename in os.listdir(actual_path):
                if filename.endswith('.png'):
                    a_path = ''
                    b_path = ''
                    d_path = ''

                    if not os.path.exists(diff_path):
                        os.makedirs(diff_path)

                    b_path = baseline_path + '/' + filename
                    a_path = actual_path + '/' + filename
                    d_path = diff_path + '/' + filename

                    compare_cmd = 'compare -metric RMSE -subimage-search -dissimilarity-threshold 1.0 %s %s %s' \
                                  % (a_path, b_path, d_path)

                    proc = subprocess.Popen(compare_cmd,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    out, err = proc.communicate()
                    difference = err.split()[1][1:-1]
                    output = open(actual_path + '/' + filename + '.txt', 'w')
                    output.write(difference)
                    output.close()