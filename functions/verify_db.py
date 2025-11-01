import os
import sqlite3
import pandas as pd

try:
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
except ImportError as e:
    raise RuntimeError(
        "Missing dependency 'reportlab'. Fix by activating your venv and installing it:\n"
        "  source .venv/bin/activate\n"
        "  pip install reportlab\n"
    ) from e

# ---------- Paths ----------
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.db")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PDF = os.path.join(OUTPUT_DIR, "warning.pdf")


# ---------- Fetch discrepancies ----------
def fetch_discrepancies(db_path: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    query = """
    SELECT
        c.CourseName AS CourseName,
        c.CourseCode AS CourseCode,
        c.CoordinatorName AS CoordinatorName,
        COALESCE(c.ReviewStd, 0) AS ReviewStd,
        COALESCE(cd.No_Student, 0) AS No_Student
    FROM Courses c
    JOIN CourseDept cd
      ON c.CourseCode = cd.CourseCode
     AND c.CourseType = cd.CourseType
     AND c.CoordinatorName = cd.CoordinatorName
    -- semester comparison removed intentionally
    ORDER BY c.CourseCode;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return df

    # Group by CourseName, CourseCode, CoordinatorName and sum No_Student
    grouped = (
        df.groupby(["CourseName", "CourseCode", "CoordinatorName"], as_index=False)
        .agg({"ReviewStd": "max", "No_Student": "sum"})
    )

    # Keep only mismatches
    discrepancies = grouped[grouped["ReviewStd"] != grouped["No_Student"]].reset_index(drop=True)
    return discrepancies


# ---------- Build landscape PDF ----------
def build_pdf(df: pd.DataFrame, out_pdf: str):
    # Use landscape A4
    doc = SimpleDocTemplate(
        out_pdf,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Heading1"], alignment=1, fontSize=14)
    normal_center = ParagraphStyle("center", parent=styles["Normal"], alignment=1)

    elements = []
    elements.append(Paragraph("ReviewStd vs Actual Enrolled Students — Discrepancy Report", title_style))
    elements.append(Spacer(1, 10))

    # If no discrepancies
    if df.empty:
        elements.append(Paragraph("No discrepancies found. ReviewStd matches actual enrolled counts.", normal_center))
        doc.build(elements)
        return

    # Table header + rows
    data = [["Course Name", "Course Code", "Coordinator", "ReviewStd", "Total (No_Student)"]]
    for _, row in df.iterrows():
        data.append([
            row["CourseName"] or "",
            row["CourseCode"] or "",
            row["CoordinatorName"] or "",
            int(row["ReviewStd"]),
            int(row["No_Student"])
        ])

    # Build table for landscape layout
    table = Table(data, repeatRows=1, hAlign="LEFT", colWidths=[250, 100, 200, 80, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d3d3d3")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (3, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(table)
    doc.build(elements)


# ---------- Main ----------
def main():
    df = fetch_discrepancies(DB_PATH)
    build_pdf(df, OUTPUT_PDF)
    print(f"Landscape warning PDF generated: {OUTPUT_PDF} (rows: {len(df)})")


if __name__ == "__main__":
    main()
