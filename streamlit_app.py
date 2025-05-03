import streamlit as st
from datetime import datetime, timedelta
import time

from celery_app import app
from celery_tasks import tasks

st.set_page_config(page_title="Reddit Scraper", layout="wide")

if "tasks" not in st.session_state:
    st.session_state.tasks = {}


def submit_scraping_task(author_name):
    """Submit a new scraping task and return the task ID"""
    try:
        task = tasks.crawl_reddit_author.delay(
            author_name=author_name, date_start=datetime.now() - timedelta(days=21)
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


st.title("Reddit User Scraper")

with st.form("scraper_form"):
    author_name = st.text_input(
        "Enter Reddit username", placeholder="e.g., CozyBvnnies"
    )
    submitted = st.form_submit_button("Start Scraping")

if submitted and author_name:
    task_id = submit_scraping_task(author_name)
    if task_id:
        st.session_state.tasks[task_id] = {
            "author_name": author_name,
            "start_time": datetime.now(),
            "status": "PENDING",
        }
        st.success(f"Started scraping for user: {author_name}")

if st.session_state.tasks:
    st.header("Active Tasks")

    for task_id, task_info in list(st.session_state.tasks.items()):
        with st.expander(f"Task for {task_info['author_name']}"):
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
