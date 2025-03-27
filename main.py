from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import io
import cv2
import numpy as np
from integrations import read_text_in_image
from grading import grade_essay
import traceback
import tempfile
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

app = FastAPI()
Base = declarative_base()

class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    authorname = Column(String, unique=True)
    name = Column(String)
    essays = relationship("Essay", back_populates="author")

class Essay(Base):
    __tablename__ = 'essays'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('authors.id'))
    title = Column(String)
    text = Column(Text)
    date_submitted = Column(String, default=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))  # Store as string
    images = relationship("EssayImage", back_populates="essay")  # Multiple images
    grades = relationship("EssayGrade", back_populates="essay")  # Multiple grades
    author = relationship("Author", back_populates="essays")


class EssayImage(Base):
    __tablename__ = 'essay_images'
    id = Column(Integer, primary_key=True)
    essay_id = Column(Integer, ForeignKey('essays.id'))
    image_path = Column(String)  # Store image file path
    essay = relationship("Essay", back_populates="images")


class EssayGrade(Base):
    __tablename__ = 'essay_grades'
    id = Column(Integer, primary_key=True)
    essay_id = Column(Integer, ForeignKey('essays.id'))
    grade_type = Column(String)  # Type of grade (e.g., content, grammar)
    grade = Column(Float)  # Score
    comments = Column(Text)  # Comments
    essay = relationship("Essay", back_populates="grades")


def preprocess_image(image: Image.Image) -> Image.Image:
    # Convert the image to grayscale
    gray_image = ImageOps.grayscale(image)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(gray_image)
    enhanced_image = enhancer.enhance(2.0)

    # Convert to numpy array for OpenCV processing
    open_cv_image = np.array(enhanced_image)

    # Apply Gaussian Blur to reduce noise
    blurred_image = cv2.GaussianBlur(open_cv_image, (5, 5), 0)

    # Binarize the image using Otsu's thresholding
    _, binary_image = cv2.threshold(blurred_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Convert back to PIL Image
    preprocessed_image = Image.fromarray(binary_image)

    return preprocessed_image

@app.post("/submit-essay/")
async def submit_essay(authorname: str, title: str, files: List[UploadFile] = File(...)):
    extracted_texts = []

    for file in files:
        try:
            image_data = await file.read()
            image = Image.open(io.BytesIO(image_data))
            preprocessed_image = preprocess_image(image)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_image:
                preprocessed_image.save(temp_image, format="PNG")
                temp_image_path = temp_image.name

            text = read_text_in_image(temp_image_path)
            extracted_texts.append({"filename": file.filename, "text": text})

        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=f"Error processing {file.filename}: {str(e)}")

    # Combine extracted texts into a single essay text
    full_text = " ".join([text["text"] for text in extracted_texts])

    # Compute grades
    grades = grade_essay(full_text)

    # Get or create author
    author = session.query(Author).filter_by(authorname=authorname).first()
    if not author:
        author = Author(authorname=authorname)
        session.add(author)
        session.commit()

    # Create and store the essay
    essay = Essay(author=author, title=title, text=full_text, date_submitted=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))    
    session.add(essay)
    session.commit()  # Commit now to get `essay.id`

    # Store multiple images linked to the essay
    for extracted_text in extracted_texts:
        essay_image = EssayImage(essay=essay, image_path=extracted_text["filename"])
        session.add(essay_image)

    session.commit()  # Batch commit images

    # Store grades
    for grade in grades:
        essay_grade = EssayGrade(essay=essay, grade_type=grade["type"], grade=grade["grade"], comments=grade["comments"])
        session.add(essay_grade)

    session.commit()  # Batch commit grades

    return {
        "message": "Essay submitted successfully!",
        "essay_id": essay.id,
        "text": full_text,
        "grades": grades
    }


@app.get("/get-authors/")
def get_authors():
    """Fetch all authors and their essays."""
    authors = session.query(Author).all()
    
    authors_data = []
    for author in authors:
        author_info = {
            "authorname": author.authorname,
            "name": author.name,
            "essays": [{"title": essay.title, "id": essay.id, "date_submitted": essay.date_submitted} for essay in author.essays]
        }
        authors_data.append(author_info)

    return {"authors": authors_data}


@app.post("/get-author-grades/")
async def get_author_grades(authorname: str):
    author = session.query(Author).filter_by(authorname=authorname).first()
    if not author:
        raise HTTPException(status_code=404, detail=f"Author {authorname} not found.")

    return [
        {
            "text": essay.text,
            "title": essay.title,
            "date_submitted": essay.date_submitted,
            "grades": [{"type": grade.grade_type, "grade": grade.grade, "comments": grade.comments} for grade in essay.grades],
            "images": [img.image_path for img in essay.images]  # Return multiple image paths
        }
        for essay in author.essays
    ]

@app.post("/create-author/")
async def create_author(authorname: str, name: str):
    author = Author(authorname=authorname, name=name)
    session.add(author)
    session.commit()
    return author

engine = create_engine('sqlite:///database.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
