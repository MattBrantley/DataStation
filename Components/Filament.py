# -*- coding: utf-8 -*-
"""
A circular DC lens
"""
from Components.DC_Electrode import DC_Electrode
import os, uuid

class Filament(DC_Electrode):
    componentType = 'Filament'
    componentIdentifier = 'fil_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/13/2018'
    iconGraphicSrc = 'Filament.png' #Not adjustable like layoutGraphicSrc
    valid = False