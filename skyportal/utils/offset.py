import io
import os
from pathlib import Path
import datetime
import hashlib
import warnings

import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.ndimage.filters import gaussian_filter

from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.gaia import Gaia
from astropy.time import Time
from astropy.utils.exceptions import AstropyWarning

from astropy.wcs import WCS
from astropy.wcs.utils import pixel_to_skycoord
from astropy.io import fits
from astropy.visualization import ImageNormalize, ZScaleInterval
from reproject import reproject_adaptive

warnings.simplefilter('ignore', category=AstropyWarning)

facility_parameters = {
    'Keck': {
        "radius_degrees": 2.0 / 60,
        "mag_limit": 18.5,
        "mag_min": 11.0,
        "min_sep_arcsec": 4.0
    },
    'P200': {
        "radius_degrees": 2.0 / 60,
        "mag_limit": 18.0,
        "mag_min": 10.0,
        "min_sep_arcsec": 5.0
    },
    'Shane': {
        "radius_degrees": 2.5 / 60,
        "mag_limit": 17.0,
        "mag_min": 10.0,
        "min_sep_arcsec": 5.0
    }
}

# ZTF ref grabber URLs. See get_ztfref_url() below
irsa = {
    "url_data": "https://irsa.ipac.caltech.edu/ibe/data/ztf/products/",
    "url_search": "https://irsa.ipac.caltech.edu/ibe/search/ztf/products/",
}


def get_ztfref_url(ra, dec, imsize, *args, **kwargs):
    """
    From:
    https://gist.github.com/dmitryduev/634bd2b21a77e2b1de89e0bfd39d14b9

    Returns the URL that points to the ZTF reference image for the
    requested position

    Parameters
    ----------
    source_ra : float
        Right ascension (J2000) of the source
    source_dec : float
        Declination (J2000) of the source
    imsize : float, optional
        Requested image size (on a size) in arcmin
    *args : optional
        Extra args (not needed here)
    **kwargs : optional
        Extra kwargs (not needed here)

    Returns
    -------
    str
        the URL to download the ZTF image

    """
    imsize_deg = imsize / 60

    url_ref_meta = os.path.join(
        irsa['url_search'],
        f"ref?POS={ra:f},{dec:f}&SIZE={imsize_deg:f}&ct=csv"
    )
    s = requests.get(url_ref_meta).content
    c = pd.read_csv(io.StringIO(s.decode('utf-8')))

    field = f"{c.loc[0, 'field']:06d}"
    filt = c.loc[0, 'filtercode']
    quad = f"{c.loc[0, 'qid']}"
    ccd = f"{c.loc[0, 'ccdid']:02d}"

    path_ursa_ref = os.path.join(
        irsa['url_data'], 'ref',
        field[:3], f'field{field}', filt,
        f'ccd{ccd}', f'q{quad}',
        f'ztf_{field}_{filt}_c{ccd}_q{quad}_refimg.fits'
    )
    return path_ursa_ref


# helper dict for seaching for FITS images from various surveys
source_image_parameters = {
    'desi': {
        'url': (
            'http://legacysurvey.org/viewer/fits-cutout/'
            '?ra={ra}&dec={dec}&layer=dr8&pixscale={pixscale}&bands=r'
        ),
        'npixels': 256,
        'smooth': None,
        'str': 'DESI DR8 R-band'
    },
    'dss': {
        'url': (
            'http://archive.stsci.edu/cgi-bin/dss_search'
            '?v=poss2ukstu_red&r={ra}&dec={dec}&h={imsize}&w={imsize}&e=J2000'
        ),
        'smooth': None,
        'reproject': True,
        'npixels': 500,
        'str': 'DSS-2 Red'
    },
    'ztfref': {
        'url': get_ztfref_url,
        'reproject': True,
        'npixels': 500,
        'smooth': None,
        'str': 'ZTF Ref'
    }
}


