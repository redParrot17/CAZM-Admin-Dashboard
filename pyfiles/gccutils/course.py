
class Course:
    
    def __init__(self, code, name, term, credits, department, requisites):
        self.code = code
        self.name = name
        self.term = term
        self.credits = credits
        self.department = department
        self.requisites = requisites
    
    def __repr__(self):
        code = self.code
        name = self.name
        term = self.term
        credits = self.credits
        department = self.department
        requisites = self.requisites
        return f'Course({code=}, {name=}, {term=}, {credits=}, {department=}, {requisites=})'

    def __dict__(self):
        return {
            'code': self.code,
            'name': self.name,
            'term': self.term,
            'credits': self.credits,
            'department': self.department,
            'requisites': self.requisites}
    
    def is_same(self, other):
        return self.code == other.code and self.term == other.term
