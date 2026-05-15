from sportorg.libs.ocad import ocad
from sportorg.models import memory
from sportorg.models.memory import race


class OcadImportException(Exception):
    pass


def import_txt_v8(source):
    try:
        classes_v8 = ocad.parse_txt_v8(source)
        for course in classes_v8.courses:
            if course.bib and course.bib != "0":
                name = course.bib
            elif course.group:
                name = course.group
            else:
                name = course.course
            if name not in race().course_index_name:
                c = memory.Course()
                c.name = name
                c.length = int(course.length * 1000)
                c.climb = course.climb
                controls = []
                for order, control in course.controls.items():
                    if str(control.code).isdecimal():  # don't use start and finish
                        course_control = memory.CourseControl()
                        course_control.code = control.code
                        course_control.order = control.order
                        course_control.length = int(control.length * 1000)
                        controls.append(course_control)
                c.controls = controls
                memory.race().courses.append(c)
    except Exception as e:
        raise OcadImportException(e)

    return True
