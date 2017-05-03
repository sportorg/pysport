from sportorg.lib.ocad import ocad
from sportorg.app.models import model
import time
import logging
import config


def import_txt_v8(source):
    classes_v8 = ocad.parse_txt_v8(source)
    diff = time.time()
    logging.basicConfig(**config.LOG_KWARGS, level=logging.DEBUG if config.DEBUG else logging.WARNING)
    logging.info("Start")

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
