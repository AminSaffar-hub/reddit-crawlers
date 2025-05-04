import time
from datetime import datetime, timedelta

import streamlit as st

from celery_app import app
from celery_tasks import tasks

st.set_page_config(page_title="Social Media Scraper", layout="wide")

if "tasks" not in st.session_state:
    st.session_state.tasks = {}


def submit_scraping_task(author_name, source_type):
    """Submit a new scraping task and return the task ID"""
    try:
        task = tasks.crawl_author.delay(
            author_name=author_name,
            date_start=datetime.now() - timedelta(days=21),
            source_type=source_type,
        )
        return task.id
    except Exception as e:
        st.error(f"Error submitting task: {str(e)}")
        return None


def get_task_status(task_id):
    """Get the status of a Celery task"""
    try:
        task = app.AsyncResult(task_id)
        return {
            "status": task.status,
            "result": task.result,
            "error": str(task.traceback) if task.failed() else None,
        }
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


st.title("Social Media User Scraper")

with st.form("scraper_form"):
    col1, col2 = st.columns(2)
    with col1:
        source_type = st.selectbox(
            "Select source type",
            options=["reddit", "linkedin"],
            help="Choose the social media platform to scrape from",
        )
    with col2:
        author_name = st.text_input(
            f"Enter {source_type.capitalize()} username",
            placeholder=f"e.g., {'CozyBvnnies' if source_type == 'reddit' else 'etnikhalili'}",
        )
    submitted = st.form_submit_button("Start Scraping")

if submitted and author_name:
    task_id = submit_scraping_task(author_name, source_type)
    if task_id:
        st.session_state.tasks[task_id] = {
            "author_name": author_name,
            "source_type": source_type,
            "start_time": datetime.now(),
            "status": "PENDING",
        }
        st.success(
            f"Started scraping for {source_type.capitalize()} user: {author_name}"
        )

if st.session_state.tasks:
    st.header("Active Tasks")

    for task_id, task_info in list(st.session_state.tasks.items()):
        with st.expander(
            f"{task_info['source_type'].capitalize()} Task for {task_info['author_name']}"
        ):
            status = get_task_status(task_id)

            st.session_state.tasks[task_id]["status"] = status["status"]

            if status["status"] == "SUCCESS":
                st.success(f"✅ Task completed successfully!")
                st.write(f"Author ID: {status['result']}")
            elif status["status"] == "FAILURE":
                st.error(f"❌ Task failed: {status['error']}")
            elif status["status"] == "PENDING":
                st.info("⏳ Task is pending...")
            else:
                st.info(f"🔄 Task is {status['status']}...")

            elapsed = datetime.now() - task_info["start_time"]
            st.write(f"Elapsed time: {str(elapsed).split('.')[0]}")

            if status["status"] in ["SUCCESS", "FAILURE"]:
                if st.button(
                    f"Remove task for {task_info['author_name']}",
                    key=f"remove_{task_id}",
                ):
                    del st.session_state.tasks[task_id]
                    st.rerun()
