from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy import UniqueConstraint

from app.config.database import Base
from app import models  # noqa: F401

SQL_PATH = Path(__file__).resolve().parents[1] / "sql" / "init.sql"
CREATE_TABLE_PATTERN = re.compile(
    r"CREATE TABLE IF NOT EXISTS\s+(\w+)\s*\((.*?)\)\s*ENGINE=InnoDB;",
    flags=re.IGNORECASE | re.DOTALL,
)
UNIQUE_PATTERN = re.compile(
    r"UNIQUE KEY\s+\w+\s*\(([^)]+)\)",
    flags=re.IGNORECASE,
)
KEY_PATTERN = re.compile(
    r"(?<!UNIQUE )KEY\s+\w+\s*\(([^)]+)\)",
    flags=re.IGNORECASE,
)
FOREIGN_PATTERN = re.compile(
    r"CONSTRAINT\s+\w+\s+FOREIGN KEY\s+\((\w+)\)\s+"
    r"REFERENCES\s+(\w+)\((\w+)\)"
    r"(?:\s+ON DELETE\s+(\w+(?:\s+\w+)?))?",
    flags=re.IGNORECASE,
)


def _column_names(definition: str) -> list[str]:
    names: list[str] = []
    for raw_line in definition.splitlines():
        line = raw_line.strip().rstrip(",")
        if not line or line.upper().startswith(
            (
                "PRIMARY KEY",
                "UNIQUE KEY",
                "KEY ",
                "CONSTRAINT ",
            )
        ):
            continue
        names.append(line.split()[0])
    return names


def _index_columns(pattern: re.Pattern[str], definition: str) -> set[str]:
    columns: set[str] = set()
    for match in pattern.finditer(definition):
        columns.update(
            item.strip()
            for item in match.group(1).split(",")
        )
    return columns


def _unique_constraints(definition: str) -> set[tuple[str, ...]]:
    result = {
        tuple(
            item.strip()
            for item in match.group(1).split(",")
        )
        for match in UNIQUE_PATTERN.finditer(definition)
    }
    return result


def _foreign_keys(
    definition: str,
) -> dict[str, tuple[str, str, str | None]]:
    result: dict[str, tuple[str, str, str | None]] = {}
    for match in FOREIGN_PATTERN.finditer(definition):
        local_column, table, remote_column, action = match.groups()
        result[local_column] = (
            f"{table}.{remote_column}",
            table,
            action.upper() if action else None,
        )
    return result


def test_chat_orm_matches_mysql_ddl_baseline():
    sql = SQL_PATH.read_text(encoding="utf-8")
    definitions = {
        table_name: definition
        for table_name, definition in CREATE_TABLE_PATTERN.findall(sql)
    }

    for table_name in ("ai_chat_session", "ai_chat_message"):
        assert table_name in definitions
        table = Base.metadata.tables[table_name]
        definition = definitions[table_name]

        assert set(_column_names(definition)) == {
            column.name for column in table.columns
        }

        orm_unique: set[tuple[str, ...]] = set()
        for constraint in table.constraints:
            if isinstance(constraint, UniqueConstraint):
                orm_unique.add(
                    tuple(column.name for column in constraint.columns)
                )
        for index in table.indexes:
            if index.unique:
                orm_unique.add(
                    tuple(column.name for column in index.columns)
                )
        assert _unique_constraints(definition) == orm_unique

        orm_foreign_keys = {
            foreign_key.parent.name: (
                foreign_key.target_fullname,
                foreign_key.target_fullname.split(".", 1)[0],
                (
                    foreign_key.ondelete.upper()
                    if foreign_key.ondelete
                    else None
                ),
            )
            for foreign_key in table.foreign_keys
        }
        assert _foreign_keys(definition) == orm_foreign_keys

        orm_indexed_columns = {
            column.name
            for column in table.columns
            if column.index
        }
        ddl_indexed_columns = _index_columns(
            UNIQUE_PATTERN,
            definition,
        ) | _index_columns(KEY_PATTERN, definition)
        assert orm_indexed_columns <= ddl_indexed_columns
