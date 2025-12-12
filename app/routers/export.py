from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from io import BytesIO
import os
from pathlib import Path
import locale
import tempfile
import subprocess
import sys

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

from app.database import get_db
from app import crud, models
from app.services.calculation import calculate_shopping_list, get_camp_statistics

router = APIRouter()

# Helper function to get German weekday names
def get_german_weekday(date):
    """Get German weekday name for a date"""
    weekdays = {
        0: "Montag",
        1: "Dienstag",
        2: "Mittwoch",
        3: "Donnerstag",
        4: "Freitag",
        5: "Samstag",
        6: "Sonntag"
    }
    return weekdays.get(date.weekday(), date.strftime('%A'))

def open_pdf_file(filepath):
    """Open PDF file with default system viewer"""
    try:
        if sys.platform == 'win32':
            os.startfile(filepath)
        elif sys.platform == 'darwin':  # macOS
            subprocess.run(['open', filepath])
        else:  # linux
            subprocess.run(['xdg-open', filepath])
        return True
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return False

def get_downloads_folder():
    """Get or create downloads folder for PDFs"""
    # Get user's Downloads folder or create one in app directory
    if sys.platform == 'win32':
        downloads_path = Path.home() / 'Downloads' / 'Kuechenplaner'
    else:
        downloads_path = Path.home() / 'Downloads' / 'Kuechenplaner'

    # Create folder if it doesn't exist
    downloads_path.mkdir(parents=True, exist_ok=True)
    return downloads_path

@router.get("/shopping-list/pdf/{camp_id}")
async def export_shopping_list_pdf(
    camp_id: int,
    db: Session = Depends(get_db)
):
    """Export shopping list as PDF"""

    camp = crud.get_camp(db, camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    shopping_data = calculate_shopping_list(db, camp_id)

    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    # Container for PDF elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=30
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#374151'),
        spaceAfter=12
    )

    # Title
    title = Paragraph(f"Einkaufsliste: {camp.name}", title_style)
    elements.append(title)

    # Camp info
    info_text = f"Zeitraum: {camp.start_date.strftime('%d.%m.%Y')} - {camp.end_date.strftime('%d.%m.%Y')}<br/>"
    info_text += f"Teilnehmer: {camp.participant_count}<br/>"
    info_text += f"Rezepte: {shopping_data['total_recipes']}<br/>"
    info_text += f"Zutaten: {shopping_data['total_items']}"

    info = Paragraph(info_text, styles['Normal'])
    elements.append(info)
    elements.append(Spacer(1, 20))

    # Shopping list by category
    for category, items in shopping_data['categories'].items():
        # Category heading
        category_heading = Paragraph(category, heading_style)
        elements.append(category_heading)

        # Table data
        table_data = [["Zutat", "Menge", "Einheit"]]

        for item in items:
            table_data.append([
                item['ingredient'].name,
                f"{item['quantity']:.1f}",
                item['unit']
            ])

        # Create table
        table = Table(table_data, colWidths=[10*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))

    # Build PDF
    doc.build(elements)

    buffer.seek(0)
    filename = f"einkaufsliste_{camp.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"

    # Save PDF to downloads folder and open it
    downloads_folder = get_downloads_folder()
    filepath = downloads_folder / filename

    # Write PDF to file
    with open(filepath, 'wb') as f:
        f.write(buffer.getvalue())

    # Try to open the PDF automatically
    open_pdf_file(str(filepath))

    # Return file response
    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/shopping-list/excel/{camp_id}")
