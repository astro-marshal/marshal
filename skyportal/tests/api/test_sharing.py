from skyportal.tests import api


def test_sharing_photometry(
    upload_data_token_two_groups,
    public_source_two_groups,
    public_group,
    public_group2,
    view_only_token,
    ztf_camera,
):
    upload_data_token = upload_data_token_two_groups
    public_source = public_source_two_groups
    status, data = api(
        "POST",
        "photometry",
        data={
            "obj_id": str(public_source.id),
            "mjd": 58000.0,
            "instrument_id": ztf_camera.id,
            "flux": 12.24,
            "fluxerr": 0.031,
            "zp": 25.0,
            "magsys": "ab",
            "filter": "ztfg",
            "group_ids": [public_group2.id],
        },
        token=upload_data_token,
    )
    assert status == 200
    assert data["status"] == "success"

    photometry_id = data["data"]["ids"][0]
    status, data = api(
        "GET", f"photometry/{photometry_id}?format=flux", token=upload_data_token
    )
    assert status == 200
    assert data["status"] == "success"

    status, data = api(
        "GET", f"photometry/{photometry_id}?format=flux", token=view_only_token
    )
    # `view_only_token only` belongs to `public_group`, but not `public_group2`
    assert status == 400
    assert data["status"] == "error"
    assert "Insufficient permissions" in data["message"]

    status, data = api(
        "POST",
        "sharing",
        data={
            "IDs": [photometry_id],
            "dataType": "Photometry",
            "groupIDs": [public_group.id],
        },
        token=upload_data_token,
    )

    status, data = api(
        "GET", f"photometry/{photometry_id}?format=flux", token=view_only_token
    )
    # `view_only_token only` belongs to `public_group`, but not `public_group2`
    assert status == 200
    assert data["status"] == "success"
    assert data["data"]["obj_id"] == public_source.id
