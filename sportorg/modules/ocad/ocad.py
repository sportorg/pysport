from sportorg.libs.ocad import ocad
from sportorg.models import memory


class OcadImportException(Exception):
    pass


def import_txt_v8(source):
    try:
        classes_v8 = ocad.parse_txt_v8(source)
        for course in classes_v8.courses:
            if course.bib and course.bib != '0':
                name = course.bib
            elif course.group:
                name = course.group
            else:
                name = course.course
            if memory.find(memory.race().courses, name=name) is None:
                c = memory.create(
                    memory.Course,
                    name=name,
                    length=int(course.length * 1000),
                    climb=course.climb,
                )
                controls = []
                for order, control in course.controls.items():
                    if str(control.code).isdecimal():  # don't use start and finish
                        controls.append(
                            memory.create(
                                memory.CourseControl,
                                code=control.code,
                                order=control.order,
                                length=int(control.length * 1000),
                            )
                        )
                c.controls = controls
                memory.race().courses.append(c)
    except Exception as e:
        raise OcadImportException(e)

    return True