async def export_shopping_list_excel(
    camp_id: int,
    db: Session = Depends(get_db)
):
    """Export shopping list as Excel"""

    camp = crud.get_camp(db, camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    shopping_data = calculate_shopping_list(db, camp_id)

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Einkaufsliste"

    # Title
    ws['A1'] = f"Einkaufsliste: {camp.name}"
    ws['A1'].font = Font(size=16, bold=True)

    # Camp info
    ws['A3'] = f"Zeitraum:"
    ws['B3'] = f"{camp.start_date.strftime('%d.%m.%Y')} - {camp.end_date.strftime('%d.%m.%Y')}"
    ws['A4'] = f"Teilnehmer:"
    ws['B4'] = camp.participant_count
    ws['A5'] = f"Rezepte:"
    ws['B5'] = shopping_data['total_recipes']

    # Headers row
    row = 7
    ws[f'A{row}'] = "Kategorie"
    ws[f'B{row}'] = "Zutat"
    ws[f'C{row}'] = "Menge"
    ws[f'D{row}'] = "Einheit"
    ws[f'E{row}'] = "✓"  # Checkbox column

    # Style headers
    for col in ['A', 'B', 'C', 'D', 'E']:
        cell = ws[f'{col}{row}']
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="E5E7EB", end_color="E5E7EB", fill_type="solid")
        cell.alignment = Alignment(horizontal='left')

    row += 1

    # Data rows
    for category, items in shopping_data['categories'].items():
        for item in items:
            ws[f'A{row}'] = category
            ws[f'B{row}'] = item['ingredient'].name
            ws[f'C{row}'] = round(item['quantity'], 1)
            ws[f'D{row}'] = item['unit']
            ws[f'E{row}'] = ""  # Empty checkbox
            row += 1

    # Adjust column widths
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['E'].width = 5

    # Save to buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"einkaufsliste_{camp.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/meal-plan/pdf/{camp_id}")
async def export_meal_plan_pdf(
    camp_id: int,
    db: Session = Depends(get_db)
):
    """Export meal plan as PDF in landscape table format"""

    camp = crud.get_camp(db, camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    meal_plans = crud.get_meal_plans_for_camp(db, camp_id)

    # Organize by date and meal type
    from datetime import timedelta
    from collections import defaultdict

    meal_grid = defaultdict(lambda: {
        models.MealType.BREAKFAST: [],
        models.MealType.LUNCH: [],
        models.MealType.DINNER: []
    })

    for meal_plan in meal_plans:
        date_key = meal_plan.meal_date.date()
        meal_grid[date_key][meal_plan.meal_type].append(meal_plan)

    # Create PDF in landscape
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)

    elements = []
    styles = getSampleStyleSheet()

    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # Generate all days
    all_days = []
    current_date = camp.start_date
    while current_date <= camp.end_date:
        all_days.append(current_date)
        current_date += timedelta(days=1)

    # Split days into weeks (7 days per page)
    weeks = []
    for i in range(0, len(all_days), 7):
        weeks.append(all_days[i:i+7])

    # Create a table for each week
    for week_index, week_days in enumerate(weeks):
        if week_index > 0:
            elements.append(PageBreak())

        # Title with camp info
        title = Paragraph(f"Speiseplan: {camp.name}", title_style)
        elements.append(title)

        # Camp info
        info_text = f"Zeitraum: {camp.start_date.strftime('%d.%m.%Y')} - {camp.end_date.strftime('%d.%m.%Y')} | Teilnehmer: {camp.participant_count}"
        if len(weeks) > 1:
            info_text += f" | Woche {week_index + 1} von {len(weeks)}"

        info = Paragraph(info_text, styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 15))

        # Build table data
        table_data = []

        # Header row with dates
        header_row = [""]  # Empty cell for meal type column
        for day in week_days:
            weekday = get_german_weekday(day)
            date_str = day.strftime('%d.%m.')
            header_row.append(f"{weekday}\n{date_str}")

        table_data.append(header_row)

        # Meal rows
        meal_types = [
            (models.MealType.BREAKFAST, "Frühstück"),
            (models.MealType.LUNCH, "Mittagessen"),
            (models.MealType.DINNER, "Abendessen")
        ]

        for meal_type, meal_name in meal_types:
            row = [meal_name]

            for day in week_days:
                date_key = day.date()
                recipes = meal_grid[date_key][meal_type]

                if recipes:
                    names = []
                    for mp in recipes:
                        if mp.recipe:
                            names.append(mp.recipe.name)
                        else:
                            names.append("Kein Essen")
                    recipe_text = "\n".join(names) if names else "-"
                else:
                    recipe_text = "-"

                row.append(recipe_text)

            table_data.append(row)

        # Calculate column widths
        num_days = len(week_days)
        meal_col_width = 2.5*cm
        day_col_width = (landscape(A4)[0] - 3*cm - meal_col_width) / num_days
        col_widths = [meal_col_width] + [day_col_width] * num_days

        # Create table
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),

            # Meal type column styling
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F3F4F6')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('VALIGN', (0, 1), (0, -1), 'MIDDLE'),

            # Data cells styling
            ('FONTSIZE', (1, 1), (-1, -1), 8),
            ('ALIGN', (1, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (1, 1), (-1, -1), 'TOP'),
            ('LEFTPADDING', (1, 1), (-1, -1), 5),
            ('RIGHTPADDING', (1, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),

            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#4F46E5')),

            # Alternating row colors for data
            ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ]))

        elements.append(table)

    # Build PDF
    doc.build(elements)

    buffer.seek(0)
    filename = f"speiseplan_{camp.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"

    # Save PDF to downloads folder and open it
    downloads_folder = get_downloads_folder()
    filepath = downloads_folder / filename

    # Write PDF to file
    with open(filepath, 'wb') as f:
        f.write(buffer.getvalue())

    # Try to open the PDF automatically
    open_pdf_file(str(filepath))

    # Return file response
    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/recipe-book/pdf/{camp_id}")
