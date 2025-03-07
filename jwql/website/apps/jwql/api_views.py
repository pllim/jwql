"""Defines the views for the ``jwql`` REST API.

The functions within serve as views for the ``jwql`` REST API.
Currently, the following services are available:

    - Return a list of all proposals (``api/proposals/``)
    - Return a list of proposals for a given instrument (``/api/<instrument>/proposals/``)
    - Return a list of filenames for a given proposal (``/api/<proposal>/filenames/``)
    - Return a list of filenames for a given rootname (``/api/<rootname>/filenames/``)
    - Return a list of preview images for a given instrument (``/api/<instrument>/preview_images/``)
    - Return a list of preview images for a given proposal (``/api/<proposal>/preview_images/``)
    - Return a list of preview images for a given rootname (``/api/<rootname>/preview_images/``)
    - Return a list of thumbnails for a given instrument (``/api/<instrument>/thumbnails/``)
    - Return a list of thumbnails for a given proposal (``/api/<proposal>/thumbnails/``)
    - Return a list of thumbnails for a given rootname (``/api/<rootname>/thumbnails/``)

Where ``<instrument>`` is the instrument of interest (e.g. ``NIRCam``),
``<proposal>`` is the five-digit proposal number of interest (e.g.
``86600``), and ``<rootname>`` is the rootname of interest (e.g.
``jw86600008001_02101_00007_guider2``).  Note that ``<rootname>`` need
not be the full rootname, but can be any shortened version, (e.g.
``jw8660000801_02101``, or ``jw8660``); using an abbreviated version
will return all filenames associated with the rootname up to that point.

Authors
-------

    - Matthew Bourque
    - Teagan King
    - Melanie Clarke

Use
---

    This module is called in ``urls.py`` as such:
    ::

        from django.urls import path
        from . import api_views
        urlpatterns = [path('web/path/to/view/', api_views.view_name, name='view_name')]

References
----------
    For more information please see:
        ``https://docs.djangoproject.com/en/2.0/topics/http/views/``
"""

from django.http import JsonResponse

from .data_containers import get_all_proposals
from .data_containers import get_filenames_by_proposal
from .data_containers import get_filenames_by_rootname
from .data_containers import get_instrument_proposals
from .data_containers import get_instrument_looks
from .data_containers import get_preview_images_by_proposal
from .data_containers import get_preview_images_by_rootname
from .data_containers import get_thumbnails_by_proposal
from .data_containers import get_thumbnail_by_rootname


def all_proposals(request):
    """Return a list of proposals for the mission

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage

    Returns
    -------
    JsonResponse object
        Outgoing response sent to the webpage
    """

    proposals = get_all_proposals()
    return JsonResponse({'proposals': proposals}, json_dumps_params={'indent': 2})


def filenames_by_proposal(request, proposal):
    """Return a list of filenames for the given ``proposal``

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage
    proposal : str
        The five-digit proposal number (e.g. ``88600``)

    Returns
    -------
    JsonResponse object
        Outgoing response sent to the webpage
    """

    filenames = get_filenames_by_proposal(proposal)
    return JsonResponse({'filenames': filenames}, json_dumps_params={'indent': 2})


def filenames_by_rootname(request, rootname):
    """Return a list of filenames for the given ``rootname``

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage
    rootname : str
        The rootname of interest (e.g. ``jw86600008001_02101_00007_guider2``).

    Returns
    -------
    JsonResponse object
        Outgoing response sent to the webpage
    """

    filenames = get_filenames_by_rootname(rootname)
    return JsonResponse({'filenames': filenames}, json_dumps_params={'indent': 2})


def instrument_proposals(request, inst):
    """Return a list of proposals for the given instrument

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage
    inst : str
        The instrument of interest.  The name of the instrument must
        mach one of the following: (``nircam``, ``NIRCam``, ``niriss``,
        ``NIRISS``, ``nirspec``, ``NIRSpec``, ``miri``, ``MIRI``,
        ``fgs``, ``FGS``).

    Returns
    -------
    JsonResponse object
        Outgoing response sent to the webpage
    """

    proposals = get_instrument_proposals(inst)
    return JsonResponse({'proposals': proposals}, json_dumps_params={'indent': 2})


def instrument_looks(request, inst, status=None):
    """Return a table of looks information for the given instrument.

    'Viewed' indicates whether an observation is new or has been reviewed
    for QA.  In addition to 'filename', and 'viewed', observation
    descriptors from the Django models may be added to the table. Keys
    are specified by instrument in the REPORT_KEYS_PER_INSTRUMENT constant.

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage.
    inst : str
        The JWST instrument of interest.
    status : str, optional
        If set to None, all viewed values are returned. If set to
        'viewed', only viewed data is returned. If set to 'new', only
        new data is returned.

    Returns
    -------
    JsonResponse
        Outgoing response sent to the webpage, depending on return_type.
    """
    # get all observation looks from file info model
    # and join with observation descriptors
    keys, looks = get_instrument_looks(inst, look=status)

    # return results by api key
    if status is None:
        status = 'looks'

    response = JsonResponse({'instrument': inst,
                             'keys': keys,
                             'type': status,
                             status: looks},
                            json_dumps_params={'indent': 2})
    return response


def preview_images_by_proposal(request, proposal):
    """Return a list of available preview images in the filesystem for
    the given ``proposal``.

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage
    proposal : str
        The five-digit proposal number (e.g. ``88600``)

    Returns
    -------
    JsonResponse object
        Outgoing response sent to the webpage
    """

    preview_images = get_preview_images_by_proposal(proposal)
    return JsonResponse({'preview_images': preview_images}, json_dumps_params={'indent': 2})


def preview_images_by_rootname(request, rootname):
    """Return a list of available preview images in the filesystem for
    the given ``rootname``.

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage
    rootname : str
        The rootname of interest (e.g. ``jw86600008001_02101_00007_guider2``).

    Returns
    -------
    JsonResponse object
        Outgoing response sent to the webpage
    """

    preview_images = get_preview_images_by_rootname(rootname)
    return JsonResponse({'preview_images': preview_images}, json_dumps_params={'indent': 2})


def thumbnails_by_proposal(request, proposal):
    """Return a list of available thumbnails in the filesystem for the
    given ``proposal``.

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage
    proposal : str
        The five-digit proposal number (e.g. ``88600``)

    Returns
    -------
    JsonResponse object
        Outgoing response sent to the webpage
    """

    thumbnails = get_thumbnails_by_proposal(proposal)
    return JsonResponse({'thumbnails': thumbnails}, json_dumps_params={'indent': 2})


def thumbnail_by_rootname(request, rootname):
    """Return the best available thumbnail in the filesystem for the
    given ``rootname``.

    Parameters
    ----------
    request : HttpRequest object
        Incoming request from the webpage
    rootname : str
        The rootname of interest (e.g. ``jw86600008001_02101_00007_guider2``).

    Returns
    -------
    JsonResponse object
        Outgoing response sent to the webpage
    """

    thumbnail = get_thumbnail_by_rootname(rootname)
    return JsonResponse({'thumbnails': thumbnail}, json_dumps_params={'indent': 2})
