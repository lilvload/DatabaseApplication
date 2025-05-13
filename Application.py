import customtkinter as ct
import pyodbc
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox

# Підключення до БД
connection = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=DESKTOP-ALGL9A7;'
    'DATABASE=PizzaDeliveryDB;'
    'Trusted_Connection=yes;'
)
cursor = connection.cursor()

ct.set_appearance_mode("system")
ct.set_default_color_theme("blue")

app = ct.CTk()
app.geometry("1000x600")
app.title("Головна сторінка додатку")

content_frame = ct.CTkFrame(app)
content_frame.pack(fill="both", expand=True, padx=20, pady=10)

def show_main_menu():
    for widget in content_frame.winfo_children():
        widget.destroy()

    ct.CTkLabel(content_frame, text="Entities", font=ct.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
    ct.CTkLabel(content_frame, text="Click on an entity to view/edit its content").pack(pady=(0, 20))

    tables = [
        'Bakeries', 'CourierAssignments', 'Couriers', 'Customers', 'DeliveryTracking', 'OrderDetails',
        'Orders', 'Payments', 'Pizzas'
    ]

    for table in tables:
        ct.CTkButton(content_frame, text=table, width=300,
                     anchor="w", command=lambda t=table: show_table_view(t)).pack(pady=5)

    ct.CTkButton(content_frame, text="About", width=300, command=show_about_window).pack(pady=40)

def show_table_view(table_name):
    for widget in content_frame.winfo_children():
        widget.destroy()

    back_button = ct.CTkButton(content_frame, text="← Back", command=show_main_menu)
    back_button.pack(anchor="w", pady=(10, 10))

    label = ct.CTkLabel(content_frame, text=f"{table_name} table view", font=ct.CTkFont(size=16, weight="bold"))
    label.pack(pady=5)

    # Пошук
    search_frame = ct.CTkFrame(content_frame)
    search_frame.pack(pady=5)

    search_entry = ct.CTkEntry(search_frame, placeholder_text="Search...")
    search_entry.pack(side="left", padx=5)

    # Кнопка додавання нового рядка
    add_button = ct.CTkButton(content_frame, text="Add New Row", command=lambda: open_add_window(table_name))
    add_button.pack(pady=5)

    tree_frame = ct.CTkFrame(content_frame)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()

        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")

        # Вставка рядків + зберігаємо всі iid
        all_iids = []
        for row in rows:
            cleaned_row = [str(cell) if cell is not None else "" for cell in row]
            iid = tree.insert("", "end", values=cleaned_row)
            all_iids.append(iid)

        def perform_search():
            query = search_entry.get().lower()
            for iid in all_iids:
                values = tree.item(iid, "values")
                if any(query in str(value).lower() for value in values):
                    tree.reattach(iid, '', 'end')
                else:
                    tree.detach(iid)

        def show_all_rows():
            for iid in all_iids:
                tree.reattach(iid, '', 'end')

        # Кнопки пошуку та показу всіх рядків
        search_button = ct.CTkButton(search_frame, text="Search", command=perform_search)
        search_button.pack(side="left", padx=5)

        show_all_button = ct.CTkButton(search_frame, text="Show All", command=show_all_rows)
        show_all_button.pack(side="left", padx=5)

        def edit_selected_row():
            selected = tree.selection()
            if not selected:
                return
            row_values = tree.item(selected[0], "values")
            open_edit_window(table_name, columns, row_values)

        def delete_selected_row():
            selected = tree.selection()
            if not selected:
                return
            row_values = tree.item(selected[0], "values")
            confirm_delete(table_name, columns[0], row_values[0])

        edit_button = ct.CTkButton(content_frame, text="Edit Selected Row", command=edit_selected_row)
        edit_button.pack(pady=5)

        delete_button = ct.CTkButton(content_frame, text="Delete Selected Row", command=delete_selected_row)
        delete_button.pack(pady=5)

    except pyodbc.Error as e:
        ct.CTkLabel(content_frame, text=f"Failed to load data: {e}", text_color="red").pack()





def open_edit_window(table_name, columns, row_values):
    edit_win = ct.CTkToplevel()
    edit_win.title("Edit Row")
    edit_win.geometry("500x600")


    entries = {}
    row_id = row_values[0]  # Вважаємо, що перший стовпець — це первинний ключ

    for i, (col, val) in enumerate(zip(columns, row_values)):
        label = ct.CTkLabel(edit_win, text=col)
        label.pack(pady=5)
        entry = ct.CTkEntry(edit_win)
        entry.pack(pady=5)
        entry.insert(0, val)
        if i == 0:  # Перший стовпець (primary key) — не редагується
            entry.configure(state="disabled")
        entries[col] = entry

    def save_changes():
        update_pairs = []
        values = []

        for idx, col in enumerate(columns):
            if idx == 0:  # Пропускаємо перший стовпець (primary key)
                continue
            update_pairs.append(f"{col} = ?")
            values.append(entries[col].get())

        values.append(row_id)  # Значення для WHERE Id = ?

        try:
            # Використовуємо перший стовпець як ключ
            query = f"UPDATE {table_name} SET {', '.join(update_pairs)} WHERE {columns[0]} = ?"
            cursor.execute(query, values)
            connection.commit()
            edit_win.destroy()
            show_table_view(table_name)
        except pyodbc.Error as e:
            ct.CTkLabel(edit_win, text=f"Error: {e}", text_color="red").pack()

    save_button = ct.CTkButton(edit_win, text="Save Changes", command=save_changes)
    save_button.pack(pady=20)


def confirm_delete(table_name, key_column, key_value):
    confirm_win = ct.CTkToplevel()
    confirm_win.title("Confirm Deletion")
    confirm_win.geometry("400x200")

    label = ct.CTkLabel(confirm_win, text=f"Are you sure you want to delete row with {key_column} = {key_value}?", wraplength=350)
    label.pack(pady=20)

    def delete_row():
        try:
            query = f"DELETE FROM {table_name} WHERE {key_column} = ?"
            cursor.execute(query, (key_value,))
            connection.commit()
            confirm_win.destroy()
            show_table_view(table_name)
        except pyodbc.Error as e:
            ct.CTkLabel(confirm_win, text=f"Error: {e}", text_color="red").pack()

    confirm_button = ct.CTkButton(confirm_win, text="Yes, Delete", command=delete_row)
    confirm_button.pack(pady=10)

    cancel_button = ct.CTkButton(confirm_win, text="Cancel", command=confirm_win.destroy)
    cancel_button.pack(pady=5)

def open_add_window(table_name):
    add_win = ct.CTkToplevel()
    add_win.title("Add New Row")
    add_win.geometry("500x600")

    # Робимо вікно модальним
    add_win.transient(app)
    add_win.grab_set()
    add_win.focus()

    # Отримуємо назви стовпців
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [column[0] for column in cursor.description]

    entries = {}

    for i, col in enumerate(columns):
        if i == 0:  # Пропускаємо перший стовпець (primary key)
            continue
        label = ct.CTkLabel(add_win, text=col)
        label.pack(pady=5)
        entry = ct.CTkEntry(add_win)
        entry.pack(pady=5)
        entries[col] = entry

    def save_new_row():
        try:
            col_names = list(entries.keys())
            placeholders = ', '.join(['?'] * len(col_names))
            values = [entries[col].get() for col in col_names]

            query = f"INSERT INTO {table_name} ({', '.join(col_names)}) VALUES ({placeholders})"
            cursor.execute(query, values)
            connection.commit()
            add_win.destroy()
            show_table_view(table_name)
        except pyodbc.Error as e:
            ct.CTkLabel(add_win, text=f"Error: {e}", text_color="red").pack()

    save_button = ct.CTkButton(add_win, text="Save", command=save_new_row)
    save_button.pack(pady=20)

def show_about_window():
    for widget in content_frame.winfo_children():
        widget.destroy()

    back_button = ct.CTkButton(content_frame, text="← Back", command=show_main_menu)
    back_button.pack(anchor="w", pady=(10, 10))

    ct.CTkLabel(content_frame, text='Курсова робота з предмету "Бази даних" на тему "Доставка піци"',
                font=ct.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))

    description = (
        "Виробник піци (мережа пекарень і кафе) як роботодавець запрошує громадян на "
    "роботу по доставці піци замовникам. Будь-який громадянин може приєднатися до угоди з "
    "виробником і почати працювати кур’єром по доставці піци, для цього достатньо даних "
    "паспорта і ІПН. Виробник приймає замовлення на піцу на сайті або телефоном. Замовник "
    "повідомляє виробнику адресу. Як правило, замовлення має бути виконано протягом "
    "години. Мінімальна вартість замовлення 300грн. В разі самовивозу знижка 18%. Воно "
    "автоматично направляється в найближчу до замовника пекарню. "
    "Кур’єр забирає з пекарні кілька замовлень, а також бере роздрукований перелік "
    "взятих замовлень. Коли піца доставлена замовнику, останній розписується в переліку "
    "замовлень, а також оплачує замовлення (готівкою, по QR-коду або за реквізитами), якщо "
    "не зробив цього на сайті. Виробник нараховує кур’єру оплату замовлення (яка відповідає "
    "потенційній сумі знижки за самовивіз) після того, як побачить на сайті відмітку замовника "
    "щодо доставленої піци або зателефонує замовнику. "
    "Власників мережі цікавлять дані в динаміці по реалізації піци залежно від "
    "розташування замовників, а також обороти і прибутки окремих пекарень, і мережі в "
    "цілому.\n\n "
    )
    ct.CTkLabel(content_frame, text=description, wraplength=800, justify="left").pack(padx=20, pady=10)

    ct.CTkLabel(content_frame, text='Виконав студент групи ІС-34 Бакунець Владислав',
                font=ct.CTkFont(size=14, weight="bold")).pack(pady=(20, 10))

# Запуск
show_main_menu()
app.mainloop()
