import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

import skyportal


def test_source_list(driver, user, public_source, private_source):
    driver.get(f"/become_user/{user.id}")  # TODO decorator/context manager?
    assert 'localhost' in driver.current_url
    simbad_class = public_source.other_metadata['simbad_class']
    driver.get('/')
    driver.wait_for_xpath("//div[contains(@title,'connected')]")
    driver.wait_for_xpath('//h2[contains(text(), "Sources")]')
    driver.wait_for_xpath(f'//a[text()="{public_source.id}"]')
    driver.wait_for_xpath(f'//td[text()="{simbad_class}"]')
    driver.wait_for_xpath_missing(f'//a[text()="{private_source.id}"]')
    el = driver.wait_for_xpath('//button[text()="View Next 100 Sources"]')
    assert not el.is_enabled()
    el = driver.wait_for_xpath('//button[text()="View Previous 100 Sources"]')
    assert not el.is_enabled()


def test_source_filtering_and_pagination(driver, user, public_sources_205):
    driver.get(f"/become_user/{user.id}")  # TODO decorator/context manager?
    assert 'localhost' in driver.current_url
    simbad_class = public_sources_205[0].other_metadata['simbad_class']
    driver.get('/')
    driver.wait_for_xpath("//div[contains(@title,'connected')]")
    driver.wait_for_xpath('//h2[contains(text(), "Sources")]')
    driver.wait_for_xpath(f'//td[text()="{simbad_class}"]')
    # Pagination
    next_button = driver.wait_for_xpath('//button[text()="View Next 100 Sources"]')
    assert next_button.is_enabled()
    prev_button = driver.wait_for_xpath('//button[text()="View Previous 100 Sources"]')
    assert not prev_button.is_enabled()
    next_button.click()
    time.sleep(1)
    assert prev_button.is_enabled()
    next_button.click()
    time.sleep(1)
    assert not next_button.is_enabled()
    prev_button.click()
    time.sleep(1)
    assert next_button.is_enabled()
    prev_button.click()
    time.sleep(1)
    assert not prev_button.is_enabled()
    # Source filtering
    assert next_button.is_enabled()
    source_id = driver.wait_for_xpath("//input[@name='sourceID']")
    source_id.send_keys('aa')
    submit = driver.wait_for_xpath("//input[@type='submit']")
    submit.click()
    time.sleep(1)
    assert not next_button.is_enabled()


def test_skyportal_version_displayed(driver):
    driver.get('/')
    driver.wait_for_xpath(f"//div[contains(.,'SkyPortal v{skyportal.__version__}')]")
