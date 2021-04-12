import mysql.connector


class Database:

    def __init__(self, config_file):
        self.db = mysql.connector.connect(option_files=config_file, autocommit=True)
    
    def close(self):
        self.db.close()

    def get_current_semester(self):
        cursor = self.db.cursor(buffered=True)
        sql = "SELECT Semester, Year FROM CurrentSemester;"
        cursor.execute(sql)
        result = cursor.fetchone()
        if result is not None:
            semester, year = result
            return f'{semester} {year}'
        return ''

    def set_current_semester(self, semester):
        cursor = self.db.cursor(buffered=True)

        sql = "DELETE FROM CurrentSemester;"
        cursor.execute(sql)

        semester, year = semester.rsplit(' ', 1)
        year = int(year)

        sql = "INSERT INTO CurrentSemester (Semester, Year) VALUES (%s, %s);"
        arg = (semester, year,)
        cursor.execute(sql, arg)

    def get_course(self, course_code):
        cursor = self.db.cursor(buffered=True)
        sql = "SELECT name, credits, semester, year FROM COURSE WHERE course_code=%s;"
        cursor.execute(sql, (course_code,))
        result = cursor.fetchone()
        cursor.close()

        if result is not None:
            name, hours, semester, year = result
            requisites = self.fetch_course_requisites(course_code)
            return self._map_to_course(course_code, name, hours, semester, year, requisites)

    def get_all_courses(self):
        cursor = self.db.cursor(buffered=True)
        sql = "SELECT course_code, name, credits, semester, year FROM COURSE;"
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        for code, name, hours, semester, year in results:
            requisites = self.fetch_course_requisites(code)
            yield self._map_to_course(code, name, hours, semester, year, requisites)

    def update_course(self, code, old_semester, old_year, name, hours, semester, year, requisites):
        self.delete_courses([(code, old_semester, old_year)])
        cursor = self.db.cursor(buffered=True)
        sql = "INSERT INTO COURSE (COURSE_CODE, NAME, CREDITS, SEMESTER, YEAR) " \
              "VALUES(%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE " \
              "NAME=VALUES(NAME), CREDITS=VALUES(CREDITS);"
        args = (code, name, hours, semester, year)
        cursor.execute(sql, args)
        cursor.close()
        self.update_course_requisites(code, requisites)

    def delete_courses(self, course_values):
        for value in course_values:
            code, semester, year = value
            requisites = self.fetch_course_requisites(code)
            self.delete_all_course_requisites(code)
            self._delete_course(code, semester, year)
            try: self.insert_course_requisites(code, requisites)
            except: pass
    
    def _delete_course(self, course_code, semester, year):
        cursor = self.db.cursor(buffered=True)
        args = (course_code, semester, year)
        sql = "DELETE FROM COURSE WHERE course_code=%s AND semester=%s AND year=%s;"
        cursor.execute(sql, args)
        cursor.close()

    def fetch_course_requisites(self, course_code):
        cursor = self.db.cursor(buffered=True)
        sql = "SELECT requisite_group, type, requisite_code FROM REQUISITES WHERE course_code=%s;"
        cursor.execute(sql, (course_code,))
        results = cursor.fetchall()

        requisites = {}
        for group_num, req_type, req_name in results:
            if group_num not in requisites:
                requisites[group_num] = []
            requisites[group_num].append([self._map_id_to_type(req_type), req_name])

        cursor.close()
        return [v for _, v in requisites.items()]

    def update_course_requisites(self, course_code, requisites):
        self.delete_all_course_requisites(course_code)
        self.insert_course_requisites(course_code, requisites)

    def insert_course_requisites(self, course_code, requisites):
        cursor = self.db.cursor(buffered=True)
        sql = "INSERT INTO REQUISITES (course_code, requisite_group, type, requisite_code) " \
              "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE type=VALUES(type);"
        data = []

        for group_num, entries in enumerate(requisites):
            for entry in entries:
                data.append((course_code, group_num, self._map_type_to_id(entry[0]), entry[1]))

        cursor.executemany(sql, data)
        cursor.close()

    def delete_all_course_requisites(self, course_code):
        cursor = self.db.cursor(buffered=True)
        sql = "DELETE FROM REQUISITES WHERE course_code=%s;"
        cursor.execute(sql, (course_code,))
        cursor.close()

    @staticmethod
    def _map_type_to_id(requisite_type):
        if requisite_type == 'prerequisite':
            return 1
        if requisite_type == 'corequisite':
            return 2
        return 0

    @staticmethod
    def _map_id_to_type(requisite_type_id):
        if requisite_type_id == 1:
            return 'prerequisite'
        if requisite_type_id == 2:
            return 'corequisite'
        return 'other'

    @staticmethod
    def _map_to_course(code, name, hours, semester, year, requisites):
        return dict(
            code=code, 
            name=name,
            credits=hours, 
            term=f'{semester} {year}',
            requisites=requisites)