def get_nearby_offset_stars(source_ra, source_dec, source_name,
                            how_many=3,
                            radius_degrees=2 / 60.,
                            mag_limit=18.0,
                            mag_min=10.0,
                            min_sep_arcsec=5,
                            starlist_type='Keck',
                            obstime=None,
                            use_source_pos_in_starlist=True,
                            allowed_queries=2,
                            queries_issued=0
                            ):
    """Finds good list of nearby offset stars for spectroscopy
       and returns info about those stars, including their
       offsets calculated to the source of interest

    Parameters
    ----------
    source_ra : float
        Right ascension (J2000) of the source
    source_dec : float
        Declination (J2000) of the source
    source_name : str
        Name of the source
    how_many : int, optional
        How many offset stars to try to find
    radius_degrees : float, optional
        Search radius from the source position in arcmin
    mag_limit : float, optional
        How faint should we search for offset stars?
    mag_min : float, optional
        What is the brightest offset star we will allow?
    min_sep_arcsec : float, optional
        What is the closest offset star allowed to the source?
    starlist_type : str, optional
        What starlist format should we use?
    obstime : str, optional
        What datetime (in isoformat) should we assume for the observation
        (to calculate proper motions)?
    use_source_pos_in_starlist : bool, optional
        Return the source itself for in starlist?
    allowed_queries : int, optional
        How many times should we query (with looser and looser criteria)
        before giving up on getting the number of offset stars we desire?
    queries_issued : int, optional
        How many times have we issued a query? Bookkeeping parameter.

    Returns
    -------
    (list, str, int, int)
        Return a tuple which contains: a list of dictionaries for each object
        in the star list, the query issued, the number of queries issues, and
        the length of the star list (not including the source itself)
    """

    if queries_issued >= allowed_queries:
        raise Exception(
            'Number of offsets queries needed exceeds what is allowed'
        )

    if not obstime:
        source_obstime = Time(datetime.datetime.utcnow().isoformat())
    else:
        # TODO: check the obstime format
        source_obstime = Time(obstime)

    gaia_obstime = "J2015.5"

    center = SkyCoord(source_ra, source_dec, unit=(u.degree, u.degree),
                      frame='icrs', obstime=source_obstime)
    # get three times as many stars as requested for now
    # and go fainter as well
    fainter_diff = 2.0  # mag
    search_multipler = 10
    query_string = f"""
                  SELECT TOP {how_many*search_multipler} DISTANCE(
                    POINT('ICRS', ra, dec),
                    POINT('ICRS', {source_ra}, {source_dec})) AS
                    dist, source_id, ra, dec, ref_epoch,
                    phot_rp_mean_mag, pmra, pmdec, parallax
                  FROM gaiadr2.gaia_source
                  WHERE 1=CONTAINS(
                    POINT('ICRS', ra, dec),
                    CIRCLE('ICRS', {source_ra}, {source_dec},
                           {radius_degrees}))
                  AND phot_rp_mean_mag < {mag_limit + fainter_diff}
                  AND phot_rp_mean_mag > {mag_min}
                  AND parallax < 250
                  ORDER BY phot_rp_mean_mag ASC
                """
    # TODO possibly: save the offset data (cache)
    job = Gaia.launch_job(query_string)
    r = job.get_results()
    queries_issued += 1

    catalog = SkyCoord.guess_from_table(r)

    # star needs to be this far away
    # from another star
    min_sep = min_sep_arcsec * u.arcsec
    good_list = []
    for source in r:
        c = SkyCoord(
            ra=source["ra"], dec=source["dec"],
            unit=(u.degree, u.degree),
            pm_ra_cosdec=(
                np.cos(source["dec"] * np.pi / 180.0) * source['pmra'] * u.mas / u.yr
            ),
            pm_dec=source["pmdec"] * u.mas / u.yr,
            frame='icrs', distance=min(abs(1 / source["parallax"]), 10) * u.kpc,
            obstime=gaia_obstime
        )

        d2d = c.separation(catalog)  # match it to the catalog
        if sum(d2d < min_sep) == 1 and source["phot_rp_mean_mag"] <= mag_limit:
            # this star is not near another star and is bright enough
            # precess it's position forward to the source obstime and
            # get offsets suitable for spectroscopy
            # TODO: put this in geocentric coords to account for parallax
            cprime = c.apply_space_motion(new_obstime=source_obstime)
            dra, ddec = cprime.spherical_offsets_to(center)
            good_list.append(
                (source["dist"], c, source,
                 dra.to(u.arcsec),
                 ddec.to(u.arcsec))
            )

    good_list.sort()

    # if we got less than we asked for, relax the criteria
    if (len(good_list) < how_many) and (queries_issued < allowed_queries):
        return get_nearby_offset_stars(
            source_ra, source_dec, source_name,
            how_many=how_many,
            radius_degrees=radius_degrees*1.3,
            mag_limit=mag_limit+1.0,
            mag_min=mag_min-1.0,
            min_sep_arcsec=min_sep_arcsec/2.0,
            starlist_type=starlist_type,
            obstime=obstime,
            use_source_pos_in_starlist=use_source_pos_in_starlist,
            queries_issued=queries_issued,
            allowed_queries=allowed_queries
        )

    # default to keck star list
    sep = ' '  # 'fromunit'
    commentstr = "#"
    giveoffsets = True
    maxname_size = 16
    # truncate the source_name if we need to
    if len(source_name) > 10:
        basename = source_name[0:3] + ".." + source_name[-6:]
    else:
        basename = source_name

    if starlist_type == 'Keck':
        pass

    elif starlist_type == 'P200':
        sep = ':'  # 'fromunit'
        commentstr = "!"
        giveoffsets = False
        maxname_size = 20

        # truncate the source_name if we need to
        if len(source_name) > 15:
            basename = source_name[0:3] + ".." + source_name[-11:]
        else:
            basename = source_name

    else:
        print("Warning: Do not recognize this starlist format. Using Keck.")

    basename = basename.strip().replace(" ", "")
    space = " "
    star_list_format = (
        f"{basename:{space}<{maxname_size}} "
        + f"{center.to_string('hmsdms', sep=sep, decimal=False, precision=2, alwayssign=True)[1:]}"
        + f" 2000.0 {commentstr}"
    )

    star_list = []
    if use_source_pos_in_starlist:
        star_list.append({"str": star_list_format, "ra": float(source_ra),
                          "dec": float(source_dec), "name": basename})

    for i, (dist, c, source, dra, ddec) in enumerate(good_list[:how_many]):

        dras = f"{dra.value:<0.03f}\" E" if dra > 0 else f"{abs(dra.value):<0.03f}\" W"
        ddecs = f"{ddec.value:<0.03f}\" N" if ddec > 0 else f"{abs(ddec.value):<0.03f}\" S"

        if giveoffsets:
            offsets = \
                f"raoffset={dra.value:<0.03f} decoffset={ddec.value:<0.03f}"
        else:
            offsets = ""

        name = f"{basename}_off{i+1}"

        star_list_format = (
            f"{name:{space}<{maxname_size}} "
            + f"{c.to_string('hmsdms', sep=sep, decimal=False, precision=2, alwayssign=True)[1:]}"
            + f" 2000.0 {offsets} "
            + f" {commentstr} dist={3600*dist:<0.02f}\"; {source['phot_rp_mean_mag']:<0.02f} mag"
            + f"; {dras}, {ddecs} "
            + f" ID={source['source_id']}"
        )

        star_list.append(
            {
                "str": star_list_format, "ra": float(source["ra"]),
                "dec": float(source["dec"]), "name": name, "dras": dras,
                "ddecs": ddecs, "mag": float(source["phot_rp_mean_mag"])
            }
        )

    # send back the starlist in
    return (star_list, query_string.replace("\n", " "),
            queries_issued, len(star_list) - 1)


