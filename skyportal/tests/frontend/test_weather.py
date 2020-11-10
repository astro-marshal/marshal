import uuid
import pytest
from skyportal.tests import api


@pytest.mark.flaky(reruns=2)
def test_weather_widget(driver, user, public_group, upload_data_token, p60_telescope):
    name = str(uuid.uuid4())
    post_data = {
        'name': name,
        'nickname': name,
        'lat': 0.0,
        'lon': 0.0,
        'elevation': 0.0,
        'diameter': 10.0,
        'skycam_link': 'http://www.lulin.ncu.edu.tw/wea/cur_sky.jpg',
        'weather_link': 'http://www.lulin.ncu.edu.tw/',
        'robotic': True,
    }

    status, data = api('POST', 'telescope', data=post_data, token=upload_data_token)
    assert status == 200
    assert data['status'] == 'success'

    driver.get(f'/become_user/{user.id}')
    driver.get('/')

    driver.click_xpath('//*[@data-testid="tel-list-button"]')
    driver.click_xpath(f'//*[text()="{p60_telescope.name}"]')
    driver.wait_for_xpath(f'//h6[text()="{p60_telescope.name}"]')
