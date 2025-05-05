# Social Media Data Processing Pipeline

This project is a data processing pipeline that scrapes, processes, and stores social media data. It uses Celery for task management, MinIO for storage, and Selenium for web scraping.

## Project Structure

- `scrapers/`: Contains social media scraping logic
- `extractors/`: Data extraction and processing modules
- `config/`: Configuration files
- `celery_tasks/`: Celery task definitions
- `models/`: Data models
- `tests/`: Test files
- `storage/`: Storage-related code

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- Poetry for dependency management

## Setup

1. Clone the repository
2. Copy `.env-example` to `.env` and fill in your credentials:

   ```bash
   cp .env-example .env
   ```

3. Install dependencies:

   ```bash
   poetry install
   ```

## Running the Project

Start all services using Docker Compose:

```bash
make run-dev-build
```

This will start:

- MinIO (object storage) on port 9000
- Redis (message broker) on port 6379
- Selenium Chrome on port 4444
- Celery workers for different tasks
- Flower (Celery monitoring) on port 5555
- Streamlit web interface on port 8501

## Usage

To crawl a user's profile posts and Media you can use the streamlit interface available on Port 8501.
Select the website where the user is subscribed and provide a username. To update the status of execution click on the refresh button.

## Services

- **Crawler Worker**: Handles social media data scraping
- **Processor Worker**: Processes scraped data
- **Storage Worker**: Manages data storage in MinIO
- **Media Worker**: Handles media file processing
- **Flower**: Monitors Celery tasks
- **Streamlit**: Web interface for data visualization

## Configuration

The project uses environment variables for configuration. Key settings include:

- Celery configuration (broker and backend)
- Selenium hub URL
- MinIO credentials
- Snowflake database settings
- social media credentials

## Development

- Run tests:

  ```bash
  make test
  ```

- Format code:
  
  ```bash
  make formatter
  ```

- lint checking:
  
  ```bash
  make lint
  ```

## License

This project is licensed under the terms specified in the LICENSE file.
