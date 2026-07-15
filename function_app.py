import os
import json
import logging
import pymssql
import azure.functions as func

app = func.FunctionApp()


def get_sql_connection():
    server = os.environ["SQL_SERVER"]
    database = os.environ["SQL_DATABASE"]
    username = os.environ["SQL_USER"]
    password = os.environ["SQL_PASSWORD"]

    return pymssql.connect(
        server=server,
        database=database,
        user=username,
        password=password,
    )


@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"status": "ok"}),
        mimetype="application/json",
        status_code=200,
    )


@app.route(route="customers", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def create_customer(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        customer_id = int(body["id"])
        name = body["name"]
        salary = float(body["salary"])
        address = body["address"]
    except (ValueError, KeyError, TypeError) as ex:
        return func.HttpResponse(
            json.dumps({"error": f"Invalid request body: {ex}"}),
            mimetype="application/json",
            status_code=400,
        )

    try:
        conn = get_sql_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Customers (CustomerId, Name, Salary, Address)
            VALUES (%s, %s, %s, %s)
            """,
            (customer_id, name, salary, address),
        )
        conn.commit()
        cursor.close()
        conn.close()

        return func.HttpResponse(
            json.dumps({
                "message": "Customer loaded into Cloud SQL",
                "customer_id": customer_id,
            }),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as ex:
        logging.error(f"SQL insert failed: {ex}")
        return func.HttpResponse(
            json.dumps({"error": str(ex)}),
            mimetype="application/json",
            status_code=500,
        )