async def export_recipe_book_pdf(
    camp_id: int,
    db: Session = Depends(get_db)
):
    """Export recipe book with all recipes from meal plan"""

    camp = crud.get_camp(db, camp_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    meal_plans = crud.get_meal_plans_for_camp(db, camp_id)

    # Get unique recipes (filter out None recipe_ids)
    recipe_ids = set(mp.recipe_id for mp in meal_plans if mp.recipe_id is not None)
    recipes = [crud.get_recipe(db, rid) for rid in recipe_ids if rid is not None]
    # Filter out None recipes (in case a recipe was deleted)
    recipes = [r for r in recipes if r is not None]

    if not recipes:
        raise HTTPException(status_code=404, detail="No recipes found in meal plan")

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    elements = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=30
    )

    title = Paragraph(f"Rezeptbuch: {camp.name}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 20))

    # Each recipe
    for i, recipe in enumerate(recipes):
        if i > 0:
            elements.append(PageBreak())

        # Calculate scaling factor for this camp
        scaling_factor = camp.participant_count / recipe.base_servings

        # Recipe name
        recipe_title = Paragraph(recipe.name, styles['Heading1'])
        elements.append(recipe_title)

        # Description
        if recipe.description:
            desc = Paragraph(recipe.description, styles['Normal'])
            elements.append(desc)
            elements.append(Spacer(1, 10))

        # Basic info with scaled portions
        info_text = f"Portionen: {camp.participant_count} (Originalrezept: {recipe.base_servings}) | "
        if recipe.preparation_time:
            info_text += f"Vorbereitung: {recipe.preparation_time} min | "
        if recipe.cooking_time:
            info_text += f"Kochzeit: {recipe.cooking_time} min"

        info = Paragraph(f"<i>{info_text}</i>", styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 15))

        # Allergens
        if recipe.allergens:
            allergen_names = ", ".join([a.name for a in recipe.allergens])
            allergen_text = Paragraph(f"<b>Allergene:</b> {allergen_names}", styles['Normal'])
            elements.append(allergen_text)
            elements.append(Spacer(1, 10))

        # Ingredients with scaled quantities
        elements.append(Paragraph("<b>Zutaten:</b>", styles['Heading3']))

        ingredient_data = [["Zutat", "Menge", "Einheit"]]
        for ri in recipe.ingredients:
            scaled_quantity = ri.quantity * scaling_factor
            ingredient_data.append([
                ri.ingredient.name,
                f"{scaled_quantity:.1f}",
                ri.unit
            ])

        ing_table = Table(ingredient_data, colWidths=[10*cm, 3*cm, 3*cm])
        ing_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(ing_table)
        elements.append(Spacer(1, 15))

        # Instructions
        if recipe.instructions:
            elements.append(Paragraph("<b>Zubereitung:</b>", styles['Heading3']))
            instructions = Paragraph(recipe.instructions, styles['Normal'])
            elements.append(instructions)

    # Build PDF
    doc.build(elements)

    buffer.seek(0)
    filename = f"rezeptbuch_{camp.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"

    # Save PDF to downloads folder and open it
    downloads_folder = get_downloads_folder()
    filepath = downloads_folder / filename

    # Write PDF to file
    with open(filepath, 'wb') as f:
        f.write(buffer.getvalue())

    # Try to open the PDF automatically
    open_pdf_file(str(filepath))

    # Return file response
    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/recipes/pdf")
