async def db_get(db, query, **parameters):
    async with db.execute(query, parameters) as cursor:
        async for row in cursor:
            yield dict(row)


async def db_get_one(db, column, query, **parameters):
    async for row in db_get(db, query, **parameters):
        return row.get(column, None)
    else:
        return None


async def db_get_first(db, query, **parameters):
    async for row in db_get(db, query, **parameters):
        return row
    else:
        return None


async def insert_one(db, query, **parameters):
    async with db.execute(query, parameters) as cursor:
        return cursor.lastrowid
