import pyfiles.gccutils.datacollection as datac


class MyGcc:

    def __init__(self, username, password):
        # self.username = username
        # self.password = password
        self.dc = datac.DataCollection(username, password)
    
    def login(self):
        """ Attempts to login to myGCC """
        pass

    def logout(self):
        """ Logs out of myGCC if currently logged in """
        pass

    def iter_all_courses(self):
        iterator = datac.CourseIterator(self.dc)
        for course in iterator.iter_all_courses():
            yield course
