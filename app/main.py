from datetime import date, time, datetime
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarHTTPException

from app.schemas import PostCreate, PostResponse

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="./templates")


class Post(BaseModel):
    id: int
    author: str
    title: str
    content: str
    date: str

posts: list[Post] = [
    Post(
        id=0,
        author="jeff",
        title="fastapi",
        content="fastapi lowk goated",
        date="2026-08-01",
    ),

    Post(
        id=1,
        author="teddy",
        title="python",
        content="ilovepython",
        date="2026-08-02",
    ),

    Post(
        id=2,
        author="bear",
        title="salmon",
        content="ilovesalmon",
        date="2026-08-04",
    ),
]

@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"posts" : posts, "title" : "Home"})

@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request, post_id: int):
    for p in posts:
        if p.id == post_id:
            title = p.title[:25]
            return templates.TemplateResponse(
                request, 
                "post.html",
                {
                    "post" : p,
                    "title": title
                } 
            )
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"post with {post_id=} not found")

@app.get("/api/posts", response_model=list[PostResponse])
def get_posts():
    return posts

@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int):
    for p in posts:
        if p.id == post_id:
            return p
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"post with {post_id=} not found")

@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(post: PostCreate):
    new_id = max(p.id for p in posts) + 1 if posts else 1
    new_post = Post(
        id = new_id,
        author = post.author,
        title = post.title,
        content = post.content,
        date = date.today().isoformat()
    )
    posts.append(new_post)
    return new_post

'''
What's the point of this? From Corey Schafer's series:

The reason why Starlette HTTP exception is used because we want to be able to handle anything that isn't caught by the FastAPI router.
This is fine for pure JSON API, but because there's also a UI, we want the user flow to not break and show JSON
This catches the error, and then sends it into a Jinja template if UI, and just sends the generic JSON API response/exception
'''
@app.exception_handler(StarHTTPException)
def general_http_exception_handler(request: Request, exception: StarHTTPException):
    message = (
        exception.detail if exception.detail else "An error occured."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            comment={"detail" : message}
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code
    )

@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )