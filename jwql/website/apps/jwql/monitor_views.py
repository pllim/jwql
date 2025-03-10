"""Defines the views for the ``jwql`` web app instrument monitors.

Authors
-------

    - Lauren Chambers
    - Maria Pena-Guerrero

Use
---

    This module is called in ``urls.py`` as such:
    ::

        from django.urls import path
        from . import monitor_views
        urlpatterns = [path('web/path/to/view/', monitor_views.view_name,
        name='view_name')]

References
----------
    For more information please see:
        ``https://docs.djangoproject.com/en/2.0/topics/http/views/``

Dependencies
------------
    The user must have a configuration file named ``config.json``
    placed in the ``jwql`` directory.
"""

import os

from astropy.time import Time
from bokeh.resources import CDN, INLINE
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
import json
import pandas as pd

from . import bokeh_containers
from jwql.website.apps.jwql import bokeh_containers
from jwql.website.apps.jwql.monitor_models.claw import NIRCamClawStats
from jwql.website.apps.jwql.monitor_pages.monitor_readnoise_bokeh import ReadNoiseFigure
from jwql.utils.constants import JWST_INSTRUMENT_NAMES_MIXEDCASE
from jwql.utils.utils import get_config, get_base_url
from jwql.instrument_monitors.nirspec_monitors.ta_monitors import msata_monitor
from jwql.instrument_monitors.nirspec_monitors.ta_monitors import wata_monitor
from jwql.utils import monitor_utils


CONFIG = get_config()
FILESYSTEM_DIR = os.path.join(CONFIG['jwql_dir'], 'filesystem')


def background_monitor(request):
    """Generate the NIRCam background monitor page

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage

    Returns
    -------
    HttpResponse object
        Outgoing response sent to the webpage
    """

    template = "background_monitor.html"

    # Get the background trending filters to display
    output_dir_bkg = static(os.path.join("outputs", "claw_monitor", "backgrounds"))
    fltrs = ['F070W', 'F090W', 'F115W', 'F150W', 'F200W', 'F277W', 'F356W', 'F444W']
    bkg_plots = [os.path.join(output_dir_bkg, '{}_backgrounds.png'.format(fltr)) for fltr in fltrs]
    bkg_rms_plots = [os.path.join(output_dir_bkg, '{}_backgrounds_rms.png'.format(fltr)) for fltr in fltrs]
    bkg_model_plots = [os.path.join(output_dir_bkg, '{}_backgrounds_vs_models.png'.format(fltr)) for fltr in fltrs]

    context = {
        'inst': 'NIRCam',
        'bkg_plots': bkg_plots,
        'bkg_rms_plots': bkg_rms_plots,
        'bkg_model_plots': bkg_model_plots
    }

    # Return a HTTP response with the template and dictionary of variables
    return render(request, template, context)


def bad_pixel_monitor(request, inst):
    """Generate the bad pixel monitor page for a given instrument

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage
    inst : str
        Name of JWST instrument

    Returns
    -------
    HttpResponse object
        Outgoing response sent to the webpage
    """
    # Locate the html file for the instrument
    template = f"{inst.lower()}_bad_pix_plots.html"

    context = {
        'inst': inst,
    }

    return render(request, template, context)


def bias_monitor(request, inst):
    """Generate the bias monitor page for a given instrument

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage
    inst : str
        Name of JWST instrument

    Returns
    -------
    HttpResponse object
        Outgoing response sent to the webpage
    """

    # Ensure the instrument is correctly capitalized
    inst = JWST_INSTRUMENT_NAMES_MIXEDCASE[inst.lower()]
    template = f"{inst.lower()}_bias_plots.html"

    context = {
        'inst': inst,
    }

    # Return a HTTP response with the template and dictionary of variables
    return render(request, template, context)


def claw_monitor(request):
    """Generate the NIRCam claw monitor page

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage

    Returns
    -------
    HttpResponse object
        Outgoing response sent to the webpage
    """

    template = "claw_monitor.html"

    # Get all recent claw stack images from the last 10 days
    query = NIRCamClawStats.objects.filter(expstart_mjd__gte=(Time.now().mjd - 10))
    query = query.order_by('-expstart_mjd').all().values('skyflat_filename')
    recent_files = list(pd.unique(pd.DataFrame.from_records(query)['skyflat_filename']))
    output_dir_claws = static(os.path.join("outputs", "claw_monitor", "claw_stacks"))
    claw_stacks = [os.path.join(output_dir_claws, filename) for filename in recent_files]

    context = {
        'inst': 'NIRCam',
        'claw_stacks': claw_stacks
    }

    # Return a HTTP response with the template and dictionary of variables
    return render(request, template, context)


