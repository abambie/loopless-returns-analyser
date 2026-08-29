"""Database access for the Loopless application.

SQLite is the zero-configuration default for portfolio reviewers. The same
repository interface can use MySQL when environment variables are supplied.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from config import DB_BACKEND, SQLITE_PATH, get_mysql_config


FilterMap = Dict[str, Any]


@dataclass
class DataRepository:
    backend: str = DB_BACKEND
    sqlite_path: Path | str = SQLITE_PATH
    mysql_config: Optional[Dict[str, str]] = None
    connection: Any = field(default=None, repr=False)
    is_connected: bool = False
    TABLE_NAME: str = "purchases"

    FILTER_COLUMNS = {
        "category",
        "brand",
        "season",
        "size",
        "color",
        "product_id",
    }
    DATE_COLUMNS = {"purchase_date", "return_date"}

    def __post_init__(self) -> None:
        self.backend = self.backend.strip().lower()
        if self.backend not in {"sqlite", "mysql"}:
            raise ValueError("backend must be either 'sqlite' or 'mysql'.")
        self.sqlite_path = Path(self.sqlite_path) if self.sqlite_path != ":memory:" else ":memory:"

    @property
    def placeholder(self) -> str:
        return "?" if self.backend == "sqlite" else "%s"

    def connect(self) -> None:
        if self._connection_is_live():
            return

        if self.backend == "sqlite":
            if self.sqlite_path != ":memory:":
                Path(self.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(str(self.sqlite_path), check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        else:
            try:
                import mysql.connector
            except ImportError as exc:
                raise RuntimeError(
                    "MySQL support requires: pip install mysql-connector-python"
                ) from exc
            settings = self.mysql_config or get_mysql_config()
            self.connection = mysql.connector.connect(**settings)

        self.is_connected = True

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
        self.connection = None
        self.is_connected = False

    def initialise(self, csv_path: Path | str, required_columns: Sequence[str]) -> int:
        """Create the schema and import the bundled CSV when the table is empty."""

        self.connect()
        self.execute(self._create_table_sql())
        count = int(self.query(f"SELECT COUNT(*) AS n FROM {self.TABLE_NAME}")[0]["n"])
        if count:
            return count

        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"Dataset not found: {csv_path}")

        df = pd.read_csv(csv_path)
        df.columns = [column.strip().lower().replace(" ", "_") for column in df.columns]
        for column in required_columns:
            if column not in df.columns:
                df[column] = None
        df = df[list(required_columns)].copy()
        df["is_returned"] = df["is_returned"].map(
            lambda value: 1 if str(value).strip().lower() in {"1", "true", "yes"} else 0
        )
        for column in ("purchase_date", "return_date"):
            if column in df.columns:
                df[column] = df[column].where(pd.notna(df[column]), None)

        self.insert_dataframe(self.TABLE_NAME, df)
        return len(df)

    def reset_from_csv(self, csv_path: Path | str, required_columns: Sequence[str]) -> int:
        self.connect()
        self.execute(f"DROP TABLE IF EXISTS {self.TABLE_NAME}")
        return self.initialise(csv_path, required_columns)

    def execute(self, sql: str, params: Tuple[Any, ...] = ()) -> None:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        self.connection.commit()
        cursor.close()

    def query(self, sql: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        self._ensure_connected()
        if self.backend == "mysql":
            cursor = self.connection.cursor(dictionary=True)
        else:
            cursor = self.connection.cursor()
        cursor.execute(sql, params)
        rows = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return rows

    def load_dataset(self, filters: FilterMap = None) -> pd.DataFrame:
        filters = filters or {}
        where_sql, params = self._build_where_clause(filters)
        rows = self.query(f"SELECT * FROM {self.TABLE_NAME} {where_sql}", params)
        df = pd.DataFrame(rows)
        for column in ("purchase_date", "return_date"):
            if not df.empty and column in df.columns:
                df[column] = pd.to_datetime(df[column], errors="coerce")
        return df

    def insert_dataframe(self, table_name: str, df: pd.DataFrame) -> int:
        self._ensure_connected()
        if df.empty:
            return 0
        if table_name != self.TABLE_NAME:
            raise ValueError("Unsupported table name.")

        columns = list(df.columns)
        placeholders = ", ".join([self.placeholder] * len(columns))
        column_names = ", ".join(f"`{column}`" for column in columns)
        sql = f"INSERT INTO `{table_name}` ({column_names}) VALUES ({placeholders})"
        rows = [
            tuple(None if pd.isna(value) else value for value in row)
            for row in df.itertuples(index=False, name=None)
        ]
        cursor = self.connection.cursor()
        cursor.executemany(sql, rows)
        self.connection.commit()
        cursor.close()
        return len(rows)

    def get_distinct_values(self, column: str, filters: FilterMap = None) -> List[str]:
        if column not in self.FILTER_COLUMNS:
            raise ValueError(f"Unsupported filter column: {column}")
        where_sql, params = self._build_where_clause(filters or {})
        rows = self.query(
            f"SELECT DISTINCT `{column}` AS v FROM {self.TABLE_NAME} "
            f"{where_sql} ORDER BY v",
            params,
        )
        return [str(row["v"]) for row in rows if row.get("v") is not None]

    def get_date_range(self, date_column: str = "purchase_date") -> Tuple[Any, Any]:
        if date_column not in self.DATE_COLUMNS:
            raise ValueError(f"Unsupported date column: {date_column}")
        rows = self.query(
            f"SELECT MIN(`{date_column}`) AS min_d, MAX(`{date_column}`) AS max_d "
            f"FROM {self.TABLE_NAME}"
        )
        if not rows:
            return (None, None)
        return (rows[0].get("min_d"), rows[0].get("max_d"))

    def _connection_is_live(self) -> bool:
        if self.connection is None:
            return False
        if self.backend == "sqlite":
            return True
        try:
            return bool(self.connection.is_connected())
        except Exception:
            return False

    def _ensure_connected(self) -> None:
        if not self._connection_is_live():
            self.connect()

    def _build_where_clause(self, filters: FilterMap) -> Tuple[str, Tuple[Any, ...]]:
        clauses: List[str] = []
        params: List[Any] = []

        for column in sorted(self.FILTER_COLUMNS):
            if column in filters and filters[column] not in (None, "", []):
                clauses.append(f"`{column}` = {self.placeholder}")
                params.append(filters[column])

        if filters.get("is_returned") is not None:
            clauses.append(f"`is_returned` = {self.placeholder}")
            params.append(int(filters["is_returned"]))
        if filters.get("min_price") is not None:
            clauses.append(f"`current_price` >= {self.placeholder}")
            params.append(float(filters["min_price"]))
        if filters.get("max_price") is not None:
            clauses.append(f"`current_price` <= {self.placeholder}")
            params.append(float(filters["max_price"]))
        if filters.get("date_from"):
            clauses.append(f"`purchase_date` >= {self.placeholder}")
            params.append(str(filters["date_from"]))
        if filters.get("date_to"):
            clauses.append(f"`purchase_date` <= {self.placeholder}")
            params.append(str(filters["date_to"]))

        if not clauses:
            return ("", ())
        return ("WHERE " + " AND ".join(clauses), tuple(params))

    def _create_table_sql(self) -> str:
        id_column = (
            "id INTEGER PRIMARY KEY AUTOINCREMENT"
            if self.backend == "sqlite"
            else "id INT AUTO_INCREMENT PRIMARY KEY"
        )
        return f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                {id_column},
                product_id VARCHAR(50),
                category VARCHAR(100),
                brand VARCHAR(100),
                season VARCHAR(50),
                size VARCHAR(20),
                color VARCHAR(50),
                original_price FLOAT,
                markdown_percentage FLOAT,
                current_price FLOAT,
                purchase_date DATE,
                stock_quantity INT,
                customer_rating FLOAT,
                is_returned SMALLINT DEFAULT 0,
                return_reason VARCHAR(255),
                return_date DATE
            )
        """
