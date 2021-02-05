from pyfiles.gccutils.course import Course
from bs4 import BeautifulSoup
import requests


class DataCollection:
    BASEURL = 'https://my.gcc.edu'

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = None
        self.response = None


    def GET(self, url, **kwargs):
        if self.session is None:
            self._create_session()
        self.response = self.session.get(url, **kwargs)
        return self.response
    
    def POST(self, url, **kwargs):
        if self.session is None:
            self._create_session()
        self.response = self.session.post(url, **kwargs)
        return self.response

    def make_soup(self):
        if self.response is not None:
            return BeautifulSoup(self.response.text, features='html.parser')
        return None
    
    def prepare_payload(self, payload: dict={}, postback: str=None, include_search=True) -> dict:
        soup = self.make_soup()
        if soup is not None:
            for hiddenInput in soup.find_all('input', {'type': 'hidden'}):
                input_name = hiddenInput.get('name')
                input_value = hiddenInput.get('value')
                payload[input_name] = input_value
        if postback is not None:
            postback = postback.replace('javascript:__doPostBack(', '')
            postback = postback.replace(')', '')
            postback = postback.replace("'", '')
            eventtarget, eventargument = tuple(postback.split(',', 1))
            payload['__EVENTTARGET'] = eventtarget
            payload['__EVENTARGUMENT'] = eventargument
        if include_search:
            payload['siteNavBar$ctl00$tbSearch'] = ''
        return payload


    def _create_session(self):
        url = f'{self.BASEURL}/ICS/'
        payload = {
            '_scriptManager_HiddenField': '',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': '',
            '__VIEWSTATEGENERATOR': '',
            '___BrowserRefresh': '',
            'siteNavBar$ctl00$tbSearch': '',
            'userName': self.username,
            'password': self.password,
            'siteNavBar$btnLogin': 'Login'}
        self.session = requests.Session()
        self.response = self.session.post(url, data=payload)


class CourseIterator:
    COURSEURL = 'https://my.gcc.edu/ICS/Academics/Home.jnz'
    QUERYPARAMS = {
        'portlet': 'AddDrop_Courses',
        'screen': 'Advanced Course Search',
        'screenType': 'next'}

    def __init__(self, data_collection: DataCollection):
        self.dc = data_collection
        self.current_term = None
        self.remaining_terms = []

    def iter_all_courses(self):
        self.nav_to_search()
        self.init_term_data()
        self.nav_to_first_term()

        with open('output.html', 'w+') as f:
            f.write(self.dc.response.text)

        while True:
            while True:

                # iterate over each course on the page
                soup = self.dc.make_soup()
                table = soup.find('tbody', {'class': 'gbody'})
                if table is not None:
                    for course_row in table.find_all('tr'):
                        if 'subItem' in course_row.get('class', ''):
                            continue
                        yield self.course_row_to_course(course_row)
                
                # navigate to next page
                if not self.try_nav_next_page(soup):
                    break  # stop if this was the last page

            # navigate to next term
            if not self.try_nav_next_term():
                break  # stop if this was the last term


    def nav_to_search(self):
        self.dc.GET(self.COURSEURL, params=self.QUERYPARAMS)
    
    def init_term_data(self):
        soup = self.dc.make_soup()
        if soup is not None:
            for term_choice in soup.find('select', {'id': 'pg0_V_ddlTerm'}).find_all('option'):
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
        self.dc.POST(self.COURSEURL, data=payload, params=self.QUERYPARAMS)
    
    def course_row_to_course(self, row):

        # navigate to course page
        postback = row.find('a').get('href')
        course_code = ' '.join(row.find('a').text.strip().split(' ')[:2])
        payload = {
            'pg0$V$ddlTerm': self.current_term,
            'pg0$V$ddlDivision': 'UG'}
        payload = self.dc.prepare_payload(payload, postback)
        self.dc.POST(self.COURSEURL, data=payload, params=self.QUERYPARAMS)

        # fetch data from this page
        soup = self.dc.make_soup()
        details = soup.find('div', {'id': 'pg0_V_divCourseDetails'})

        title_elem = details.find('b')
        term_elem = details.find('span', {'id': 'pg0_V_lblTermDescValue'})
        cred_elem = details.find('span', {'id': 'pg0_V_lblCreditHoursValue'})
        dept_elem = details.find('span', {'id': 'pg0_V_lblDepartmentValue'})

        course_title = title_elem.text if title_elem else None
        course_term = term_elem.text.strip().strip(',') if term_elem else None
        course_credits = float(cred_elem.text.strip()) if cred_elem else 0.0
        course_department = dept_elem.text.strip() if dept_elem else None
        course_requisites = {}

        #fetch prerequisites
        prereqlink = soup.find('a', {'id': 'pg0_V_lnkbCourseRequisites'})
        if prereqlink is not None:
            postback = prereqlink.get('href')
            payload = self.dc.prepare_payload({}, postback)
            self.dc.POST(self.COURSEURL, data=payload, params=self.QUERYPARAMS)

            soup = self.dc.make_soup()
            course_requisites = self.parse_course_requisites(soup)

            # navigate back to the term page
            for bread in soup.find('span', {'id': 'portlet-breadcrumbs'}).find_all('a'):
                if bread.text == 'Results':
                    postback = bread.get('href')
                    payload = self.dc.prepare_payload({}, postback)
                    self.dc.POST(self.COURSEURL, data=payload, params=self.QUERYPARAMS)
                    break
        else:
            # navigate back to the term page
            payload = self.dc.prepare_payload()
            payload['__EVENTTARGET'] = 'pg0$V$lnkBack'
            self.dc.POST(self.COURSEURL, data=payload, params=self.QUERYPARAMS)

        # construct course class from data
        course = Course(course_code, course_title, course_term, course_credits, course_department, course_requisites)
        return course
    
    def parse_course_requisites(self, soup):
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
                    group_num = int(rgroup_val)
                    if group_num not in requisites:
                        requisites[group_num] = []
                    requisites[group_num].append((rtype_val, rname_val))
        return requisites

                

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
                self.dc.POST(self.COURSEURL, data=payload, params=self.QUERYPARAMS)
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
            self.dc.POST(self.COURSEURL, data=payload, params=self.QUERYPARAMS)

            # navigate to first page
            navigator = soup.find('div', {'class': 'letterNavigator'})
            if navigator is not None:
                navlinks = navigator.find_all('a')
                if len(navlinks) > 1 and navlinks[0].text == '<-- Previous page':
                    postback = navlinks[1].get('href')
                    payload = {
                        'pg0$V$ddlTerm': self.current_term,
                        'pg0$V$ddlDivision': 'UG'}
                    payload = self.dc.prepare_payload(payload, postback)
                    self.dc.POST(self.COURSEURL, data=payload, params=self.QUERYPARAMS)

            return True
        return False
