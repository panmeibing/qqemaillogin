import sys
import time
import cv2
import os
import requests
import random
import numpy as np
from PIL import Image as Im
from selenium import webdriver
from selenium.webdriver import ActionChains


class QQEmail(object):
    def __init__(self, user, pwd):
        self.root = sys.path[0] + "/pic/"
        self.driver = webdriver.Firefox()
        self.user = user  # 用户名
        self.pwd = pwd  # 密码

    def login_email(self):
        login_url = "https://mail.qq.com"
        time.sleep(2)
        self.driver.get(login_url)
        time.sleep(2)

        self.driver.switch_to.frame("login_frame")
        try:
            self.driver.find_element_by_id("switcher_plogin").click()
        except Exception as e:
            print(e)
        time.sleep(1)

        u_input = self.driver.find_element_by_id("u")
        u_input.clear()
        u_input.send_keys(self.user)
        time.sleep(1)
        p_input = self.driver.find_element_by_id("p")
        p_input.clear()
        p_input.send_keys(self.pwd)
        time.sleep(1)
        self.driver.find_element_by_id("login_button").click()
        time.sleep(2)

        if "tcaptcha_iframe" in self.driver.page_source:
            self.driver.switch_to.frame("tcaptcha_iframe")

        if "拖动下方滑块完成拼图" in self.driver.page_source:
            print("拖动下方滑块完成拼图")

            self.verification_code(23)
        else:
            print("不需要验证码，直接登录")

    def download_img(self, url, pic_type):
        path = self.root + pic_type + '.png'
        try:
            if not os.path.exists(self.root):
                os.makedirs(self.root)
            res = requests.get(url)
            with open(path, "wb") as f:
                f.write(res.content)
            return f.name
        except Exception as e:
            print(e)
            self.download_img(url, pic_type)

    def get_distance(self, small_url, big_url):

        s_img = self.download_img(small_url, 'small')
        time.sleep(2)
        b_img = self.download_img(big_url, 'big')

        target = cv2.imread(s_img, 0)
        template = cv2.imread(b_img, 0)
        w, h = target.shape[::-1]
        temp = self.root + 'temp.jpg'
        targ = self.root + 'targ.jpg'
        cv2.imwrite(temp, template)
        cv2.imwrite(targ, target)
        target = cv2.imread(targ)
        target = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
        target = abs(255 - target)
        cv2.imwrite(targ, target)
        target = cv2.imread(targ)
        template = cv2.imread(temp)
        result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
        x, y = np.unravel_index(result.argmax(), result.shape)
        image = Im.open(b_img)
        xy = (y + 20, x + 20, y + w - 20, x + h - 20)
        imagecrop = image.crop(xy)
        imagecrop.save(self.root + "/new_image.jpg")
        return y

    def verification_code(self, offset):
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame('login_frame')
        self.driver.switch_to.frame(self.driver.find_element_by_id("tcaptcha_iframe"))
        self.driver.find_element_by_id('e_reload').click()

        small_url = self.driver.find_element_by_id('slideBlock').get_attribute('src')
        big_url = self.driver.find_element_by_id('slideBg').get_attribute('src')
        y = self.get_distance(small_url, big_url)

        element = self.driver.find_element_by_id('tcaptcha_drag_button')
        distance = y * (280.0 / 680.0) - offset
        print('distance:', distance)
        has_gone_dist = 0
        remaining_dist = distance
        ActionChains(self.driver).click_and_hold(element).perform()
        time.sleep(0.5)

        steps = self.get_steps(distance)
        for step in steps:
            print(step)
            ActionChains(self.driver).move_by_offset(step, random.randint(-5, 5)).perform()
            time.sleep((random.randint(5, 15) / 1000))

        ActionChains(self.driver).release(on_element=element).perform()

        self.driver.switch_to.parent_frame()
        if self.driver.title != "QQ邮箱":
            try:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame('login_frame')
                self.driver.switch_to.frame("tcaptcha_iframe")
                print(self.driver.find_element_by_id('guideText').text)
                print('滑动失败!')
                self.verification_code(23)
            except Exception as e:
                print(e)
                print('帐号密码有误!')

        else:
            print('登录成功!')
            self.driver.quit()

    def get_steps(self, dis):
        # v=v0+at, s=v0t+½at², v²-v0²=2as
        v = 0
        t = 0.3
        steps = []
        current = 0
        mid = dis / 2
        while current < dis:
            if current < mid:
                a = 2
            else:
                a = -2
            v0 = v
            s = v0 * t + 0.5 * a * (t ** 2)
            current += s
            steps.append(round(s))
            v = v0 + a * t
        return steps


if __name__ == '__main__':
    email = QQEmail("993226448", "23562465")
    email.login_email()
