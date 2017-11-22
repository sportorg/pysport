from sportorg.lib.ocad import ocad
from sportorg.app.models import memory


def import_txt_v8(source):
    classes_v8 = ocad.parse_txt_v8(source)
    for course in classes_v8.courses:
        c = memory.create(
            memory.Course,
            name=course.group if course.group else course.course,
            length=int(course.length * 1000),
            climb=course.climb
        )
        controls = []
        for order, control in course.controls.items():
            if str(control.code).isdecimal():  # don't use start and finish
                controls.append(memory.create(
                    memory.CourseControl,
                    code=control.code,
                    order=control.order,
                    length=int(control.length * 1000)
                ))
        c.controls = controls
        memory.race().courses.append(c)

    return True
