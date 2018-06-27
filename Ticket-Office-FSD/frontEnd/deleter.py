import os


class TrashCan(object):
    def __init__(self):
        pass

    def unlink(self, path):
        os.remove(path)
