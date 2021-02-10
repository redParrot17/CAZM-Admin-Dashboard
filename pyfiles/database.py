import json


def initialize():
    # for development purposes, we will copy the courses.json
    # file into the static/json directory
    # lines = []
    # with open('courses.json', 'r') as f:
    #     lines = f.readlines()
    # with open('static/json/courses.json', 'w+') as f:
    #     f.writelines(lines)
    pass

def create_entry(code, name, term, credits, requisites):
    print('Creating: ', {'code': code, 'name': name, 'term': term, 'credits': credits, 'requisites': requisites})

def update_entry(code, name, term, credits, requisites):
    print('Updating: ', {'code': code, 'name': name, 'term': term, 'credits': credits, 'requisites': requisites})

def delete_entries(course_codes: list):
    print('Deleting: ', course_codes)
    
