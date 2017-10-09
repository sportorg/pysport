import time
import logging

from sportorg.lib.ocad import ocad
from sportorg.app.models import model
from sportorg.app.models import memory


def import_txt_v8_to_model(source):
    classes_v8 = ocad.parse_txt_v8(source)
    diff = time.time()
    logging.info("Start import_txt_v8_to_model")

    for course in classes_v8.courses:
        c = model.Course.create(
            name=course.group,
            course_family=course.type,
            length=course.length,
            climb=course.climb,
            number_of_controls=len(course.controls),
            race=1
        )
        with model.database_proxy.atomic():
            for order, control in course.controls.items():
                model.CourseControl.create(
                    course=c.id,
                    control=control.code,
                    order=control.order,
                    leg_length=control.length
                )
    logging.info("Finish " + str(time.time()-diff))

    return True


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
