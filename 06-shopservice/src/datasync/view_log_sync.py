import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pymysql
from pymysql.cursors import DictCursor
from neo4j import GraphDatabase

from src.schema.config import get_config


def read_user_view_log(config):
    """从 MySQL 读取用户浏览记录"""
    with pymysql.connect(
        host=config.mysql_host,
        port=config.mysql_port,
        user=config.mysql_user,
        password=config.mysql_password,
        database=config.mysql_database,
        charset=config.mysql_charset or "utf8mb4"
    ) as conn:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute("""
                SELECT
                    v.user_id,
                    v.sku_id,
                    s.sku_name,
                    v.view_time
                FROM user_view_log v
                JOIN sku_info s ON v.sku_id = s.id
                ORDER BY v.id
            """)
            return cursor.fetchall()


def write_user_view_log(config, user_view_log):
    """将用户浏览记录同步到 Neo4j"""
    with GraphDatabase.driver(
        config.neo4j_uri,
        auth=(config.neo4j_user, config.neo4j_password)
    ) as driver:

        driver.verify_connectivity()

        for log in user_view_log:
            driver.execute_query(
                """
                MERGE (u:User {user_id: $user_id})
                MERGE (s:SKU {sku_id: $sku_id})
                SET s.sku_name = $sku_name
                MERGE (u)-[:View]->(s)
                """,
                user_id=log["user_id"],
                sku_id=log["sku_id"],
                sku_name=log["sku_name"],
                database_=config.neo4j_database
            )

    print(f"成功同步 {len(user_view_log)} 条浏览记录")


if __name__ == "__main__":
    try:
        config = get_config()

        logs = read_user_view_log(config)
        print(f"从 MySQL 读取到 {len(logs)} 条浏览记录")

        write_user_view_log(config, logs)
        print("用户行为数据入库成功！")

    except Exception as e:
        print(f"用户行为数据入库失败：{e}")
        raise