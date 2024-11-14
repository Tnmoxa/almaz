import xml.etree.ElementTree as ET
from datetime import datetime, date

from fastapi import FastAPI, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from almaz.celery.tasks import fetch_sales_data
from almaz.database import storage_models as sm
from almaz.dependencies import database, logger, lifespan

app = FastAPI(lifespan=lifespan)


@app.post("/process_sales")
async def fetch_xml(request: Request, db: AsyncSession = Depends(database)):
    """
        Обрабатывает данные о продажах, полученные в формате XML, сохраняет их в базе данных
        и отправляет задачу в Celery для анализа данных.

        Данная функция ожидает, что XML данные будут переданы в теле POST-запроса. Она извлекает информацию
        о продажах, включая дату, товарные данные, количество и цену каждого товара, и сохраняет их в базу данных.
        После обработки данных отправляется задача в Celery для анализа продаж и составления отчета с рекомендациями.

        Args:
            request (Request): Объект запроса FastAPI, содержащий XML данные.
            db (AsyncSession, optional): Объект сессии базы данных, автоматически передаваемый через зависимость.

        Raises:
            HTTPException: Если данные XML некорректны или содержат ошибки в формате данных о товаре, будет выброшено
            исключение с подробным описанием ошибки.

        Returns:
            dict: Ответ с состоянием успешной обработки данных и отправки задачи в Celery.
        """
    try:
        xml_data = await request.body()
        data = ET.fromstring(xml_data)
        sales_date = data.attrib.get("date", date.today().isoformat())
    except ET.ParseError as e:
        logger.error(f"Ошибка парсинга XML: {str(e)}")
        raise HTTPException(status_code=404, detail={"error": "Invalid XML format", "details": str(e)})

    total_revenue = 0
    product_sales = []
    category_sales = {}
    for product in data.find("products").findall("product"):
        try:
            product_data = {
                "date": datetime.strptime(sales_date, "%Y-%m-%d").date(),
                "product_id": int(product.find("id").text),
                "name": product.find("name").text,
                "quantity": int(product.find("quantity").text),
                "price": float(product.find("price").text),
                "category": product.find("category").text
            }
            logger.info(f"Обработан продукт: {product_data['name']}")
        except (ValueError, AttributeError) as e:
            logger.error(f"Ошибка обработки данных продукта: {str(e)}")
            raise HTTPException(status_code=404, detail={"error": "Invalid product data format", "details": str(e)})

        sales_entry = sm.SalesData(**product_data)

        db.add(sales_entry)
        total_revenue += product_data["quantity"] * product_data["price"]

        product_sales.append(product_data)

        category = product_data["category"]
        category_sales[category] = category_sales.get(category, 0) + product_data["quantity"]
    try:
        top_products = sorted(product_sales, key=lambda p: p["quantity"], reverse=True)[:3]
        top_products = [(p["name"], p["quantity"]) for p in top_products]

        prompt = f"""
        Данные о продажах за {sales_date}:
    
        1. Общая выручка: {total_revenue} (по всем товарам).
        2. Топ-3 товара по количеству проданных единиц:
           - {top_products[0][0]}: {top_products[0][1]} единиц
           - {top_products[1][0]}: {top_products[1][1]} единиц
           - {top_products[2][0]}: {top_products[2][1]} единиц
        3. Распределение продаж по категориям:
           {', '.join([f'{category}: {quantity}' for category, quantity in category_sales.items()])}
    
        Проанализируй эти данные и составь подробный отчет с рекомендациями по улучшению продаж:
        - Обсуди, какие товары и категории показали наилучшие результаты.
        - Укажи, какие товары или категории имеют потенциал для улучшения.
        - Дай рекомендации по повышению продаж в наименее активных категориях или товарах.
        - Какие действия можно предпринять, чтобы увеличить общую выручку на основе данных.
    
        Пожалуйста, предоставь отчет в виде четких рекомендаций.
        """
        logger.info("Отправка задачи для анализа данных в Celery")
        fetch_sales_data.delay(sales_date, prompt)
        await db.commit()
        logger.info("Обработка данных завершена и данные сохранены в базе")
        return {"status": "Success", "message": "Data processed and task sent to Celery"}
    except Exception as e:
        if e.args == (-3, 'Temporary failure in name resolution'):
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise HTTPException(status_code=404,
                                detail={"error": "Database connection failed. Please try again later."})
        logger.error(f"Ошибка при обработке данных продаж: {str(e)}")
        raise HTTPException(status_code=404, detail={"error": "An error occurred during processing", "details": str(e)})
