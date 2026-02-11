from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from io import BytesIO
import os
from pathlib import Path
import re
import subprocess
import sys
from collections import defaultdict

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

from app.database import get_db
from app import crud, models
from app.services.calculation import calculate_shopping_list
from app.logging_config import get_logger

logger = get_logger("export")

router = APIRouter()


# --- Helper functions ---

def sanitize_filename(name: str) -> str:
    """Sanitize a string for safe use as a filename"""
    return re.sub(r'[^\w\-.]', '_', name)


def get_german_weekday(date):
    """Get German weekday name for a date"""
    weekdays = {
        0: "Montag", 1: "Dienstag", 2: "Mittwoch", 3: "Donnerstag",
        4: "Freitag", 5: "Samstag", 6: "Sonntag"
    }
    return weekdays.get(date.weekday(), date.strftime('%A'))


def get_downloads_folder():
    """Get or create downloads folder for exported files"""
    downloads_path = Path.home() / 'Downloads' / 'Kuechenplaner'
    downloads_path.mkdir(parents=True, exist_ok=True)
    return downloads_path


def open_file(filepath):
    """Open file with default system viewer"""
    try:
        if sys.platform == 'win32':
            os.startfile(filepath)
        elif sys.platform == 'darwin':
            subprocess.run(['open', filepath])
        else:
            subprocess.run(['xdg-open', filepath])
        return True
    except Exception as e:
        logger.error(f"Error opening file: {e}", exc_info=True)
        return False


def build_and_serve_pdf(buffer: BytesIO, filename: str) -> FileResponse:
    """Save PDF to downloads folder, open it, and return FileResponse"""
    buffer.seek(0)
    downloads_folder = get_downloads_folder()
    filepath = downloads_folder / filename

    with open(filepath, 'wb') as f:
        f.write(buffer.getvalue())

    open_file(str(filepath))

    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def get_pdf_styles():
    """Get common PDF styles used across all exports"""
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ExportTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=30
    )

    heading_style = ParagraphStyle(
        'ExportHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#374151'),
        spaceAfter=12
    )

    section_heading_style = ParagraphStyle(
        'ExportSectionHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#374151'),
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )

    return styles, title_style, heading_style, section_heading_style


def get_table_style():
    """Get common table style for ingredient/data tables"""
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])


def make_timestamp():
    """Generate a timestamp string for filenames"""
    return datetime.now(timezone.utc).strftime('%Y%m%d')


