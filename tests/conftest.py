# tests/e2e/conftest.py

import subprocess
import time
import pytest
from playwright.sync_api import sync_playwright
import requests
import logging
from typing import Generator, Dict, List
from contextlib import contextmanager
import requests
from faker import Faker
from playwright.sync_api import sync_playwright, Browser, Page
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.database import Base, get_engine, get_sessionmaker
from app.models.user import User
from app.config import settings
from app.database_init import init_db, drop_db

@pytest.fixture(scope='session')
def fastapi_server():
    """
    Fixture to start the FastAPI server before E2E tests and stop it after tests complete.
    """
    # Start FastAPI app
    fastapi_process = subprocess.Popen(['python', 'main.py'])
    
    # Define the URL to check if the server is up
    server_url = 'http://127.0.0.1:8000/'
    
    # Wait for the server to start by polling the root endpoint
    timeout = 30  # seconds
    start_time = time.time()
    server_up = False
    
    print("Starting FastAPI server...")
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(server_url)
            if response.status_code == 200:
                server_up = True
                print("FastAPI server is up and running.")
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    
    if not server_up:
        fastapi_process.terminate()
        raise RuntimeError("FastAPI server failed to start within timeout period.")
    
    yield
    
    # Terminate FastAPI server
    print("Shutting down FastAPI server...")
    fastapi_process.terminate()
    fastapi_process.wait()
    print("FastAPI server has been terminated.")

@pytest.fixture(scope="session")
def playwright_instance_fixture():
    """
    Fixture to manage Playwright's lifecycle.
    """
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def browser(playwright_instance_fixture):
    """
    Fixture to launch a browser instance.
    """
    browser = playwright_instance_fixture.chromium.launch(headless=True)
    yield browser
    browser.close()

@pytest.fixture(scope="function")
def page(browser):
    """
    Fixture to create a new page for each test.
    """
    page = browser.new_page()
    yield page
    page.close()

def create_fake_user() -> Dict[str, str]:
    return {
        "username": Faker().user_name(),
        "email": Faker().email(),
        "first_name": Faker().first_name(),
        "last_name": Faker().last_name(),
        "password": Faker().password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    }
def managed_db_session() -> Generator[Session, None, None]:
    """
    Context manager to handle database sessions.
    """
    engine = get_engine()
    SessionLocal = get_sessionmaker(engine)
    
    db_session = SessionLocal()
    try:
        yield db_session
    except SQLAlchemyError as e:
        db_session.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        db_session.close()