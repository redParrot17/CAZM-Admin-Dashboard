
class Course:
    
    def __init__(self, code, name, term, hours, requisites):
        self.code = code
        self.name = name
        self.term = term
        self.hours = hours
        self.requisites = requisites
    
    def __repr__(self):
        code = self.code
        name = self.name
        term = self.term
        hours = self.hours
        requisites = self.requisites
        return f'Course({code=}, {name=}, {term=}, {hours=}, {requisites=})'

    def __dict__(self):
        return {
            'code': self.code,
            'name': self.name,
            'term': self.term,
            'credits': self.hours,
            'requisites': self.requisites}
    
    def is_same(self, other):
        return self.code == other.code and self.term == other.term
