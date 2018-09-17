
class eventType():
    def __init__(self):
        self.name = 'DefaultEvent'
        self.parameters = list()

    def getLength(self, params):
        return 0

class eventParameter(QLineEdit):
    valueModified = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.name = ''
        self.editingFinished.connect(self.isTextDirty)
        self.textEdited.connect(self.textHasChanged)
        self.dirty = False

    def textHasChanged(self, value):
        self.dirty = True

    def isTextDirty(self):
        if(self.dirty is True):
            self.valueModified.emit()
        self.dirty = False

class eventParameterDouble(eventParameter):
    def __init__(self, name, defaultVal=0, decimalPlaces=4, allowZero=True, allowNegative=True, **kwargs):
        super().__init__()
        self.name = name
        self.allowZero = allowZero
        self.validator = QDoubleValidator()
        self.quant = Decimal(10) ** -decimalPlaces
        self.setValidator(self.validator)
        if(allowNegative == False):
            self.validator.setBottom(0)
        self.editingFinished.connect(self.checkValue)

        self.setText(str(defaultVal))
        self.editingFinished.emit()
        self.dirty = False

    def value(self):
        if(self.text() != '' and self.text() != '-' and self.text() != '.'):
            return float(self.text())
        else:
            return float(0.0)

    def setValue(self, value):
        self.setText(str(Decimal(value).quantize(self.quant)))

    def checkValue(self):
        value = self.text()
        if(self.allowZero is False):
            if(float(self.text()) == 0):
                value = '0.001'
        self.setText(str(Decimal(value).quantize(self.quant)))

class eventParameterInt(eventParameter):
    def __init__(self, name, defaultVal=0, allowZero=True, allowNegative=True, **kwargs):
        super().__init__()
        self.name = name
        self.allowZero = allowZero
        self.validator = QIntValidator()
        self.setValidator(self.validator)
        if(allowNegative == False):
            self.validator.setBottom(0)
        self.editingFinished.connect(self.checkValue)

        self.setText(str(defaultVal))
        self.editingFinished.emit()
        self.dirty = False

    def value(self):
        if(self.text() != ''):
            return int(self.text())
        else:
            return int(0)

    def setValue(self, value):
        self.setText(str(value))

    def checkValue(self):
        value = self.text()
        if(self.allowZero is False):
            if(float(self.text()) == 0):
                value = '1'
        self.setText(value)

class eventParameterString(eventParameter):
    def __init__(self, name, **kwargs):
        super().__init__()
        self.name = name
        self.dirty = False
        
    def value(self):
        return self.text()

    def setValue(self, value):
        self.setText(str(value))
