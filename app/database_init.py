from app.database import Base, engine  # ✅ this is your shared Base
from app.models import user, calculation  # ✅ import all models so Base.metadata knows them

def init_db():
    Base.metadata.create_all(bind=engine)

def drop_db():
    Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    init_db()  # pragma: no cover
