def generate_pdf_report(df, total_revenue):
    filename = "daily_report.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 50, "Daily Parking Report")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 90, f"Date: {datetime.date.today()}")
    c.drawString(50, height - 110, f"Total Transactions: {len(df)}")
    c.drawString(50, height - 130, f"Total Revenue: ₹{total_revenue}")

    y = height - 170
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Vehicle No")
    c.drawString(150, y, "Type")
    c.drawString(250, y, "Hours")
    c.drawString(320, y, "Bill")

    c.setFont("Helvetica", 10)
    y -= 20

    for _, row in df.iterrows():
        if y < 50:
            c.showPage()
            y = height - 50

        c.drawString(50, y, str(row["vehicle_no"]))
        c.drawString(150, y, str(row["vehicle_type"]))
        c.drawString(250, y, str(row["duration_hours"]))
        c.drawString(320, y, f"₹{row['bill']}")
        y -= 18

    c.save()
    return filename
