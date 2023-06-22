import validators
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from . import models, schemas, crud
from .database import SessionLocal, engine

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

@app.get("/")
def read_root():
    return "Welcome to the URL shortener API :)"

@app.post("/url", response_model=schemas.URLInfo)
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)): # requires a URLBase schema as an argument and depends on the database session
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    db_url = crud.create_db_url(db=db, url=url) # get the db_url database object back
    db_url.url = db_url.key
    db_url.admin_url = db_url.secret_key

    return db_url

@app.get("/{url_key}")
def forward_to_target_url(
        url_key: str,
        request: Request,
        db: Session = Depends(get_db)
    ):
    if db_url := crud.get_db_url_by_key(db=db, url_key=url_key): # walrus operator to assign variables in the middle of an expression
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)