"""DocuSphere v2: FastAPI app with local login, private document access and RAG."""
import logging
import sqlite3
import uuid
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from starlette.concurrency import run_in_threadpool

from auth import (create_token, ensure_secret, get_current_user,
                  hash_password, verify_password)
from config import MAX_PDF_BYTES
from database import (init_db, find_user_by_email, add_user, list_documents,
                      find_document, remove_document, save_chat_turn,
                      load_chat_messages, delete_chat_history)
from rag import (answer, delete_vectors_for_document, extract_pdf_pages,
                 extract_public_webpage, ingest_sections)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_secret()
    yield

app = FastAPI(title='DocuSphere AI', version='2.0.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    allow_credentials=False, allow_methods=['GET','POST','DELETE'],
    allow_headers=['Authorization','Content-Type'])

class AuthRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UrlRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)

class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

@app.get('/health')
def health_check():
    return {'status': 'ok', 'version': '2.0.0'}

@app.post('/auth/register', status_code=201)
def register(body: AuthRequest):
    email = str(body.email).lower().strip()
    if find_user_by_email(email):
        raise HTTPException(status_code=409, detail='Email already registered')
    user_id = str(uuid.uuid4())
    try:
        add_user(user_id, email, hash_password(body.password))
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail='Email already registered')
    return {'access_token': create_token(user_id), 'token_type': 'bearer',
            'user': {'id': user_id, 'email': email}}

@app.post('/auth/login')
def login(body: AuthRequest):
    user = find_user_by_email(str(body.email).lower().strip())
    if not user or not verify_password(body.password, user['password_hash']):
        raise HTTPException(status_code=401, detail='Invalid email or password')
    return {'access_token': create_token(user['id']), 'token_type': 'bearer',
            'user': {'id': user['id'], 'email': user['email']}}

@app.get('/auth/me')
def me(user=Depends(get_current_user)):
    return user

@app.get('/documents')
def documents(user=Depends(get_current_user)):
    return {'documents': list_documents(user['id'])}

@app.post('/ingest/pdf', status_code=201)
async def ingest_pdf(file: UploadFile = File(...), user=Depends(get_current_user)):
    filename = (file.filename or '').split('/')[-1].split('\\')[-1][:180]
    if not filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail='Only PDF files are accepted')
    content = await file.read(MAX_PDF_BYTES + 1)
    await file.close()
    if len(content) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail='PDF too large; max 10 MB')
    if not content.startswith(b'%PDF-'):
        raise HTTPException(status_code=422, detail='File is not a valid PDF')
    sections = await run_in_threadpool(extract_pdf_pages, content)
    try:
        return await run_in_threadpool(ingest_sections, user['id'], filename, 'pdf', sections)
    except HTTPException:
        raise
    except Exception as error:
        logger.exception('PDF ingestion error')
        raise HTTPException(status_code=500, detail='Unable to ingest PDF') from error

@app.post('/ingest/url', status_code=201)
async def ingest_url(body: UrlRequest, user=Depends(get_current_user)):
    text, final_url = await extract_public_webpage(body.url)
    parsed = urlparse(final_url)
    name = f'{parsed.netloc}{parsed.path}'[:180] or 'Web document'
    try:
        return await run_in_threadpool(ingest_sections, user['id'], name, 'url', [(None, text)], final_url)
    except HTTPException:
        raise
    except Exception as error:
        logger.exception('URL ingestion error')
        raise HTTPException(status_code=500, detail='Unable to ingest URL') from error

@app.get('/chat/history')
def chat_history(user=Depends(get_current_user)):
    return {'messages': load_chat_messages(user['id'])}

@app.delete('/chat/history')
def clear_chat_history(user=Depends(get_current_user)):
    delete_chat_history(user['id'])
    return {'cleared': True}

@app.post('/query')
def query(body: QueryRequest, user=Depends(get_current_user)):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail='Question cannot be empty')
    if not list_documents(user['id']):
        return {'answer': 'Please upload a document first.', 'sources': [],
                'confidence': 'no_match', 'matched_chunks': 0}
    try:
        result = answer(user['id'], question)
        save_chat_turn(user['id'], question, result)
        return result
    except HTTPException:
        raise
    except Exception as error:
        logger.exception('Query failed')
        raise HTTPException(status_code=502, detail='Answer generation failed. Check embedding model/Groq API.') from error

@app.delete('/documents/{document_id}')
def delete_document(document_id: str, user=Depends(get_current_user)):
    if not find_document(user['id'], document_id):
        raise HTTPException(status_code=404, detail='Document not found')
    try:
        delete_vectors_for_document(document_id)
        remove_document(user['id'], document_id)
    except Exception as error:
        logger.exception('Document delete failed')
        raise HTTPException(status_code=502, detail='Could not delete document') from error
    return {'deleted': True, 'document_id': document_id}
