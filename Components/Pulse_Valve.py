# -*- coding: utf-8 -*-
"""
A circular DC lens
"""
from Components.Basic_Trigger import Basic_Trigger
import os, uuid

class Pulse_Valve(Basic_Trigger):
    componentType = 'Pulse Valve'
    componentIdentifier = 'pulsevalve_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/13/2018'
    iconGraphicSrc = 'Pulse_Valve.png' #Not adjustable like layoutGraphicSrc
    valid = False