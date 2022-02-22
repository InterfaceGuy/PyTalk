from pydeation.objects.abstract_objects import SVG
import c4d

class David(SVG):

    def __init__(self, **kwargs):
        super().__init__("david", **kwargs)

class GitHub(SVG):

    def __init__(self, **kwargs):
        super().__init__("github", **kwargs)

class DNA(SVG):

    def __init__(self, **kwargs):
        super().__init__("dna", **kwargs)
