import sys
import time
from io import BytesIO

import cv2
import os
import requests
import random
import numpy as np
from PIL import Image as Im
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

wait_time_short = 1
wait_time1_long = 2


class QQEmail(object):
    def __init__(self, user, pwd, executable_path):
        self.user = user
        self.pwd = pwd
        self.driver = webdriver.Chrome(service=Service(executable_path))
        self.save_dir = sys.path[0] + "/pic/"

    def login_email(self):
        login_url = "https://mail.qq.com"
        self.driver.get(login_url)
        time.sleep(wait_time1_long)
        self.driver.switch_to.frame("login_frame")
        try:
            self.driver.find_element("switcher_plogin").click()
        except Exception as e:
            print(e)
        time.sleep(wait_time1_long)

        u_input = self.driver.find_element(By.XPATH, '//*[@id="u"]')
        u_input.clear()
        u_input.send_keys(self.user)
        time.sleep(wait_time_short)
        p_input = self.driver.find_element(By.XPATH, '//*[@id="p"]')
        p_input.clear()
        p_input.send_keys(self.pwd)
        time.sleep(wait_time_short)
        self.driver.find_element(By.ID, "login_button").click()
        time.sleep(wait_time1_long)
        if "tcaptcha_iframe_dy" in self.driver.page_source:
            self.driver.switch_to.frame("tcaptcha_iframe_dy")
        if "拖动下方滑块完成拼图" in self.driver.page_source:
            print("需要验证码")
            self.verification_code(60)
        else:
            print("不需要验证码，直接登录")
        time.sleep(10)

    def download_img(self, url, size_type):
        try_times = 3
        path = self.save_dir + size_type + '.png'
        while try_times > 0:
            try:
                if not os.path.exists(self.save_dir):
                    os.makedirs(self.save_dir)
                res = requests.get(url)
                if size_type == "small":
                    img = Im.open(BytesIO(res.content))
                    crop = img.crop((140, 490, 260, 610))
                    crop.save(path)
                    return path
                else:
                    with open(path, "wb") as f:
                        f.write(res.content)
                    return f.name
            except Exception as e:
                print(e)
                try_times -= 1

    def get_distance(self, small_url, big_url):
        s_img = self.download_img(small_url, 'small')
        time.sleep(2)
        b_img = self.download_img(big_url, 'big')
        print("s_img:", s_img)
        print("b_img:", b_img)
        small_pic = cv2.Canny(cv2.GaussianBlur(cv2.imread('pic/small.png'), (5, 5), 0), 100, 300)
        big_pic = cv2.Canny(cv2.GaussianBlur(cv2.imread('pic/big.png'), (5, 5), 0), 100, 300)
        res = cv2.matchTemplate(big_pic, small_pic, cv2.TM_CCOEFF_NORMED)
        x, y = np.unravel_index(res.argmax(), res.shape)
        # min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        # print('max_loc[0]:', max_loc[0])
        return y

    def verification_code(self, offset):
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame('login_frame')
        self.driver.switch_to.frame(self.driver.find_element(By.ID, "tcaptcha_iframe_dy"))
        self.driver.find_element(By.ID, 'e_reload').click()
        time.sleep(wait_time1_long)
        small_pic_pattern = '//*[@id="tcOperation"]/div[8]'
        small_url = self.driver.find_element(By.XPATH, small_pic_pattern).value_of_css_property('background-image')
        small_url = small_url.split('"')[1]
        print("small_url:", small_url)
        big_pic_pattern = '/html/body/div/div[3]/div[2]/div[1]/div[2]/div'
        big_url = self.driver.find_element(By.XPATH, big_pic_pattern).value_of_css_property('background-image')
        big_url = big_url.split('"')[1]
        print(big_url)

        distance = self.get_distance(small_url, big_url)
        distance = (distance - offset) * (280.0 / 680.0)
        print("distance:", distance)
        element = self.driver.find_element(By.XPATH, '//*[@id="tcOperation"]/div[6]')
        ActionChains(self.driver).click_and_hold(element).perform()
        time.sleep(0.5)
        steps = self.get_steps(distance)
        print("steps:", steps)
        for step in steps:
            ActionChains(self.driver).move_by_offset(step, random.randint(-5, 5)).perform()
            time.sleep((random.randint(5, 15) / 1000))

        ActionChains(self.driver).release(on_element=element).perform()
        time.sleep(wait_time1_long)
        self.driver.switch_to.parent_frame()
        time.sleep(wait_time1_long)
        if self.driver.title != "QQ邮箱":
            try:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame('login_frame')
                self.driver.switch_to.frame("tcaptcha_iframe_dy")
                print(self.driver.find_element(By.ID, 'guideText').text)
                print('滑动失败!')
                self.verification_code(60)
            except Exception as e:
                print(e)
                print('帐号密码有误!')

        else:
            print('登录成功!')
            self.driver.quit()

    def get_steps(self, dis):
        # 计算公式：v=v0+at, s=v0t+½at², v²-v0²=2as
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

    def __del__(self):
        if self.driver:
            self.driver.quit()


if __name__ == '__main__':
    driver_path = r"E:\webdriver\chromedriver.exe"
    user_name = '993226449'
    password = '123456789'
    email = QQEmail(user_name, password, driver_path)
    email.login_email()
