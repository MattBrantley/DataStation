# -*- coding: utf-8 -*-
from DC_Electrode import DC_Electrode
import os, uuid

class Penning_Trap(DC_Electrode):
    componentType = 'Penning Trap'
    componentIdentifier = 'penTrap_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/13/2018'
    iconGraphicSrc = 'Penning_Trap.png' #Not adjustable like layoutGraphicSrc
    valid = False