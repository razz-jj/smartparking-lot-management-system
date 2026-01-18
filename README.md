def login_ui():
    st.subheader(" Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
if st.button("Login ✅"):
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state.logged_in = True
            st.success("Login Successful ✅")
            st.rerun()
        else:
            st.error("Invalid username or password ❌")


# -----------------------------
# MAIN APP
# -----------------------------
init_db()

st.set_page_config(page_title="Smart Parking Lot Web App", layout="wide")
st.title("🚗 Smart Parking Lot Management System (Web App)")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_ui()
    st.stop()

# Logout
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# Load slots
slots = load_slots_from_db()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["✅ Vehicle Entry", "🚪 Vehicle Exit", "📌 Slot Status", "📊 Dashboard & Report"])


# -----------------------------
# ENTRY TAB
# -----------------------------
with tab1:
    st.subheader("Vehicle Entry")

col1, col2, col3 = st.columns(3)
    with col1:
        vehicle_no = st.text_input("Vehicle Number", placeholder="Example: TS09AB1234")
    with col2:
        vehicle_type = st.selectbox("Vehicle Type", list(VEHICLE_PRICING.keys()))
    with col3:
        vip_entry = st.radio("VIP Entry?", ["No", "Yes"])

if st.button("Park Vehicle ✅"):
        vno = vehicle_no.strip().upper()

if not vno:
            st.error("Vehicle number required!")
        else:
            already = any(data and data["vehicle_no"] == vno for data in slots.values())
            if already:
                st.error("Vehicle already parked!")
            else:
                is_vip = (vip_entry == "Yes")
                slot_no = get_next_free_slot(slots, is_vip=is_vip)

if slot_no is None:
                    st.error("Parking Full!")
                else:
                    entry_time = datetime.datetime.now()
                    add_parked_vehicle(slot_no, vno, vehicle_type, entry_time, is_vip)
                    st.success(f"✅ Parked in Slot {slot_no}")
                    st.info(f"Entry Time: {entry_time}")
                    st.rerun()


# -----------------------------
# EXIT TAB
# -----------------------------
with tab2:
    st.subheader("Vehicle Exit")

exit_vehicle_no = st.text_input("Vehicle Number for Exit")

if st.button("Exit Vehicle 🚪"):
        vno_exit = exit_vehicle_no.strip().upper()
        found_slot = None

for slot_no, data in slots.items():
            if data and data["vehicle_no"] == vno_exit:
                found_slot = slot_no
                break

  if found_slot is None:
            st.error("Vehicle not found!")
        else:
            exit_time = datetime.datetime.now()
            entry_time = slots[found_slot]["entry_time"]
            vtype = slots[found_slot]["type"]
          bill, hours = calculate_bill(vtype, entry_time, exit_time)
            log_transaction(vno_exit, vtype, entry_time, exit_time, hours, bill)
            remove_parked_vehicle(found_slot)
            st.success("✅ Exit successful!")
            st.write(f"Slot Freed: {found_slot}")
            st.write(f"Duration: {hours} hour(s)")
            st.write(f"Bill Amount: ₹{bill}")
            st.rerun()


# -----------------------------
# SLOT STATUS TAB
# -----------------------------
with tab3:
    st.subheader("Slot Status")

available = []
    parked = []
    for slot_no, data in slots.items():
        if data is None:
            available.append(f"Slot {slot_no} {'(VIP)' if slot_no in VIP_SLOTS else ''}")
        else:
            parked.append({
                "Slot": slot_no,
                "Vehicle No": data["vehicle_no"],
                "Type": data["type"],
                "Mode": "VIP" if data["vip"] else "NORMAL",
                "Entry Time": data["entry_time"].strftime("%Y-%m-%d %H:%M:%S")
            })

colA, colB = st.columns(2)

with colA:
        st.markdown("### ✅ Available Slots")
        if available:
            st.write(available)
        else:
            st.warning("No slots available!")

with colB:
        st.markdown("### 🚗 Parked Vehicles")
        if parked:
            st.dataframe(pd.DataFrame(parked), use_container_width=True)
        else:
            st.info("No parked vehicles.")


# -----------------------------
# DASHBOARD + REPORT TAB
# -----------------------------
with tab4:
    st.subheader("Dashboard & Daily Report")

df = get_today_transactions()
    total_revenue = df["bill"].sum() if not df.empty else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transactions Today", len(df))
    col2.metric("Today's Revenue", f"₹{total_revenue}")
    col3.metric("Vehicles Parked (Live)", sum(1 for x in slots.values() if x is not None))
    st.markdown("---")

    # Charts
if not df.empty:
        st.markdown("### 📈 Revenue Chart (Per Transaction)")
        fig1 = plt.figure()
        plt.plot(df["bill"].tolist())
        plt.xlabel("Transaction Index")
        plt.ylabel("Bill Amount")
        st.pyplot(fig1)

 st.markdown("### 🚘 Vehicle Type Count")
        fig2 = plt.figure()
        df["vehicle_type"].value_counts().plot(kind="bar")
        plt.xlabel("Vehicle Type")
        plt.ylabel("Count")
        st.pyplot(fig2)

 st.markdown("### 🧾 Today's Transactions Table")
        st.dataframe(df[["vehicle_no", "vehicle_type", "duration_hours", "bill", "exit_time"]], use_container_width=True)

# PDF download
if st.button("⬇ Download Daily Report PDF"):
            pdf_file = generate_pdf_report(df, total_revenue)
            with open(pdf_file, "rb") as f:
                st.download_button(
                    label="📄 Click to Download PDF",
                    data=f,
                    file_name="daily_report.pdf",
                    mime="application/pdf"
                )
    else:
        st.info("No transactions today. Exit a vehicle to generate report.")
