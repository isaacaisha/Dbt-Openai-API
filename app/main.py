from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import Memory
from . import models
from .database import engine, get_db
from typing import Optional

import openai
import uvicorn
from fastapi import FastAPI, Response, status, HTTPException, Depends
from psycopg2.extras import RealDictCursor
import time

from dotenv import load_dotenv, find_dotenv
import os
import psycopg2

from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, validators
import secrets

_ = load_dotenv(find_dotenv())

models.Base.metadata.create_all(bind=engine)

app = FastAPI(debug=True)

openai.api_key = os.environ['OPENAI_API_KEY']
# Generate a random secret key
secret_key = secrets.token_hex(199)
# Set it as the Flask application's secret key
app.secret_key = secret_key

# Initialize an empty conversation chain
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")  # Set your desired LLM model here
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)


# Define a Flask form
class TextAreaForm(FlaskForm):
    writing_text = TextAreaField('Start Writing', [validators.InputRequired(message="Please enter text.")])
    submit = SubmitField()


class MemoryCreate(BaseModel):
    user_message: str
    llm_response: str
    conversations_summary: str
    published: Optional[bool] = True
    rating: Optional[int] = None

## Pydantic model for creating a new Memory_create record
# class MemoryCreate(Memory_create):
#    pass
#
#
## Pydantic model for returning a Memory_create record
# class MemoryRecord(Memory_create):
#    id: int
#    created_at: str  # Assuming you want to return the created_at timestamp as a string


# Heroku provides the DATABASE_URL environment variable
DATABASE_URL = os.environ['DATABASE_URL']
# conn = psycopg2.connect(DATABASE_URL, sslmode='require')


while True:
    try:
        conn = psycopg2.connect(
            f"postgresql://{os.environ['user']}:{os.environ['password']}@"
            f"{os.environ['host']}:{os.environ['port']}/{os.environ['database']}"
        )
        cursor = conn.cursor()
        print(f'Database connection was successful 😎\n')
        break
    except Exception as error:
        print(f'Connecting to database failed:\nError: {error} 😭\n')
        time.sleep(3)

# Create OMR table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS omr (
        id SERIAL PRIMARY KEY,
        user_message TEXT,
        llm_response TEXT,
        conversations_summary TEXT,
        published BOOLEAN,
        rating INTEGER,
        created_at TIMESTAMP
    )
""")
conn.commit()

# Creating the SQL command to fetch all data from the OMR table
memory_db = "SELECT * FROM omr"

# Executing the query and fetching all the data
cursor.execute(memory_db)
conversations_datas = cursor.fetchall()


def find_conversation_by_id(id):
    for converse in conversations_datas:
        if converse[0] == id:  # Assuming 'id' is the first column in the OMR table
            print(f'conversation by id: {converse}')
            return converse


def find_index_converse(id):
    for i, conv in enumerate(conversations_datas):
        if isinstance(conv, dict) and conv.get('id') == id:
            return i
        elif isinstance(conv, tuple) and conv[0] == id:  # Assuming the ID is the first element in the tuple
            return i
    return None


# Function to generate LLM response
def generate_llm_response(user_message):
    # Assuming 'conversation' is initialized as a ChatOpenAI object
    return conversation.predict(input=user_message)


@app.get("/", status_code=status.HTTP_201_CREATED)
async def root():
    return {"message: Be Good Doing Good By Acting Good ¡!¡": conversations_datas}


@app.get("/history", status_code=status.HTTP_201_CREATED)
def get_posts(db: Session = Depends(get_db)):
    # cursor.execute("""SELECT * FROM memories""")
    # posts = cursor.fetchall()(db: Session = Depends(get_db)):
    histories = db.query(models.Memory).all()
    print(f'posts:\n{histories} 👌🏿\n')
    return {"data": histories}


@app.get("/sqlalchemy", status_code=status.HTTP_201_CREATED)
def test_posts(db: Session = Depends(get_db)):
    memory_ = db.query(models.Memory).all()
    return {"data": memory_}


@app.post("/conversation", status_code=status.HTTP_201_CREATED, response_model=MemoryCreate)
def start_conversation(omr: MemoryCreate, db: Session = Depends(get_db)):
    try:
        # Use SQLAlchemy ORM to insert a new record
        new_memo = Memory(**omr.dict())

        # Get LLM response using the user's message
        llm_response = generate_llm_response(omr.user_message)

        # Update the new_memo with the LLM response
        new_memo.llm_response = llm_response

        db.add(new_memo)
        db.commit()
        db.refresh(new_memo)

        return new_memo
    except Exception as e:
        # Log the exception or print it for debugging
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    # cursor.execute(
    #    """
    #    INSERT INTO OMR (user_message, llm_response, conversations_summary, created_at) VALUES (%s, %s, %s, now())
    #    """,
    #    (user_message, llm_response, conversations_datas)
    # )
    # conn.commit()


#
## Fetch the conversation ID and timestamp
# cursor.execute("SELECT id, created_at FROM OMR ORDER BY id DESC LIMIT 1")
# last_entry = cursor.fetchone()
# conversation_id, created_at = last_entry if last_entry else (None, None)
#
## Format and return the conversation details
# conversation_dict = {
#    "user_message": user_message,
#    "llm_response": llm_response,
#    "published": True,
#    "created_at": created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else None,
#    "id": conversation_id
# }
#
# return {"conversation": conversation_dict}


@app.get("/audio", status_code=status.HTTP_201_CREATED)
async def audio_response():
    return {"message: Be Good Doing Good By Acting Good ¡!¡": conversations_datas[-1:]}


@app.get("/conversation-summary", status_code=status.HTTP_201_CREATED)
def get_conversation_summary():
    return {f"conversation_summary": conversations_datas[:3]}


@app.get("/conversation_by_id/{id}", status_code=status.HTTP_201_CREATED)
def get_conversation_by_id(id: int, response: Response):
    converse = find_conversation_by_id(id)
    if not converse:
        print(f'conversations_by_id: "{id}" was not found')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"conversations_by_id: '{id}' was not found'")
    return {"conversations_by_id:" f"{converse}"}


@app.put("/update-conversation/{id}", response_model=None)
def upd_conversation(id: int, memory: MemoryCreate, db: Session = Depends(get_db)):
    index = find_index_converse(id)
    if index is None:
        print(f'Conversation with ID: {id} does not exist')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID: {id} does not exist"
        )

    # Update the conversation details in the list
    conversations_datas[index] = (
        memory.user_message,
        memory.llm_response,
        memory.conversations_summary,
        memory.published,
        memory.rating,
        memory.created_at
    )

    # Logging the conversation update
    print(f'Conversation with ID: {id} updated:\n{conversations_datas[index]}')
    return {"message": f"Conversation with ID: {id} has been updated:\n{conversations_datas[index]}"}


@app.delete("/delete-conversation/{id}", status_code=status.HTTP_204_NO_CONTENT)
def del_conversation(id: int):
    index = find_index_converse(id)
    if index == None:
        print(f'conversations_by_id: "{id}" does not exist')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"conversation with id: '{id}' does not exist")
    conversations_datas.pop(index)
    print(f'"message": "conversation was successfully deleted"')
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
