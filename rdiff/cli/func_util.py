from functools import partial


class starpartial(partial):
    def __call__(self, args):
        return super().__call__(*args)