def fits_image(center_ra, center_dec, imsize=4.0, image_source="desi",
               cache=True, cachedir="./skyportal_image_cache/",
               max_cache=5):

    """Returns an opened FITS image centered on the source
       of the requested size.

    Parameters
    ----------
    source_ra : float
        Right ascension (J2000) of the source
    source_dec : float
        Declination (J2000) of the source
    imsize : float, optional
        Requested image size (on a size) in arcmin
    image_source : str, optional
        Survey where the image comes from "desi" or "dss" (more to be added)
    cache : bool, optional
        Use a cache version of the image and save to a cache if True
    cachedir : str, optional
        Where should the cache live?
    max_cache : int, optional
        How many older files in the cache should we keep?

    Returns
    -------
    object
        Either a pyfits HDU object or None. If no suitable image is found
        then None is returned. The caller of `fits_image` will need to
        handle this case.
    """

    if image_source not in source_image_parameters:
        raise Exception("do not know how to grab image source")

    pixscale = \
        60*imsize/source_image_parameters[image_source].get("npixels", 256)

    if isinstance(source_image_parameters[image_source]["url"], str):
        url = source_image_parameters[image_source]["url"].format(
            ra=center_ra, dec=center_dec, pixscale=pixscale, imsize=imsize)
    else:
        # use the URL field as a function
        url = source_image_parameters[image_source]["url"](
                       ra=center_ra,
                       dec=center_dec,
                       imsize=imsize)

    cachedir = Path(cachedir)
    if not cachedir.is_dir():
        cachedir.mkdir()

    def get_hdu(url):
        response = requests.get(url, stream=True, allow_redirects=True)
        if response.status_code == 200:
            hdu = fits.open(io.BytesIO(response.content))[0]
            return hdu
        else:
            return None

    if cache:
        m = hashlib.md5()
        m.update(
            f"{center_ra}{center_dec}{imsize}{image_source}".encode('utf-8'))
        hash_name = "image" + m.hexdigest()
        image_file = cachedir / hash_name
        if image_file.exists():
            print("Opening cached image")
            image_file.touch()
            hdu = fits.open(image_file)[0]
        else:
            hdu = get_hdu(url)
            if np.count_nonzero(hdu.data) > 0:
                hdu.writeto(image_file)
            else:
                hdu = None

        if max_cache > 1:
            cached_files = []
            for item in Path(cachedir).glob('*'):
                if item.is_file():
                    cached_files.append((item.stat().st_mtime, item.name))
            if len(cached_files) > max_cache:
                for t, f in cached_files[-max_cache:]:
                    try:
                        os.remove(cachedir / f)
                    except FileNotFoundError:
                        pass
    else:
        hdu = get_hdu(url)
        if np.count_nonzero(hdu.data) > 0:
            hdu = None

    return hdu


