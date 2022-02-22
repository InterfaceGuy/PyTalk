import c4d


class Document:

    def __init__(self):
        self.create_document()
        self.insert_document()

    def create_document(self):
        self.document = c4d.documents.BaseDocument()

    def insert_document(self):
        c4d.documents.InsertBaseDocument(self.document)
        c4d.documents.SetActiveDocument(self.document)
