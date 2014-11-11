#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

from . import common as com
from .ibeis_part import IBEIS_Part


class IBEIS_Object(object):

    def __init__(ibso, _xml, width, height, name=None, **kwargs):
        if name is None:
            ibso.name = com.get(_xml, 'name')
            ibso.pose = com.get(_xml, 'pose')
            ibso.truncated = com.get(_xml, 'truncated') == "1"
            ibso.difficult = com.get(_xml, 'difficult') == "1"

            bndbox = com.get(_xml, 'bndbox', text=False)
            ibso.xmax = min(width,  int(float(com.get(bndbox, 'xmax'))))
            ibso.xmin = max(0,      int(float(com.get(bndbox, 'xmin'))))
            ibso.ymax = min(height, int(float(com.get(bndbox, 'ymax'))))
            ibso.ymin = max(0,      int(float(com.get(bndbox, 'ymin'))))

            ibso.parts = [ IBEIS_Part(part) for part in com.get(_xml, 'part', text=False, singularize=False)]
        else:
            ibso.name = name
            ibso.pose = 'Unspecified'
            ibso.truncated = False
            ibso.difficult = False

            ibso.xmax = min(width,  int(_xml['xmax']))
            ibso.xmin = max(0,      int(_xml['xmin']))
            ibso.ymax = min(height, int(_xml['ymax']))
            ibso.ymin = max(0,      int(_xml['ymin']))

            ibso.parts = []

        ibso.width = ibso.xmax - ibso.xmin
        ibso.height = ibso.ymax - ibso.ymin
        ibso.xcenter = int(ibso.xmin + (ibso.width / 2))
        ibso.ycenter = int(ibso.ymin + (ibso.height / 2))
        ibso.area = ibso.width * ibso.height

    def __len__(ibso):
        return len(ibso.parts)

    def bounding_box(ibso, parts=False):
        _parts = [ part.bounding_box() for part in ibso.parts ]
        return [ibso.name, ibso.xmax, ibso.xmin, ibso.ymax, ibso.ymin, _parts]
