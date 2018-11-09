

class ModuleResource():
############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def Has_Tag(self, tags):
        self.hasTag(tags)

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, name, tags):
        self.name = name
        self.tags = tags

    def hasTag(self, tags):
        if isinstance(tags, list): # Is a list of tags
            for tag in tags:
                if tag in self.tags:
                    return True
        else: # is a single tag
            if tags in self.tags:
                return True