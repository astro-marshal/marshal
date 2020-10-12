import uuid

from .. import api
from selenium.common.exceptions import TimeoutException

from tdtax import taxonomy, __version__

from datetime import datetime, timezone


def test_add_new_source_renders_on_group_sources_page(
    driver,
    super_admin_user,
    public_group,
    upload_data_token,
    taxonomy_token,
    classification_token,
):

    driver.get(f"/become_user/{super_admin_user.id}")  # become a super-user

    obj_id = str(uuid.uuid4())

    t0 = datetime.now(timezone.utc)

    # upload a new source, saved to the public group
    status, data = api(
        'POST',
        'sources',
        data={
            'id': f'{obj_id}',
            'ra': 234.22,
            'dec': -22.33,
            'redshift': 3,
            'altdata': {'simbad': {'class': 'RRLyr'}},
            'transient': False,
            'ra_dis': 2.3,
            'group_ids': [public_group.id],
        },
        token=upload_data_token,
    )
    assert status == 200
    assert data['data']['id'] == f'{obj_id}'

    # go to the group sources page
    driver.get(f"/group_sources/{public_group.id}")

    # make sure the group name appears
    driver.wait_for_xpath(f"//*[text()[contains(., '{public_group.name}')]]")

    # find the name of the newly added source
    driver.wait_for_xpath(f"//a[contains(@href, '/source/{obj_id}')]")

    # find the date it was saved
    driver.wait_for_xpath(
        f"//*[text()[contains(., '{t0.strftime('%Y-%m-%dT%H:%M:%S')}')]]"
    )

    # little triangle you push to expand the table
    expand_button = driver.wait_for_xpath("//*[@id='expandable-button']")
    driver.scroll_to_element_and_click(expand_button)

    # make sure the div containing the individual source appears
    driver.wait_for_xpath("//div[@class='MuiGrid-root MuiGrid-item']")

    try:  # the vega plot may take some time to appear, and in the meanwhile the MUI drawer gets closed for some reason.
        driver.wait_for_xpath(
            "//*[@class='vega-embed']"
        )  # make sure the table row opens up and show the vega plot
    except TimeoutException:
        # try again to click this triangle thingy to open the drawer
        expand_button = driver.wait_for_xpath("//*[@id='expandable-button']")
        driver.scroll_to_element_and_click(expand_button)

        # with the drawer opened again, it should now work...
        driver.wait_for_xpath(
            "//*[@class='vega-embed']"
        )  # make sure the table row opens up and show the vega plot

    # post a taxonomy and classification
    status, data = api(
        'POST',
        'taxonomy',
        data={
            'name': "test taxonomy" + str(uuid.uuid4()),
            'hierarchy': taxonomy,
            'group_ids': [public_group.id],
            'provenance': f"tdtax_{__version__}",
            'version': __version__,
            'isLatest': True,
        },
        token=taxonomy_token,
    )
    assert status == 200
    taxonomy_id = data['data']['taxonomy_id']

    status, data = api(
        'POST',
        'classification',
        data={
            'obj_id': obj_id,
            'classification': 'Algol',
            'taxonomy_id': taxonomy_id,
            'probability': 1.0,
            'group_ids': [public_group.id],
        },
        token=classification_token,
    )
    assert status == 200

    # go to the group sources page
    # driver.get(f"/group_sources/{public_group.id}")

    # check the classification shows up
    driver.wait_for_xpath(f"//*[text()[contains(., '{'Algol'}')]]")
