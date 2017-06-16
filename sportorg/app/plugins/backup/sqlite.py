from sportorg.app.models import memory, model


def dump(source):
    model.initialize(source)
    model.create_db()
    dump_persons()


def dump_persons():
    with model.database_proxy.atomic():
        for person in memory.race().persons:
            model.Person.create(
                name=person.name,
                surname=person.surname,
                sex=person.sex,
                year=person.year,
                birth_date=person.birth_date,
                world_code=person.world_code,
                national_code=person.national_code,
                rank=person.rank,
                qual=person.qual,
            )


def load(source):
    pass