def cosmic_ray_monitor(request, inst):
    """Generate the cosmic ray monitor page for a given instrument

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage
    inst : str
        Name of JWST instrument
    Returns
    -------
    HttpResponse object
        Outgoing response sent to the webpage
    """

    # Ensure the instrument is correctly capitalized
    inst = inst.upper()

    tabs_components = bokeh_containers.cosmic_ray_monitor_tabs(inst)

    template = "cosmic_ray_monitor.html"

    context = {
        'inst': inst,
        'tabs_components': tabs_components,
    }

    # Return a HTTP response with the template and dictionary of variables
    return render(request, template, context)


def dark_monitor(request, inst):
    """Generate the dark monitor page for a given instrument

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage
    inst : str
        Name of JWST instrument

    Returns
    -------
    HttpResponse object
        Outgoing response sent to the webpage
    """

    # Ensure the instrument is correctly capitalized
    inst = JWST_INSTRUMENT_NAMES_MIXEDCASE[inst.lower()]

    tabs_components = bokeh_containers.dark_monitor_tabs(inst)

    template = "dark_monitor.html"

    context = {
        'inst': inst,
        'tabs_components': tabs_components,
    }

    # Return a HTTP response with the template and dictionary of variables
    return render(request, template, context)


def edb_monitor(request, inst):
    """Generate the EDB telemetry monitor page for a given instrument

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage

    inst : str
        Name of JWST instrument

    Returns
    -------
    HttpResponse object
        Outgoing response sent to the webpage
    """
    inst = inst.lower()
    plot_dir = os.path.join(CONFIG["outputs"], "edb_telemetry_monitor", inst)
    json_file = f'edb_{inst}_tabbed_plots.json'

    # Get the json data that contains the tabbed plots
    with open(os.path.join(plot_dir, json_file), 'r') as fp:
        data = json.dumps(json.loads(fp.read()))

    template = "edb_monitor.html"

    context = {
        'inst': JWST_INSTRUMENT_NAMES_MIXEDCASE[inst],
        'json_object': data,
        'resources': CDN.render()
    }

    # Return a HTTP response with the template and dictionary of variables
    return render(request, template, context)


def readnoise_monitor(request, inst):
    """Generate the readnoise monitor page for a given instrument

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage
    inst : str
        Name of JWST instrument

    Returns
    -------
    HttpResponse object
        Outgoing response sent to the webpage
    """

    # Ensure the instrument is correctly capitalized
    inst = JWST_INSTRUMENT_NAMES_MIXEDCASE[inst.lower()]

    # Get the html and JS needed to render the readnoise tab plots
    tabs_components = ReadNoiseFigure(inst).tab_components

    template = "readnoise_monitor.html"

    context = {
        'inst': inst,
        'tabs_components': tabs_components,
    }

    # Return a HTTP response with the template and dictionary of variables
    return render(request, template, context)


def msata_monitoring(request):
    """Container for MSATA monitor

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage

    Returns
    -------
    HttpResponse object
        Outgoing response sent to the webpage
    """
    # get the template and embed the plots
    template = "msata_monitor.html"

    context = {
        'inst': 'NIRSpec',
        'base_url': get_base_url()
    }

    # Return a HTTP response with the template and dictionary of variables
    return render(request, template, context)


def msata_monitoring_ajax(request):
    """Generate the MSATA monitor results to display in the monitor page

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage

    Returns
    -------
    JsonResponse object
        Outgoing response sent to the webpage
    """
    # Make plots and extract visualization components
    monitor = msata_monitor.MSATA()
    monitor.plots_for_app()

    context = {'script': monitor.script,
               'div': monitor.div}

    return JsonResponse(context, json_dumps_params={'indent': 2})


def wata_monitoring(request):
    """Container for WATA monitor

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage

    Returns
    -------
    HttpResponse object
        Outgoing response sent to the webpage
    """
    # get the template and embed the plots
    template = "wata_monitor.html"

    context = {
        'inst': 'NIRSpec',
        'base_url': get_base_url()
    }

    # Return a HTTP response with the template and dictionary of variables
    return render(request, template, context)


def wata_monitoring_ajax(request):
    """Generate the WATA monitor results to display in the monitor page

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage

    Returns
    -------
    JsonResponse object
        Outgoing response sent to the webpage
    """
    # Make plots and extract visualization components
    monitor = wata_monitor.WATA()
    monitor.plots_for_app()

    context = {'script': monitor.script,
               'div': monitor.div}

    return JsonResponse(context, json_dumps_params={'indent': 2})
