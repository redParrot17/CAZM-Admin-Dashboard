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

def create_entry(code, name, term, credits, department, requisites):
    pass

def change_entry(course_code, **changes):
    pass

def delete_entries(course_codes: list):
    pass
    # TODO: replace this with an actual database thing once created

    # data = None
    # with open('static/json/courses.json', 'r') as f:
    #     data = json.load(f)

    # new_data = []
    # for entry in data:
    #     code = entry.get('code')
    #     if code in course_codes:
    #         print('Deleting:', code)
    #     else:
    #         new_data.append(entry)
  
    
    # with open('static/json/courses.json', 'w') as f:
    #     f.write(json.dumps(new_data)) 
    