# --- Export endpoints ---

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

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    elements = []
    styles, title_style, heading_style, _ = get_pdf_styles()

    # Title
    elements.append(Paragraph(f"Einkaufsliste: {camp.name}", title_style))

    # Camp info
    info_text = (
        f"Zeitraum: {camp.start_date.strftime('%d.%m.%Y')} - {camp.end_date.strftime('%d.%m.%Y')}<br/>"
        f"Teilnehmer: {camp.participant_count}<br/>"
        f"Rezepte: {shopping_data['total_recipes']}<br/>"
        f"Zutaten: {shopping_data['total_items']}"
    )
    elements.append(Paragraph(info_text, styles['Normal']))
    elements.append(Spacer(1, 20))

    # Shopping list by category
    for category, items in shopping_data['categories'].items():
        elements.append(Paragraph(category, heading_style))

        table_data = [["Zutat", "Menge", "Einheit"]]
        for item in items:
            table_data.append([
                item['ingredient'].name,
                f"{item['quantity']:.1f}",
                item['unit']
            ])

        table = Table(table_data, colWidths=[10*cm, 3*cm, 3*cm])
        table.setStyle(get_table_style())
        elements.append(table)
        elements.append(Spacer(1, 20))

    doc.build(elements)

    filename = f"einkaufsliste_{sanitize_filename(camp.name)}_{make_timestamp()}.pdf"
    return build_and_serve_pdf(buffer, filename)


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

    wb = Workbook()
    ws = wb.active
    ws.title = "Einkaufsliste"

    ws['A1'] = f"Einkaufsliste: {camp.name}"
    ws['A1'].font = Font(size=16, bold=True)

    ws['A3'] = "Zeitraum:"
    ws['B3'] = f"{camp.start_date.strftime('%d.%m.%Y')} - {camp.end_date.strftime('%d.%m.%Y')}"
    ws['A4'] = "Teilnehmer:"
    ws['B4'] = camp.participant_count
    ws['A5'] = "Rezepte:"
    ws['B5'] = shopping_data['total_recipes']

    row = 7
    for col_letter, header in [('A', 'Kategorie'), ('B', 'Zutat'), ('C', 'Menge'), ('D', 'Einheit'), ('E', '?')]:
        cell = ws[f'{col_letter}{row}']
        cell.value = header
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="E5E7EB", end_color="E5E7EB", fill_type="solid")
        cell.alignment = Alignment(horizontal='left')

    row += 1

    for category, items in shopping_data['categories'].items():
        for item in items:
            ws[f'A{row}'] = category
            ws[f'B{row}'] = item['ingredient'].name
            ws[f'C{row}'] = round(item['quantity'], 1)
            ws[f'D{row}'] = item['unit']
            ws[f'E{row}'] = ""
            row += 1

    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['E'].width = 5

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"einkaufsliste_{sanitize_filename(camp.name)}_{make_timestamp()}.xlsx"

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

    meal_grid = defaultdict(lambda: {
        models.MealType.BREAKFAST: [],
        models.MealType.LUNCH: [],
        models.MealType.DINNER: []
    })

    for meal_plan in meal_plans:
        date_key = meal_plan.meal_date.date()
        meal_grid[date_key][meal_plan.meal_type].append(meal_plan)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'MealPlanTitle',
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

    # Split days into pages (10 days per page)
    pages = [all_days[i:i+10] for i in range(0, len(all_days), 10)]

    meal_types = [
        (models.MealType.BREAKFAST, "Frühstück"),
        (models.MealType.LUNCH, "Mittagessen"),
        (models.MealType.DINNER, "Abendessen")
    ]

    for page_idx, page_days in enumerate(pages):
        if page_idx > 0:
            elements.append(PageBreak())

        elements.append(Paragraph(f"Speiseplan: {camp.name}", title_style))

        info_text = f"Zeitraum: {camp.start_date.strftime('%d.%m.%Y')} - {camp.end_date.strftime('%d.%m.%Y')} | Teilnehmer: {camp.participant_count}"
        if len(pages) > 1:
            info_text += f" | Seite {page_idx + 1} von {len(pages)}"

        elements.append(Paragraph(info_text, styles['Normal']))
        elements.append(Spacer(1, 15))

        table_data = [["Datum"] + [meal_name for _, meal_name in meal_types]]

        for day in page_days:
            date_key = day.date()
            weekday = get_german_weekday(day)
            row = [f"{weekday}\n{day.strftime('%d.%m.%Y')}"]

            for meal_type, _ in meal_types:
                recipes = meal_grid[date_key][meal_type]
                if recipes:
                    names = [mp.recipe.name if mp.recipe else "Kein Essen" for mp in recipes]
                    row.append("\n".join(names))
                else:
                    row.append("-")

            table_data.append(row)

        date_col_width = 3.5*cm
        meal_col_width = (landscape(A4)[0] - 3*cm - date_col_width) / len(meal_types)
        col_widths = [date_col_width] + [meal_col_width] * len(meal_types)

        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F3F4F6')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('VALIGN', (0, 1), (0, -1), 'MIDDLE'),
            ('FONTSIZE', (1, 1), (-1, -1), 7),
            ('ALIGN', (1, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (1, 1), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#4F46E5')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ]))

        elements.append(table)

    doc.build(elements)

    filename = f"speiseplan_{sanitize_filename(camp.name)}_{make_timestamp()}.pdf"
    return build_and_serve_pdf(buffer, filename)


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

    recipe_ids = set(mp.recipe_id for mp in meal_plans if mp.recipe_id is not None)
    recipes = [r for r in (crud.get_recipe(db, rid) for rid in recipe_ids) if r is not None]

    if not recipes:
        raise HTTPException(status_code=404, detail="No recipes found in meal plan")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    elements = []
    styles, title_style, _, section_heading_style = get_pdf_styles()

    elements.append(Paragraph(f"Rezeptbuch: {camp.name}", title_style))
    elements.append(Spacer(1, 20))

    for i, recipe in enumerate(recipes):
        if i > 0:
            elements.append(PageBreak())

        scaling_factor = camp.participant_count / recipe.base_servings

        elements.append(Paragraph(recipe.name, styles['Heading1']))

        if recipe.description:
            elements.append(Paragraph(recipe.description, styles['Normal']))
            elements.append(Spacer(1, 10))

        info_text = f"Portionen: {camp.participant_count} (Originalrezept: {recipe.base_servings}) | "
        if recipe.preparation_time:
            info_text += f"Vorbereitung: {recipe.preparation_time} min | "
        if recipe.cooking_time:
            info_text += f"Kochzeit: {recipe.cooking_time} min"

        elements.append(Paragraph(f"<i>{info_text}</i>", styles['Normal']))
        elements.append(Spacer(1, 15))

        if recipe.allergens:
            allergen_names = ", ".join([a.name for a in recipe.allergens])
            elements.append(Paragraph(f"<b>Allergene:</b> {allergen_names}", styles['Normal']))
            elements.append(Spacer(1, 10))

        elements.append(Paragraph("<b>Zutaten:</b>", styles['Heading3']))

        ingredient_data = [["Zutat", "Menge", "Einheit"]]
        for ri in recipe.ingredients:
            ingredient_data.append([
                ri.ingredient.name,
                f"{ri.quantity * scaling_factor:.1f}",
                ri.unit
            ])

        ing_table = Table(ingredient_data, colWidths=[10*cm, 3*cm, 3*cm])
        ing_table.setStyle(get_table_style())
        elements.append(ing_table)
        elements.append(Spacer(1, 15))

        if recipe.instructions:
            elements.append(Paragraph("<b>Zubereitung:</b>", styles['Heading3']))
            elements.append(Paragraph(recipe.instructions, styles['Normal']))

    doc.build(elements)

    filename = f"rezeptbuch_{sanitize_filename(camp.name)}_{make_timestamp()}.pdf"
    return build_and_serve_pdf(buffer, filename)


@router.get("/recipes/pdf")
async def export_all_recipes_pdf(
    db: Session = Depends(get_db)
):
    """Export all recipes as PDF with improved formatting"""
    recipes = crud.get_recipes(db, skip=0, limit=10000)

    if not recipes:
        raise HTTPException(status_code=404, detail="No recipes found")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    elements = []
    styles, _, _, section_heading_style = get_pdf_styles()

    title_style = ParagraphStyle(
        'BookTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'BookSubtitle',
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

    # Title page
    elements.append(Paragraph("Rezeptsammlung", title_style))
    elements.append(Paragraph(
        f"{len(recipes)} Rezepte | {datetime.now(timezone.utc).strftime('%d.%m.%Y')}",
        subtitle_style
    ))
    elements.append(Spacer(1, 30))

    # Table of contents
    elements.append(Paragraph("<b>Inhaltsverzeichnis</b>", styles['Heading2']))
    elements.append(Spacer(1, 10))

    toc_data = [["Nr.", "Rezeptname", "Portionen"]]
    for idx, recipe in enumerate(recipes, 1):
        toc_data.append([str(idx), recipe.name, str(recipe.base_servings)])

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

    # Each recipe
    for idx, recipe in enumerate(recipes, 1):
        elements.append(Paragraph(f"{idx}. {recipe.name}", recipe_title_style))

        if recipe.description:
            elements.append(Paragraph(f"<i>{recipe.description}</i>", styles['Normal']))
            elements.append(Spacer(1, 10))

        # Recipe info box
        info_parts = [f"<b>Portionen:</b> {recipe.base_servings}"]
        if recipe.preparation_time:
            info_parts.append(f"<b>Vorbereitung:</b> {recipe.preparation_time} min")
        if recipe.cooking_time:
            info_parts.append(f"<b>Kochzeit:</b> {recipe.cooking_time} min")

        info_table = Table([info_parts], colWidths=[5*cm] * len(info_parts))
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EEF2FF')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1F2937')),
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
            parts = []
            if recipe.tags:
                parts.append(f"<b>Tags:</b> {', '.join(t.name for t in recipe.tags)}")
            if recipe.allergens:
                parts.append(f"<b>Allergene:</b> {', '.join(a.name for a in recipe.allergens)}")
            elements.append(Paragraph(" | ".join(parts), styles['Normal']))
            elements.append(Spacer(1, 15))

        # Ingredients
        elements.append(Paragraph("Zutaten", section_heading_style))

        if recipe.ingredients:
            ingredient_data = [["Zutat", "Menge", "Einheit"]]
            for ri in recipe.ingredients:
                ingredient_data.append([ri.ingredient.name, f"{ri.quantity:.1f}", ri.unit])

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

        # Instructions
        if recipe.instructions:
            elements.append(Paragraph("Zubereitung", section_heading_style))
            elements.append(Paragraph(recipe.instructions.replace('\n', '<br/>'), styles['Normal']))

        if idx < len(recipes):
            elements.append(PageBreak())

    doc.build(elements)

    filename = f"rezeptsammlung_{make_timestamp()}.pdf"
    return build_and_serve_pdf(buffer, filename)
