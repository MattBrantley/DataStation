# -*- coding: utf-8 -*-
"""
A circular DC lens
"""
from DC_Electrode import DC_Electrode
import os, uuid

class Circular_Lens(DC_Electrode):
    componentType = 'Circular Lens'
    componentIdentifier = 'circLens_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/13/2018'
    iconGraphicSrc = 'lens.png' #Not adjustable like layoutGraphicSrc
    valid = False