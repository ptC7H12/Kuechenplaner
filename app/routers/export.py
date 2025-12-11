from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
from io import BytesIO
import os
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

from app.database import get_db
from app import crud, models
from app.services.calculation import calculate_shopping_list, get_camp_statistics

router = APIRouter()

# Register fonts for PDF (for German umlauts support)
# Note: In production, you'd want to use a proper font file
# For now, we'll use the default fonts which have limited Unicode support

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

    # Return as streaming response
    buffer.seek(0)
    filename = f"einkaufsliste_{camp.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
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
    """Export meal plan as PDF"""

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

    title = Paragraph(f"Speiseplan: {camp.name}", title_style)
    elements.append(title)

    # Camp info
    info_text = f"Zeitraum: {camp.start_date.strftime('%d.%m.%Y')} - {camp.end_date.strftime('%d.%m.%Y')}<br/>"
    info_text += f"Teilnehmer: {camp.participant_count}"

    info = Paragraph(info_text, styles['Normal'])
    elements.append(info)
    elements.append(Spacer(1, 20))

    # Generate meal plan table
    current_date = camp.start_date
    while current_date <= camp.end_date:
        date_key = current_date.date()

        # Date heading
        date_heading = Paragraph(
            f"<b>{current_date.strftime('%A, %d.%m.%Y')}</b>",
            styles['Heading2']
        )
        elements.append(date_heading)

        # Meals for this day
        table_data = []

        for meal_type in [models.MealType.BREAKFAST, models.MealType.LUNCH, models.MealType.DINNER]:
            meal_name = {"BREAKFAST": "Frühstück", "LUNCH": "Mittagessen", "DINNER": "Abendessen"}[meal_type.value]
            recipes = meal_grid[date_key][meal_type]

            # Build recipe names list, handling None recipes (no meal planned)
            if recipes:
                names = []
                for mp in recipes:
                    if mp.recipe:
                        names.append(mp.recipe.name)
                    else:
                        names.append("Kein Essen")
                recipe_names = ", ".join(names) if names else "-"
            else:
                recipe_names = "-"

            table_data.append([meal_name, recipe_names])

        table = Table(table_data, colWidths=[4*cm, 12*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F3F4F6')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        current_date += timedelta(days=1)

    # Build PDF
    doc.build(elements)

    buffer.seek(0)
    filename = f"speiseplan_{camp.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
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

    # Get unique recipes
    recipe_ids = set(mp.recipe_id for mp in meal_plans)
    recipes = [crud.get_recipe(db, rid) for rid in recipe_ids]

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

        # Recipe name
        recipe_title = Paragraph(recipe.name, styles['Heading1'])
        elements.append(recipe_title)

        # Description
        if recipe.description:
            desc = Paragraph(recipe.description, styles['Normal'])
            elements.append(desc)
            elements.append(Spacer(1, 10))

        # Basic info
        info_text = f"Portionen: {recipe.base_servings} | "
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

        # Ingredients
        elements.append(Paragraph("<b>Zutaten:</b>", styles['Heading3']))

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

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
