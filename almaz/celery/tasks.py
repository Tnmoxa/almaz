import os
from datetime import datetime

from dotenv import load_dotenv
from openai import RateLimitError, PermissionDeniedError
import almaz.database.storage_models as sm
from almaz.celery.celery_app import celery_app
from almaz.dependencies import sync_database, openai_api, logger

load_dotenv()


@celery_app.task
def fetch_sales_data(sales_date, prompt):
    try:
        with sync_database() as db:
            logger.info(f"Начало обработки задачи для даты {sales_date}")
            response = openai_api.openai_api_chat.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            llm_response = response['choices'][0]['message']['content']
            logger.info("Ответ от модели GPT-3.5-turbo получен успешно")

            llm_entry = sm.LLMAnalysisResult(
                date=datetime.strptime(sales_date, "%Y-%m-%d").date(),
                prompt=prompt,
                response=llm_response
            )
            db.add(llm_entry)

            db.commit()
            logger.info(f"Результаты анализа сохранены в базе данных для даты {sales_date}")

    except RateLimitError:
        logger.error('Ответ модели не получен: на аккаунте недостаточно средств.')

    except PermissionDeniedError:
        logger.error('Ответ модели не получен: запросы из России запрещены, укажите урл sock5.')
    except Exception as e:
        logger.error(f"Произошла ошибка во время работы Celery {e}")