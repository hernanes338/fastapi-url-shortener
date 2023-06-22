import validators
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from . import models, schemas, crud
from .database import SessionLocal, engine

from starlette.datastructures import URL

from .config import get_settings

app = FastAPI()
# binds the database engine
models.Base.metadata.create_all(bind=engine)  # If the database defined in engine doesn’t exist yet, then it’ll be created with all modeled tables

def get_db(): # create and yield new database sessions with each request
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() # close the database session after each request

def raise_not_found(request):
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)

def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)

def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    base_url = URL(get_settings().base_url)
    admin_endpoint = app.url_path_for(
        "administration info", secret_key=db_url.secret_key
    )
    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    return db_url

@app.get("/")
def read_root():
    return "Welcome to the URL shortener API :)"

@app.post("/url", response_model=schemas.URLInfo)
def create_url(
        url: schemas.URLBase,          
        db: Session = Depends(get_db)
    ): # requires a URLBase schema as an argument and depends on the database session
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    db_url = crud.create_db_url(db=db, url=url) # get the db_url database object back
    return get_admin_info(db_url)

@app.get("/{url_key}")
def forward_to_target_url(
        url_key: str,
        request: Request,
        db: Session = Depends(get_db)
    ):
    if db_url := crud.get_db_url_by_key(db=db, url_key=url_key): # walrus operator to assign variables in the middle of an expression
        crud.update_db_clicks(db=db, db_url=db_url)
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)

@app.get("/admin/{secret_key}", name="administration info", response_model=schemas.URLInfo)
def get_url_info(
        secret_key: str,
        request: Request,
        db: Session = Depends(get_db)
    ):
    if db_url := crud.get_db_url_by_secret_key(db, secret_key=secret_key):
        return get_admin_info(db_url)
    else:
        raise_not_found(request)

@app.post("/admin/{secret_key}")
def activate_url(
        secret_key: str, 
        request: Request, 
        db: Session = Depends(get_db)
    ):
    if db_url := crud.activate_db_url_by_secret_key(db, secret_key=secret_key):
        message = f"Successfully activated the shortened URL for '{db_url.target_url}'"
        return {"detail": message}
    else:
        raise_not_found(request)

@app.delete("/admin/{secret_key}")
def deactivate_url(
        secret_key: str, 
        request: Request, 
        db: Session = Depends(get_db)
    ):
    if db_url := crud.deactivate_db_url_by_secret_key(db, secret_key=secret_key):
        message = f"Successfully deactivated the shortened URL for '{db_url.target_url}'"
        return {"detail": message}
    else:
        raise_not_found(request)