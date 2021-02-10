import pyfiles.gccutils.datacollection as datac


class MyGcc:

    def __init__(self, username, password):
        self.dc = datac.DataCollection(username, password)
        self.user_id = None
    
    def login(self):
        """ Attempts to login to myGCC """
        self.dc.GET('https://my.gcc.edu/ICS/', params=dict(tool='myProfileSettings'))
        soup = self.dc.make_soup()
        header = soup.find('span', {'id': 'CP_V_ViewHeader_SiteManagerLabel'})
        if header is not None:
            self.user_id = header.text.split('#')[-1].strip()
            return True
        return False

    def logout(self):
        """ Logs out of myGCC if currently logged in """
        pass

    def iter_all_courses(self):
        iterator = datac.CourseIterator(self.dc)
        for course in iterator.iter_all_courses():
            yield course
