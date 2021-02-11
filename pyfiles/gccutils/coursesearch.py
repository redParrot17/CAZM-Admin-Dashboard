from pyfiles.gccutils.datacollection import DataCollection
from pyfiles.gccutils.course import Course
from pyfiles.database import Database
from bs4 import BeautifulSoup
import multiprocessing
import requests
import threading
import time
import re


class ScraperSession(threading.Thread):
    COURSEURL = 'https://my.gcc.edu/ICS/Academics/Home.jnz'
    QUERYPARAMS = {
        'portlet': 'AddDrop_Courses',
        'screen': 'Advanced Course Search',
        'screenType': 'next'}

    def __init__(self, username, password, db_config, thread_num, num_threads):
        threading.Thread.__init__(self)
        self.db_config = db_config
        self.thread_num = thread_num
        self.num_threads = num_threads
        self.dc = DataCollection(username, password)
        self.database = None
        self.aborted = False

        self.current_term = None
        self.remaining_terms = []

    def abort(self):
        """
        Asks the thread to stop running as soon as it is convenient.

        This does not guarantee that the thread will stop!
        """
        self.aborted = True

    def run(self):
        """
        The primary method of this thread that controls the web-scraping of courses on https://my.gcc.edu/.

        Do not manually call this method. Use ScraperSession#start() instead.
        """

        start_time = time.time()
        thread_num = self.thread_num
        num_threads = self.num_threads
        self.aborted = False

        print(f'scraper thread [{thread_num}|{num_threads}] starting')

        # perform initial setup
        self.database = Database(self.db_config)
        self.dc.create_session()
        self.nav_to_search()
        self.init_term_data()

        if self.current_term is None:
            self.database.close()
            print('SCRAPER INIT: no course terms were found - aborting')
            print(f'scraper thread [{thread_num}|{num_threads}] aborting after {int(time.time() - start_time)} seconds')
            return

        self.nav_to_first_term()

        while not self.aborted:
            while not self.aborted:

                # iterate over each course on the page
                soup = self.dc.make_soup()
                table = soup.find('tbody', {'class': 'gbody'})

                # the table will be null if we failed to navigate to the desired term page
                # possibly may be null if no courses exist for this term page
                if table is not None:

                    # This row index is used to determine whether or not this thread is
                    #   responsible for parsing this specific course from the list.
                    row_index = 0

                    for course_row in table.find_all('tr'):

                        # MyGCC includes hidden rows between each course displayed in the
                        #   table. These rows are irrelevant and need to be skipped. This
                        #   also checks whether or not the task has been manually aborted.
                        if self.aborted or 'subItem' in course_row.get('class', ''):
                            continue

                        # determines if this thread is responsible for this row index
                        should_handle_row = row_index % num_threads == thread_num

                        if should_handle_row:
                            try:
                                # build a course object from the row data
                                course = self.course_row_to_course(course_row)

                                # pass the course to the callback function
                                if course is not None:
                                    self.course_callback(course)

                            except Exception as e:
                                # handle errors that occur during course creation or the callback
                                print(f'scraper thread [{thread_num}|{num_threads}]'
                                      f'(term={self.current_term},row={row_index}) exception: {e}')

                        # updating the row index
                        row_index += 1

                # navigate to next page
                if not self.try_nav_next_page(soup):
                    break  # stop if this was the last page

            # navigate to next term
            if not self.try_nav_next_term():
                break  # stop if this was the last term
        
        self.database.close()
        print(f'scraper thread [{thread_num}|{num_threads}] stopping after {int(time.time() - start_time)} seconds')

    def nav_to_search(self):
        """
        Navigates to the course search page.

        This is a necessary first step prior to accessing any course.
        """
        self.dc.http_get(self.COURSEURL, params=self.QUERYPARAMS)

    def init_term_data(self):
        """
        Determines the course terms available for searching as well as which to start with.
        """

        soup = self.dc.make_soup()
        if soup is not None:
            term_selector_element = soup.find('select', {'id': 'pg0_V_ddlTerm'})
            if term_selector_element is not None:
                for term_choice in term_selector_element.find_all('option'):
                    choice_value = term_choice.get('value')
                    selected = term_choice.get('selected', '') == 'selected'
                    if selected:
                        self.current_term = choice_value
                    else:
                        self.remaining_terms.append(choice_value)

    def nav_to_first_term(self):
        payload = {
            'pg0$V$ddlTerm': self.current_term,
            'pg0$V$ddlDept': '',
            'pg0$V$ddlCourseFrom': '',
            'pg0$V$ddlCourseTo': '',
            'pg0$V$ddlTitleRestrictor': 'BeginsWith',
            'pg0$V$txtTitleRestrictor': '',
            'pg0$V$ddlCourseRestrictor': 'BeginsWith',
            'pg0$V$txtCourseRestrictor': '',
            'pg0$V$ddlDivision': 'UG',
            'pg0$V$ddlMethod': '',
            'pg0$V$txtRefRestrictor': '',
            'pg0$V$ddlTimeFrom': '',
            'pg0$V$ddlTimeTo': '',
            'pg0$V$days': 'rdAnyDay',
            'pg0$V$ddlFaculty': '',
            'pg0$V$ddlCampus': '',
            'pg0$V$ddlBuilding': '',
            'pg0$V$ddlSecStatus': 'OpenFull',
            'pg0$V$txtMin': '',
            'pg0$V$txtMax': '',
            'pg0$V$btnSearch': 'Search'}
        payload = self.dc.prepare_payload(payload)
        self.dc.http_post(self.COURSEURL, data=payload, params=self.QUERYPARAMS)

    def try_nav_next_page(self, soup):
        navigator = soup.find('div', {'class': 'letterNavigator'})
        if navigator is not None:
            navlinks = navigator.find_all('a')[::-1]
            postback = None

            for navlink in navlinks:
                if navlink.text == 'Next page -->':
                    postback = navlink.get('href')
                    break

            if postback is not None:
                payload = {
                    'pg0$V$ddlTerm': self.current_term,
                    'pg0$V$ddlDivision': 'UG'}
                payload = self.dc.prepare_payload(payload, postback)
                self.dc.http_post(self.COURSEURL, data=payload, params=self.QUERYPARAMS)
                return True
        return False

    def try_nav_next_term(self):
        if self.remaining_terms:

            # navigate to next term
            self.current_term = self.remaining_terms.pop(0)
            payload = {
                'pg0$V$ddlTerm': self.current_term,
                'pg0$V$ddlDivision': 'UG',
                'pg0$V$btnSearch': 'Search'}
            payload = self.dc.prepare_payload(payload)
            self.dc.http_post(self.COURSEURL, data=payload, params=self.QUERYPARAMS)

            # navigate to first page
            soup = self.dc.make_soup()
            navigator = soup.find('div', {'class': 'letterNavigator'})
            if navigator is not None:
                navlinks = navigator.find_all('a')
                if len(navlinks) > 1 and navlinks[0].text == '<-- Previous page':
                    postback = navlinks[1].get('href')
                    payload = {
                        'pg0$V$ddlTerm': self.current_term,
                        'pg0$V$ddlDivision': 'UG'}
                    payload = self.dc.prepare_payload(payload, postback)
                    self.dc.http_post(self.COURSEURL, data=payload, params=self.QUERYPARAMS)

            return True
        return False

    def course_row_to_course(self, row):

        # navigate to course page
        postback_element = row.find('a')
        if postback_element is None:
            raise Exception('postback element could not be found')
        postback = postback_element.get('href')
        course_code = ' '.join(postback_element.text.strip().split(' ')[:2])
        payload = {
            'pg0$V$ddlTerm': self.current_term,
            'pg0$V$ddlDivision': 'UG'}
        payload = self.dc.prepare_payload(payload, postback)
        self.dc.http_post(self.COURSEURL, data=payload, params=self.QUERYPARAMS)

        # fetch data from this page
        soup = self.dc.make_soup()
        details = soup.find('div', {'id': 'pg0_V_divCourseDetails'})

        if details is None:  # abort course parsing if the details element is missing
            self.nav_to_courses_from_course()  # ensure we return to the courses list
            raise Exception(f'details element could not be found for {course_code}')

        # fetch course title
        title_elem = details.find('b')
        if title_elem is None:  # abort course parsing if the title element is missing
            self.nav_to_courses_from_course()   # ensure we return to the courses list
            raise Exception(f'title element missing for {course_code}')
        course_title = title_elem.text.split('(', 1)[0].strip()

        # fetch course term
        term_elem = details.find('span', {'id': 'pg0_V_lblTermDescValue'})
        if term_elem is None:  # abort course parsing if the term element is missing
            self.nav_to_courses_from_course()   # ensure we return to the courses list
            raise Exception(f'term element missing for {course_code}')
        course_term = term_elem.text.strip().strip(',')

        # fetch course hours
        cred_elem = details.find('span', {'id': 'pg0_V_lblCreditHoursValue'})
        if cred_elem is None:  # abort course parsing if the credit element is missing
            self.nav_to_courses_from_course()   # ensure we return to the courses list
            raise Exception(f'credit element missing for {course_code}')
        course_credits = float(cred_elem.text.strip())

        # fetch course requisites
        course_requisites = []
        prereqlink = soup.find('a', {'id': 'pg0_V_lnkbCourseRequisites'})
        if prereqlink is not None:

            # navigate to the course requisites page
            postback = prereqlink.get('href')
            payload = self.dc.prepare_payload({}, postback)
            self.dc.http_post(self.COURSEURL, data=payload, params=self.QUERYPARAMS)

            soup = self.dc.make_soup()
            course_requisites = self.parse_course_requisites(soup)

            self.nav_to_courses_from_requisites(soup)
        else:
            self.nav_to_courses_from_course()

        # construct course class from data
        course = Course(course_code, course_title, course_term, course_credits, course_requisites)
        return course

    @staticmethod
    def parse_course_requisites(soup):
        pattern = re.compile(r'([A-Z]{2,5})([0-9]{2,4}[A-Z]*)')

        def parse_req_type(_req_type: str) -> str:
            if _req_type.startswith('Prerequisite'):
                return 'prerequisite'
            if _req_type.startswith('Corequisite'):
                return 'corequisite'
            return 'other'

        def parse_req_name(_req_name: str) -> str:
            first_word = _req_name.split(' ', 1)[0]
            match = pattern.match(first_word)
            if match:
                first, second = match.groups()
                return first + ' ' + second
            return first_word

        requisites = {}
        table = soup.find('tbody', {'class': 'gbody'})
        if table is not None:
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) != 5:
                    continue
                _, _, rgroup, rtype, rname = tuple(cells)
                rgroup_val = rgroup.text.strip()
                rtype_val = rtype.text.strip()
                rname_val = rname.text.strip()

                if rgroup_val != '':
                    try:
                        group_num = int(rgroup_val)
                        if group_num not in requisites:
                            requisites[group_num] = []
                        requisites[group_num].append((parse_req_type(rtype_val), parse_req_name(rname_val)))
                    except ValueError:
                        print('group number could not be converted to an int')
        return [v for _, v in requisites.items()]

    def nav_to_courses_from_course(self):
        """ Navigates back to the course list from a course overview page. """
        payload = self.dc.prepare_payload()
        payload['__EVENTTARGET'] = 'pg0$V$lnkBack'
        self.dc.http_post(self.COURSEURL, data=payload, params=self.QUERYPARAMS)

    def nav_to_courses_from_requisites(self, soup):
        """ Navigates back to the course list from a course requisite page. """
        breadcrumbs = soup.find('span', {'id': 'portlet-breadcrumbs'})
        if breadcrumbs is None:
            raise Exception('failed to navigate to courses from requisite page')
        for bread in breadcrumbs.find_all('a'):
            if bread.text == 'Results':
                postback = bread.get('href')
                payload = self.dc.prepare_payload({}, postback)
                self.dc.http_post(self.COURSEURL, data=payload, params=self.QUERYPARAMS)
                break
    
    def course_callback(self, course):
        database = self.database
        semester, year = course.term.rsplit(' ', 1)
        year = int(year)
        database.update_course(
            course.code,
            course.name,
            course.hours,
            semester,
            year,
            course.requisites)


class AsyncCourseScraper:

    def __init__(self, username, password, db_config):
        self.__username = username
        self.__password = password
        self.__db_config = db_config
        self.__cpu_count = multiprocessing.cpu_count()
        self.__sessions = []
        self.reset()

    def is_running(self):
        for session in self.__sessions:
            if session.is_alive():
                return True
        return False

    def start(self):
        if self.is_running():
            raise RuntimeError('scrapers are already running')
        for session in self.__sessions:
            session.start()

    def stop(self):
        for session in self.__sessions:
            session.abort()

    def reset(self):
        self.stop()
        cpu_count = self.__cpu_count
        username = self.__username
        password = self.__password
        db_config = self.__db_config
        self.__sessions = [ScraperSession(username, password, db_config, i, cpu_count) for i in range(cpu_count)]

