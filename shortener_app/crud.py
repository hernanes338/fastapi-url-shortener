from sqlalchemy.orm import Session

from . import models, schemas, keygen

def get_db_url_by_key(db: Session, url_key: str) -> models.URL: # returns either None or a database entry with a provided key
    return (
        db.query(models.URL)
        .filter(models.URL.key == url_key, models.URL.is_active)
        .first()
    )

def create_db_url(db: Session, url: schemas.URLBase) -> models.URL:
    key = keygen.create_unique_random_key(db)
    secret_key = f"{key}_{keygen.create_random_key(length=8)}"
    db_url = models.URL(
        target_url=url.target_url, key=key, secret_key=secret_key
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url

# checks the database for an active database entry with the provided secret_key
def get_db_url_by_admin_key(db: Session, admin_key: str) -> models.URL:  # returns either None or a database entry with a provided key
    return (
        db.query(models.URL)
        .filter(models.URL.admin_url == admin_key)
        .first()
    )