async def export_all_recipes_pdf(
    db: Session = Depends(get_db)
):
    """Export all recipes as PDF with improved formatting"""

    # Get all recipes
    recipes = crud.get_recipes(db, skip=0, limit=10000)

    if not recipes:
        raise HTTPException(status_code=404, detail="No recipes found")

    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#6B7280'),
        spaceAfter=20,
        alignment=TA_CENTER
    )

    recipe_title_style = ParagraphStyle(
        'RecipeTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=15,
        fontName='Helvetica-Bold'
    )

    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#374151'),
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )

    # Title page
    title = Paragraph("Rezeptsammlung", title_style)
    elements.append(title)

    subtitle = Paragraph(f"{len(recipes)} Rezepte | {datetime.now().strftime('%d.%m.%Y')}", subtitle_style)
    elements.append(subtitle)
    elements.append(Spacer(1, 30))

    # Table of contents
    toc_heading = Paragraph("<b>Inhaltsverzeichnis</b>", styles['Heading2'])
    elements.append(toc_heading)
    elements.append(Spacer(1, 10))

    toc_data = [["Nr.", "Rezeptname", "Portionen"]]
    for idx, recipe in enumerate(recipes, 1):
        toc_data.append([
            str(idx),
            recipe.name,
            str(recipe.base_servings)
        ])

    toc_table = Table(toc_data, colWidths=[1.5*cm, 11*cm, 3*cm])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
    ]))

    elements.append(toc_table)
    elements.append(PageBreak())

    # Each recipe on its own page
    for idx, recipe in enumerate(recipes, 1):
        # Recipe number and name
        recipe_header = Paragraph(f"{idx}. {recipe.name}", recipe_title_style)
        elements.append(recipe_header)

        # Description
        if recipe.description:
            desc = Paragraph(f"<i>{recipe.description}</i>", styles['Normal'])
            elements.append(desc)
            elements.append(Spacer(1, 10))

        # Recipe info in a colored box
        info_parts = [f"<b>Portionen:</b> {recipe.base_servings}"]
        if recipe.preparation_time:
            info_parts.append(f"<b>Vorbereitung:</b> {recipe.preparation_time} min")
        if recipe.cooking_time:
            info_parts.append(f"<b>Kochzeit:</b> {recipe.cooking_time} min")

        info_data = [info_parts]

        info_table = Table(info_data, colWidths=[5*cm] * len(info_parts))
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EEF2FF')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1F2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 15))

        # Tags and allergens
        if recipe.tags or recipe.allergens:
            tag_allergen_text = []
            if recipe.tags:
                tags_str = ", ".join([tag.name for tag in recipe.tags])
                tag_allergen_text.append(f"<b>Tags:</b> {tags_str}")
            if recipe.allergens:
                allergens_str = ", ".join([a.name for a in recipe.allergens])
                tag_allergen_text.append(f"<b>Allergene:</b> {allergens_str}")

            tag_allergen_para = Paragraph(" | ".join(tag_allergen_text), styles['Normal'])
            elements.append(tag_allergen_para)
            elements.append(Spacer(1, 15))

        # Ingredients section
        elements.append(Paragraph("Zutaten", section_heading_style))

        if recipe.ingredients:
            ingredient_data = [["Zutat", "Menge", "Einheit"]]
            for ri in recipe.ingredients:
                ingredient_data.append([
                    ri.ingredient.name,
                    f"{ri.quantity:.1f}",
                    ri.unit
                ])

            ing_table = Table(ingredient_data, colWidths=[10*cm, 3*cm, 3*cm])
            ing_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (2, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
            ]))

            elements.append(ing_table)
            elements.append(Spacer(1, 15))

        # Instructions section
        if recipe.instructions:
            elements.append(Paragraph("Zubereitung", section_heading_style))

            # Split instructions by newlines and create formatted text
            instructions_text = recipe.instructions.replace('\n', '<br/>')
            instructions = Paragraph(instructions_text, styles['Normal'])
            elements.append(instructions)

        # Add page break except for the last recipe
        if idx < len(recipes):
            elements.append(PageBreak())

    # Build PDF
    doc.build(elements)

    buffer.seek(0)
    filename = f"rezeptsammlung_{datetime.now().strftime('%Y%m%d')}.pdf"

    # Save PDF to downloads folder and open it
    downloads_folder = get_downloads_folder()
    filepath = downloads_folder / filename

    # Write PDF to file
    with open(filepath, 'wb') as f:
        f.write(buffer.getvalue())

    # Try to open the PDF automatically
    open_pdf_file(str(filepath))

    # Return file response
    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
