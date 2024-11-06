import tkinter as tk
from tkinter import Toplevel, messagebox, ttk, simpledialog
from tkcalendar import Calendar
from datetime import datetime
import pymysql
from sshtunnel import SSHTunnelForwarder
import csv

class CargoPopupApp:
    def __init__(self, master):
        self.root = master
        self.row_count = 1  # Initialize sequence counter for S.No.
        self.root.title("Cargo Management System")
        self.root.geometry('900x600')

        # Set ttk style theme
        style = ttk.Style()
        style.theme_use("clam")  # Use a theme suitable for customization

        # Customize the style for buttons
        style.configure("TButton",
                        padding=(10, 5),
                        relief="raised",
                        borderwidth=2,
                        background="#4B4B4B",  # Dark gray background
                        foreground="white",  # White text
                        font=('Helvetica', 12, 'bold'))
        style.map("TButton",
                  background=[('active', '#6B6B6B'), ('pressed', '#8B8B8B')],
                  foreground=[('active', 'black'), ('pressed', 'white')])

        # SSH and DB credentials
        self.ssh_host = '173.236.222.167'
        self.ssh_user = 'menahel'
        self.ssh_pw = 'Ks%TWR1&?t'
        self.sql_host = 'sql17175.sql17175.dreamhostps.com'
        self.sql_user = 'dealtascom'
        self.sql_pw = 'hbhceuyr'
        self.sql_db = 'comingsoon'

        self.saved_data = {}
        self.current_cargo_id = None
        self.row_count = 1
        self.box_number = ""
        self.lithium_ion_status = "NO"
        self.loose_box_status = "NO"

        # Top frame for Create Cargo ID button
        self.top_frame = tk.Frame(self.root, bd=2, relief=tk.RAISED, bg="#E0E0E0")  # Light gray
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.create_button = ttk.Button(self.top_frame, text="Create Cargo ID", command=self.create_cargo_id)
        self.create_button.pack(pady=10, padx=5)

        # Center frame for live updates
        self.center_frame = tk.Frame(self.root, bg="#D0D0D0")  # Slightly darker gray
        self.center_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.live_updates_label = tk.Label(self.center_frame, text="Live Updates", font=('Helvetica', 16, 'bold'), bg="#D0D0D0")
        self.live_updates_label.pack(pady=20)

        # Treeview for displaying cargo data
        self.cargo_table = ttk.Treeview(self.center_frame, columns=("S.No.", "Cargo_ID", "TimeStamp", "Box_Number", "Tracking_ID", "Lithium_Ion", "Loose_Box"), show='headings')
        self.cargo_table.pack(fill=tk.BOTH, expand=True)

        columns = [
            ("S.No.", 50),
            ("Cargo_ID", 100),
            ("TimeStamp", 150),
            ("Box_Number", 100),
            ("Tracking_ID", 250),
            ("Lithium_Ion", 100),
            ("Loose_Box", 100),
        ]

        for col, width in columns:
            self.cargo_table.heading(col, text=col)
            self.cargo_table.column(col, width=width, anchor="center", stretch=True)  # Center align and allow stretching
        
        # Customize Treeview appearance
        self.cargo_table.tag_configure('oddrow', background="#FFFFFF")  # White for odd rows
        self.cargo_table.tag_configure('evenrow', background="#F0F0F0")  # Light gray for even rows

        # Bottom frame for buttons
        self.bottom_frame = tk.Frame(self.root, bd=2, relief=tk.RAISED, bg="#E0E0E0")
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.box_number_entry = tk.Entry(self.bottom_frame, font=('Helvetica', 14), bg="#FFFFFF", fg="black")
        self.box_number_entry.pack(pady=10)

        # Create buttons with the defined style
        self.open_button = ttk.Button(self.bottom_frame, text="Open", command=self.open_cargo_list)
        self.open_button.pack(side=tk.LEFT, padx=5)

        self.ship_button = ttk.Button(self.bottom_frame, text="Ship", command=self.ship_cargo_id)
        self.ship_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(self.bottom_frame, text="Save", command=self.save_data)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(self.bottom_frame, text="Clear Selected Row", command=self.clear_row)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.close_button = ttk.Button(self.bottom_frame, text="Close Cargo ID", command=self.close_cargo_id)
        self.close_button.pack(side=tk.LEFT, padx=5)

        self.summary_button = ttk.Button(self.bottom_frame, text="Summary", command=self.show_summary)
        self.summary_button.pack(side=tk.LEFT, padx=5)

        # Entry for scanning
        self.scan_label = tk.Label(self.bottom_frame, text="Scan Box Number or loose / If liion / Tracking Number:", font=('Helvetica', 14), bg="#E0E0E0")
        self.scan_label.pack(pady=10)

        self.scan_entry = tk.Entry(self.bottom_frame, font=('Helvetica', 14), bg="#FFFFFF", fg="black")
        self.scan_entry.pack(pady=10)
        self.scan_entry.bind('<Return>', self.handle_scan)

        # Bind double-click event for editing
        self.cargo_table.bind("<Double-1>", self.edit_cell)

    def get_last_sequence_number():
        query = "SELECT MAX(`S.No.`) FROM Dealtas_Track"
        cursor.execute(query)
        result = cursor.fetchone()
        if result and result[0] is not None:
            return result[0]
        return 0  # If no records, start from 0
    
    def edit_cell(self, event):
        selected_item = self.cargo_table.selection()[0]
        col = self.cargo_table.identify_column(event.x)[1:]  # Get column number as string
        col = int(col) - 1  # Make zero-indexed

        current_value = self.cargo_table.item(selected_item, 'values')[col]
        new_value = simpledialog.askstring("Edit Value", f"Enter new value for this cell:", initialvalue=current_value)

        if new_value:
            values = list(self.cargo_table.item(selected_item, 'values'))
            values[col] = new_value
            self.cargo_table.item(selected_item, values=values)

    def create_cargo_id(self):
        
        self.clear_all_frames()  # Clear all frames before creating a new Cargo ID
        self.top = tk.Toplevel(self.root)
        self.top.title("Select Cargo Date")
        self.cal = Calendar(self.top, selectmode="day", year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
        self.cal.pack(pady=20)
        select_btn = tk.Button(self.top, text="Select", command=self.select_date)
        select_btn.pack(pady=10)

    def clear_all_frames(self):
        # Clear the cargo table and reset the form fields
        self.cargo_table.delete(*self.cargo_table.get_children())
        self.saved_data.clear()
        self.current_cargo_id = None
        self.row_count = 1
        self.box_number = ""
        self.lithium_ion_status = "NO"
        self.loose_box_status = "NO"
        self.live_updates_label.config(text="")  # Clear the live updates label
        self.scan_entry.delete(0, tk.END)  # Clear scan entry

    def select_date(self):
        date = self.cal.get_date()
        self.current_cargo_id = datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d')
        self.row_count = 1
        self.live_updates_label.config(text=f"Created Cargo ID: {self.current_cargo_id}")
        self.scan_entry.focus()  # Set focus to the scan entry after creating cargo ID
        self.top.destroy()
        box_number = self.box_number_entry.get()
                
    def open_cargo_list(self):
        # Get only open cargo IDs from Cargo_Status
        connection = self.get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT Cargo_ID FROM Cargo_Status WHERE Status = 'open'")
            open_cargo_ids = cursor.fetchall()
        
            if open_cargo_ids:
                open_cargo_ids = [cargo_id[0] for cargo_id in open_cargo_ids]  # Unpack tuple
            
                # Open cargo list in a new window
                self.open_window = tk.Toplevel(self.root)
                self.open_window.title("Open Cargo ID")
            
                listbox_label = tk.Label(self.open_window, text="Select Cargo ID from the list:", font=('Helvetica', 14))
                listbox_label.pack(pady=10)
            
                # Create a Listbox to show available open cargo IDs
                self.cargo_listbox = tk.Listbox(self.open_window, font=('Helvetica', 14), height=10)
                self.cargo_listbox.pack(pady=20)

                # Add cargo IDs to the listbox
                for cargo_id in open_cargo_ids:
                    self.cargo_listbox.insert(tk.END, cargo_id)

                # Bind double-click event to load selected cargo ID
                self.cargo_listbox.bind("<Double-1>", self.load_selected_cargo)
            else:
                messagebox.showinfo("Open Cargo", "No saved cargo to load.")
                
    def load_selected_cargo(self, event):
        selected_cargo_id = self.cargo_listbox.get(self.cargo_listbox.curselection())

        if selected_cargo_id:
            # Clear the current table before loading new data
            self.cargo_table.delete(*self.cargo_table.get_children())

            # Fetch data from Dealtas_Track for the selected Cargo ID
            connection = self.get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Dealtas_Track WHERE Cargo_ID = %s", (selected_cargo_id,))
                cargo_data = cursor.fetchall()
            
                # Populate the cargo table with fetched data, avoiding duplicates
                for row in cargo_data:
                    existing_ids = [self.cargo_table.item(item)['values'][4] for item in self.cargo_table.get_children()]
                    if row[3] not in existing_ids:  # Assuming Tracking_ID is in the 4th position (index 3)
                        self.cargo_table.insert("", "end", values=row)

            self.current_cargo_id = selected_cargo_id
            self.live_updates_label.config(text=f"Opened Cargo ID: {self.current_cargo_id}")
            self.open_window.destroy()
        else:
            messagebox.showerror("Error", "Please select a valid Cargo ID.")

    def handle_scan(self, event):
        scanned_code = self.scan_entry.get().strip()

        if not scanned_code:
            return

        if scanned_code.isdigit() and 1 <= int(scanned_code) <= 999:
            self.box_number = scanned_code
        elif scanned_code == "liion":
            self.lithium_ion_status = "YES"
        elif scanned_code == "loose":
            self.loose_box_status = "YES"
            self.box_number = "NA"
        else:
            self.add_tracking_id_to_cargo(scanned_code)

        self.scan_entry.delete(0, tk.END)

    def add_tracking_id_to_cargo(self, tracking_id):
        if self.current_cargo_id:
            self.cargo_table.insert("", "end", values=(self.row_count, self.current_cargo_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.box_number, tracking_id, self.lithium_ion_status, self.loose_box_status))
            self.row_count += 1

            if self.current_cargo_id not in self.saved_data:
                self.saved_data[self.current_cargo_id] = []
            self.saved_data[self.current_cargo_id].append((self.row_count, self.current_cargo_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.box_number, tracking_id, self.lithium_ion_status, self.loose_box_status))

            self.lithium_ion_status = "NO"
            self.loose_box_status = "NO"
        else:
            messagebox.showerror("Error", "Please create or open a Cargo ID first.")
    
    def save_data(self):
        if self.current_cargo_id:
            connection = self.get_db_connection()
            with connection.cursor() as cursor:
                for row in self.saved_data.get(self.current_cargo_id, []):
                    # Check if the record already exists to prevent duplicates
                    cursor.execute("SELECT * FROM Dealtas_Track WHERE Cargo_ID = %s AND Tracking_ID = %s", (row[1], row[4]))
                    existing_record = cursor.fetchone()
                
                    if not existing_record:  # Only insert if the record does not exist
                        cursor.execute("INSERT INTO Dealtas_Track (Cargo_ID, TimeStamp, Box_Number, Tracking_ID, Lithium_Ion, Loose_Box) VALUES (%s, %s, %s, %s, %s, %s)", row[1:])
        
                # Ensure Cargo_Status is updated to 'open' if it doesn't already exist
                cursor.execute("SELECT * FROM Cargo_Status WHERE Cargo_ID = %s", (self.current_cargo_id,))
                existing_status = cursor.fetchone()
                if not existing_status:  # Only insert if the status does not exist
                    cursor.execute("INSERT INTO Cargo_Status (Cargo_ID, Status) VALUES (%s, %s)", (self.current_cargo_id, 'open'))

            connection.commit()
            messagebox.showinfo("Save Data", "Data has been saved successfully!")
        else:
            messagebox.showerror("Error", "No Cargo ID to save.")
    
    def ship_cargo_id(self):
        if self.current_cargo_id:
            self.save_data()  # Ensure data is saved before shipping
            connection = self.get_db_connection()
            with connection.cursor() as cursor:
                # Update Cargo_Status to 'closed'
                cursor.execute("UPDATE Cargo_Status SET Status = 'closed' WHERE Cargo_ID = %s", (self.current_cargo_id,))
            
                connection.commit()
                messagebox.showinfo("Ship Cargo", f"Cargo ID {self.current_cargo_id} has been shipped and marked as closed.")
            
                # Clear the cargo table for the next operation
                self.cargo_table.delete(*self.cargo_table.get_children())
                self.current_cargo_id = None  # Reset current cargo ID
                self.live_updates_label.config(text="")  # Clear the live updates label
                # Refresh the open cargo list to remove shipped Cargo ID
        else:
            messagebox.showerror("Error", "No Cargo ID to ship.")

    def close_cargo_id(self):
        if self.current_cargo_id:
            self.save_data()  # Ensure data is saved to Dealtas_Track

            connection = self.get_db_connection()
            with connection.cursor() as cursor:
                # Update Cargo_Status to 'open'
                cursor.execute("UPDATE Cargo_Status SET Status = 'open' WHERE Cargo_ID = %s", (self.current_cargo_id,))
                connection.commit()

                messagebox.showinfo("Close Cargo", f"Cargo ID {self.current_cargo_id} has been set to open.")

            # Clear the cargo table and reset current_cargo_id
            self.cargo_table.delete(*self.cargo_table.get_children())
            self.current_cargo_id = None
            self.row_count = 1  # Reset row count
            self.box_number = ""
            self.lithium_ion_status = "NO"
            self.loose_box_status = "NO"
            self.live_updates_label.config(text="")  # Clear the live updates label
        else:
            messagebox.showerror("Error", "No Cargo ID to close.")

    def get_db_connection(self):
        # Setting up SSH tunnel
        server = SSHTunnelForwarder(
            (self.ssh_host, 22),
            ssh_username=self.ssh_user,
            ssh_password=self.ssh_pw,
            remote_bind_address=(self.sql_host, 3306)
        )
        server.start()
        
        # Connect to the database
        connection = pymysql.connect(
            host='127.0.0.1',
            port=server.local_bind_port,
            user=self.sql_user,
            password=self.sql_pw,
            db=self.sql_db,
        )
        return connection

    def clear_row(self):
        selected_item = self.cargo_table.selection()
        if selected_item:
            self.cargo_table.delete(selected_item)
        else:
            messagebox.showerror("Error", "No row selected.")

    def show_summary(self):
        if self.current_cargo_id:
            total_lithium_boxes = sum([1 for row in self.saved_data[self.current_cargo_id] if row[5] == "YES"])
            unique_boxes = len(set(row[3] for row in self.saved_data[self.current_cargo_id]))
            tracking_numbers = [row[4] for row in self.saved_data[self.current_cargo_id]]
            ff_tracking_ids = len([t for t in tracking_numbers if t.startswith("FF45CR")])
            total_packages = len(self.saved_data[self.current_cargo_id])

            # Create a new top-level window for the summary
            summary_window = Toplevel(self.master)
            summary_window.title("Cargo Summary")

            # Create a Treeview widget
            tree = ttk.Treeview(summary_window, columns=("Description", "Count"), show="headings")
            tree.heading("Description", text="Description")
            tree.heading("Count", text="Count")

            # Set column widths
            tree.column("Description", width=250)
            tree.column("Count", width=100)

            # Insert data into the Treeview
            summary_data = [
                ("Total Lithium-Ion Boxes", total_lithium_boxes),
                ("Handeling Units", unique_boxes),
                ("IDGU Packages", ff_tracking_ids),
                ("Total Packages", total_packages)
            ]

            for item in summary_data:
                tree.insert("", "end", values=item)

            # Add a scrollbar
            scrollbar = ttk.Scrollbar(summary_window, orient="vertical", command=tree.yview)
            tree.configure(yscroll=scrollbar.set)
            scrollbar.pack(side="right", fill="y")

            tree.pack(side="left", fill="both", expand=True)

            # Center the window on the parent window
            summary_window.transient(self.master)  # Keep the window on top of the parent
            summary_window.grab_set()  # Disable interaction with other windows until this one is closed
            summary_window.geometry("400x200")  # Set a size for the summary window
        else:
            messagebox.showerror("Error", "No Cargo ID selected.")

   
# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = CargoPopupApp(root)
    root.mainloop()