def get_finding_chart(source_ra, source_dec, source_name,
                      image_source='desi',
                      output_format='pdf',
                      imsize=3.0,
                      tick_offset=0.02,
                      tick_length=0.03,
                      fallback_image_source='dss',
                      **offset_star_kwargs):

    """Create a finder chart suitable for spectroscopic observations of
       the source

    Parameters
    ----------
    source_ra : float
        Right ascension (J2000) of the source
    source_dec : float
        Declination (J2000) of the source
    source_name : str
        Name of the source
    image_source : {'desi', 'dss', 'ztfref'}, optional
        Survey where the image comes from "desi", "dss", "ztfref"
        (more to be added)
    output_format : str, optional
        "pdf" of "png" -- determines the format of the returned finder
    imsize : float, optional
        Requested image size (on a size) in arcmin. Should be between 2-15.
    tick_offset : float, optional
        How far off the each source should the tick mark be made? (in arcsec)
    tick_length : float, optional
        How long should the tick mark be made? (in arcsec)
    fallback_image_source : str, optional
        Where what `image_source` should we fall back to if the
        one requested fails
    **offset_star_kwargs : dict, optional
        Other parameters passed to `get_nearby_offset_stars`

    Returns
    -------
    dict
        success : bool
            Whether the request was successful or not, returning
            a sensible error in 'reason'
        name : str
            suggested filename based on `source_name` and `output_format`
        data : str
            binary encoded data for the image (to be streamed)
        reason : str
            If not successful, a reason is returned.
    """
    if (imsize < 2.0) or (imsize > 15):
        return {
            'success': False,
            'reason': 'Requested `imsize` out of range',
            'data': '',
            'name': ''
        }

    if image_source not in source_image_parameters:
        return {
            'success': False,
            'reason': f'image source {image_source} not in list',
            'data': '',
            'name': ''
        }

    fig = plt.figure(figsize=(11, 8.5), constrained_layout=False)
    widths = [2.6, 1]
    heights = [2.6, 1]
    spec = fig.add_gridspec(ncols=2, nrows=2, width_ratios=widths,
                            height_ratios=heights, left=0.05, right=0.95)

    # how wide on the side will the image be? 256 as default
    npixels = source_image_parameters[image_source].get("npixels", 256)
    # set the pixelscale in arcsec (typically about 1 arcsec/pixel)
    pixscale = 60*imsize/npixels

    hdu = fits_image(source_ra, source_dec, imsize=imsize,
                     image_source=image_source)

    # skeleton WCS - this is the field that the user requested
    wcs = WCS(naxis=2)

    # set the headers of the WCS.
    # The center of the image is the reference point (source_ra, source_dec):
    wcs.wcs.crpix = [npixels/2, npixels/2]
    wcs.wcs.crval = [source_ra, source_dec]

    # create the pixel scale and orientation North up, East left
    # pixelscale is in degrees, established in the tangent plane
    # to the reference point
    wcs.wcs.cd = np.array([[-pixscale/3600, 0], [0, pixscale/3600]])
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]

    if hdu is not None:
        im = hdu.data

        # replace the nans with medians
        im[np.isnan(im)] = np.nanmedian(im)
        if source_image_parameters[image_source].get("reproject", False):
            # project image to the skeleton WCS solution
            print("Reprojecting image to requested position and orientation")
            im, _ = reproject_adaptive(hdu, wcs, shape_out=(npixels, npixels))
        else:
            wcs = WCS(hdu.header)

        if source_image_parameters[image_source].get("smooth", False):
            im = gaussian_filter(
                    hdu.data,
                    source_image_parameters[image_source]["smooth"]/pixscale
                 )

        norm = ImageNormalize(im, interval=ZScaleInterval())
        watermark = source_image_parameters[image_source]["str"]

    else:
        # if we got back a blank image, try to fallback on another survey
        # and return the results from that call
        if (fallback_image_source is not None):
            if (fallback_image_source != image_source):
                print(f"Falling back on image source {fallback_image_source}")
                return get_finding_chart(source_ra, source_dec, source_name,
                                         image_source=fallback_image_source,
                                         output_format=output_format,
                                         imsize=imsize,
                                         tick_offset=tick_offset,
                                         tick_length=tick_length,
                                         fallback_image_source=None,
                                         **offset_star_kwargs)

        # we dont have an image here, so let's create a dummy one
        # so we can still plot
        im = np.zeros((npixels, npixels))
        norm = None
        watermark = None

    # add the images in the top left corner
    ax = fig.add_subplot(spec[0, 0], projection=wcs)
    ax_text = fig.add_subplot(spec[0, 1])
    ax_text.axis('off')
    ax_starlist = fig.add_subplot(spec[1, 0:])
    ax_starlist.axis('off')

    ax.imshow(im, origin='lower', norm=norm, cmap='gray_r')
    ax.set_autoscale_on(False)
    ax.grid(color='white', ls='dotted')
    ax.set_xlabel(r'$\alpha$ (J2000)', fontsize='large')
    ax.set_ylabel(r'$\delta$ (J2000)', fontsize='large')
    obstime = offset_star_kwargs.get(
            "obstime", datetime.datetime.utcnow().isoformat()
            )
    ax.set_title(f'{source_name} Finder ({obstime})',
                 fontsize='large', fontweight='bold')

    star_list, _, _, _ = get_nearby_offset_stars(source_ra, source_dec,
                                                 source_name,
                                                 **offset_star_kwargs)

    if not isinstance(star_list, list) or len(star_list) == 0:
        return {
            'success': False,
            'reason': 'failure to get star list',
            'data': '',
            'name': ''
        }

    ncolors = len(star_list)
    colors = sns.color_palette("colorblind", ncolors)

    start_text = [-0.35, 0.99]
    starlist_str = (
        "# Note: spacing in starlist many not copy/paste correctly in PDF\n"
        + f"#       you can get starlist directly from"
        + f" /api/{source_name}/offsets?"
        + f"facility={offset_star_kwargs.get('facility', 'Keck')}\n"
        + "\n".join([x["str"] for x in star_list])
    )

    # add the starlist
    ax_starlist.text(0, 0.50, starlist_str,
                     fontsize="x-small", family='monospace',
                     transform=ax_starlist.transAxes)

    # add the watermark for the survey
    props = dict(boxstyle='round', facecolor='gray', alpha=0.5)

    if watermark is not None:
        ax.text(0.035, 0.035, watermark,
                horizontalalignment='left',
                verticalalignment='center',
                transform=ax.transAxes, fontsize='medium', fontweight='bold',
                color="yellow", alpha=0.5, bbox=props)

    ax.text(0.95, 0.035,
            f"{imsize}\u2032 \u00D7 {imsize}\u2032",  # size'x size'
            horizontalalignment='right',
            verticalalignment='center',
            transform=ax.transAxes, fontsize='medium', fontweight='bold',
            color="yellow", alpha=0.5, bbox=props)

    # compass rose
    # rose_center_pixel = ax.transAxes.transform((0.04, 0.95))
    rose_center = pixel_to_skycoord(int(npixels*0.1), int(npixels*0.9), wcs)
    props = dict(boxstyle='round', facecolor='gray', alpha=0.5)

    for ang, label, off in [(0, "N", 0.01), (90, "E", 0.03)]:
        position_angle = ang * u.deg
        separation = (0.05*imsize*60) * u.arcsec  # 5%
        p2 = rose_center.directional_offset_by(position_angle, separation)
        ax.plot([rose_center.ra.value, p2.ra.value],
                [rose_center.dec.value, p2.dec.value],
                transform=ax.get_transform('world'), color="gold",
                linewidth=2)

        # label N and E
        position_angle = (ang + 15) * u.deg
        separation = ((0.05 + off)*imsize*60) * u.arcsec
        p2 = rose_center.directional_offset_by(position_angle, separation)
        ax.text(p2.ra.value, p2.dec.value, label, color="gold",
                transform=ax.get_transform('world'),
                fontsize='large', fontweight='bold')

    for i, star in enumerate(star_list):

        c1 = SkyCoord(star["ra"]*u.deg, star["dec"]*u.deg, frame='icrs')

        # mark up the right side of the page with position and offset info
        name_title = star["name"]
        if star.get("mag") is not None:
            name_title += f", mag={star.get('mag'):.2f}"
        ax_text.text(start_text[0], start_text[1]-i/ncolors, name_title,
                     ha='left', va='top', fontsize='large', fontweight='bold',
                     transform=ax_text.transAxes, color=colors[i])
        source_text = f"  {star['ra']:.5f} {star['dec']:.5f}\n"
        source_text += f"  {c1.to_string('hmsdms')}\n"
        if (star.get("dras") is not None) and (star.get("ddecs") is not None):
            source_text += \
               f'  {star.get("dras")} {star.get("ddecs")} to {source_name}'
        ax_text.text(start_text[0], start_text[1]-i/ncolors - 0.06,
                     source_text,
                     ha='left', va='top', fontsize='large',
                     transform=ax_text.transAxes, color=colors[i])

        # work on making marks where the stars are
        for ang in [0, 90]:
            position_angle = ang * u.deg
            separation = (tick_offset*imsize*60) * u.arcsec
            p1 = c1.directional_offset_by(position_angle, separation)
            separation = (tick_offset + tick_length) * imsize * 60 * u.arcsec
            p2 = c1.directional_offset_by(position_angle, separation)
            ax.plot([p1.ra.value, p2.ra.value], [p1.dec.value, p2.dec.value],
                    transform=ax.get_transform('world'), color=colors[i],
                    linewidth=3 if imsize <= 4 else 2)
        if star["name"].find("_off") != -1:
            # this is an offset star
            text = star["name"].split("_off")[-1]
            position_angle = 14 * u.deg
            separation = \
                (tick_offset + tick_length*1.6) * imsize * 60 * u.arcsec
            p1 = c1.directional_offset_by(position_angle, separation)
            ax.text(p1.ra.value, p1.dec.value, text, color=colors[i],
                    transform=ax.get_transform('world'),
                    fontsize='large', fontweight='bold')

    buf = io.BytesIO()
    fig.savefig(buf, format=output_format)
    buf.seek(0)

    return {
        "success": True,
        "name": f"finder_{source_name}.{output_format}",
        "data": buf.read(),
        "reason": ""
    }
