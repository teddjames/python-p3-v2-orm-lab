from __init__ import CURSOR, CONN

class Review:
    # Cache of all persisted Review instances
    all = {}

    def __init__(self, year, summary, employee_id, id=None):
        # Assign via property setters (validations)
        self.id = id
        self.year = year
        self.summary = summary
        self.employee_id = employee_id

    def __repr__(self):
        return (
            f"<Review {self.id}: year={self.year}, summary={self.summary!r}, "
            f"employee_id={self.employee_id}>"
        )

    @classmethod
    def create_table(cls):
        sql = """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            year INTEGER,
            summary TEXT,
            employee_id INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );
        """
        CURSOR.execute(sql)
        CONN.commit()

    @classmethod
    def drop_table(cls):
        sql = "DROP TABLE IF EXISTS reviews;"
        CURSOR.execute(sql)
        CONN.commit()

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, value):
        if not isinstance(value, int):
            raise ValueError("year must be an integer")
        if value < 2000:
            raise ValueError("year must be >= 2000")
        self._year = value

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, text):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("summary must be a non-empty string")
        self._summary = text

    @property
    def employee_id(self):
        return self._employee_id

    @employee_id.setter
    def employee_id(self, eid):
        # avoid circular import
        from employee import Employee
        if not isinstance(eid, int) or Employee.find_by_id(eid) is None:
            raise ValueError("employee_id must reference an existing Employee")
        self._employee_id = eid

    def save(self):
        sql = """
        INSERT INTO reviews (year, summary, employee_id)
        VALUES (?, ?, ?);
        """
        CURSOR.execute(sql, (self.year, self.summary, self.employee_id))
        CONN.commit()
        self.id = CURSOR.lastrowid
        type(self).all[self.id] = self

    @classmethod
    def create(cls, year, summary, employee_id):
        review = cls(year, summary, employee_id)
        review.save()
        return review

    @classmethod
    def instance_from_db(cls, row):
        rid, year, summary, eid = row
        inst = cls.all.get(rid)
        if inst:
            # refresh attributes in case they were mutated
            inst.year = year
            inst.summary = summary
            inst.employee_id = eid
        else:
            inst = cls(year, summary, eid, id=rid)
            cls.all[rid] = inst
        return inst

    @classmethod
    def find_by_id(cls, id):
        sql = "SELECT * FROM reviews WHERE id = ?;"
        row = CURSOR.execute(sql, (id,)).fetchone()
        return cls.instance_from_db(row) if row else None

    def update(self):
        sql = """
        UPDATE reviews
        SET year = ?, summary = ?, employee_id = ?
        WHERE id = ?;
        """
        CURSOR.execute(sql, (self.year, self.summary, self.employee_id, self.id))
        CONN.commit()

    def delete(self):
        sql = "DELETE FROM reviews WHERE id = ?;"
        CURSOR.execute(sql, (self.id,))
        CONN.commit()
        # remove from cache and clear id
        type(self).all.pop(self.id, None)
        self.id = None

    @classmethod
    def get_all(cls):
        sql = "SELECT * FROM reviews;"
        rows = CURSOR.execute(sql).fetchall()
        return [cls.instance_from_db(row) for row in rows]
