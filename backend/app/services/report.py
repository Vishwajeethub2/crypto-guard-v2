from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from app.services.advanced_risk import FACTOR_MAX_POINTS


# =========================================================
# HELPER FUNCTIONS
# =========================================================


def _to_dict(value):
    """
    Convert common Pydantic/object/dict values into a dictionary.

    This makes the report generator tolerant of:
    - normal dictionaries
    - Pydantic models
    - SQLAlchemy-like objects with attributes
    """
    if value is None:
        return None

    if isinstance(value, dict):
        return value

    model_dump = getattr(value, "model_dump", None)

    if callable(model_dump):
        try:
            return model_dump()
        except Exception:
            pass

    to_dict = getattr(value, "dict", None)

    if callable(to_dict):
        try:
            return to_dict()
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return {
                key: item
                for key, item in vars(value).items()
                if not key.startswith("_")
            }
        except Exception:
            pass

    return None


def _get_value(data, keys, default="N/A"):
    """
    Safely retrieve a value from a dictionary/object.

    Supports several aliases for the same logical field.
    """

    if data is None:
        return default

    converted = _to_dict(data)

    if converted is not None:
        for key in keys:
            if key in converted and converted[key] is not None:
                return converted[key]

    for key in keys:
        try:
            value = getattr(data, key)

            if value is not None:
                return value

        except Exception:
            pass

    return default


def _recursive_find(data, keys):
    """
    Recursively search nested dictionaries/lists/objects.

    This is important because analytical services can return
    structures such as:

        {
            "analytics": {
                "outgoing_connections": 4
            }
        }

    or:

        {
            "data": {
                "graph": {
                    ...
                }
            }
        }

    The report generator should still find the values.
    """

    if data is None:
        return None

    converted = _to_dict(data)

    if converted is not None:

        for key in keys:
            if key in converted and converted[key] is not None:
                return converted[key]

        for value in converted.values():
            found = _recursive_find(value, keys)

            if found is not None:
                return found

    elif isinstance(data, (list, tuple)):

        for item in data:
            found = _recursive_find(item, keys)

            if found is not None:
                return found

    return None


def _format_number(value, decimals=2):
    """
    Format numeric values for PDF readability.
    """

    if value is None:
        return "N/A"

    if isinstance(value, bool):
        return str(value)

    try:
        numeric_value = float(value)

        return f"{numeric_value:,.{decimals}f}"

    except (TypeError, ValueError):
        return str(value)


def _format_ratio(value):
    """
    Format concentration values.

    Example:
        0.998 -> 0.998
    """

    if value is None:
        return "N/A"

    try:
        return f"{float(value):.3f}"

    except (TypeError, ValueError):
        return str(value)


def _format_cell(value):
    """
    Convert any value into a safe printable string.
    """

    if value is None:
        return "N/A"

    return str(value)


def _paragraph_cell(value, style):
    """
    Use Paragraph inside table cells so long blockchain
    addresses and transaction hashes wrap instead of
    overlapping neighbouring columns.
    """

    text = _format_cell(value)

    return Paragraph(
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;"),
        style,
    )


def _find_section(analysis, section_name):
    """
    Find an analysis section such as:
        risk
        graph
        timeline
        intelligence

    First checks the expected direct key, then searches
    common nested containers.
    """

    if analysis is None:
        return None

    converted = _to_dict(analysis)

    if converted is not None:

        direct = converted.get(section_name)

        if direct is not None:
            return direct

        # Common alternative names.
        aliases = {
            "risk": [
                "advanced_risk",
                "risk_analysis",
                "risk_data",
            ],
            "graph": [
                "graph_analytics",
                "graph_analysis",
                "graph_data",
            ],
            "timeline": [
                "timeline_analytics",
                "timeline_analysis",
                "timeline_data",
            ],
            "intelligence": [
                "intelligence_exposure",
                "intelligence_data",
                "exposure",
            ],
        }

        for alias in aliases.get(section_name, []):
            if alias in converted and converted[alias] is not None:
                return converted[alias]

        # Search common containers.
        for container_name in (
            "data",
            "result",
            "analysis",
            "analytics",
        ):
            container = converted.get(container_name)

            if container is not None:

                nested = _find_section(
                    container,
                    section_name,
                )

                if nested is not None:
                    return nested

    return None


def _get_factor_rows(risk_data):
    """
    Normalize advanced-risk factor structures.

    Supports:
    - List-based factor structures
    - Dictionary-based factor structures
    - Nested factor structures
    - Explicit max_points values
    - Fallback to FACTOR_MAX_POINTS when maximums
      are not included in the analysis response
    """

    if risk_data is None:
        return []

    converted = _to_dict(risk_data)

    candidates = []

    # ---------------------------------------------------------
    # 1. Find factor collection
    # ---------------------------------------------------------

    if converted is not None:
        for key in (
            "factors",
            "factor_breakdown",
            "factor_scores",
            "risk_factors",
            "factors_breakdown",
        ):
            candidate = converted.get(key)

            if candidate is not None:
                candidates = candidate
                break

    # ---------------------------------------------------------
    # 2. Recursive fallback
    # ---------------------------------------------------------

    if not candidates:
        candidates = _recursive_find(
            risk_data,
            (
                "factors",
                "factor_breakdown",
                "factor_scores",
                "risk_factors",
            ),
        )

    if candidates is None:
        return []

    # =========================================================
    # 3. Dictionary format
    #
    # Example:
    #
    # {
    #     "connectivity": 10,
    #     "transaction_activity": 5
    # }
    #
    # Or:
    #
    # {
    #     "connectivity": {
    #         "points": 10,
    #         "max_points": 15
    #     }
    # }
    # =========================================================

    if isinstance(candidates, dict):

        rows = []

        for name, value in candidates.items():

            value_dict = _to_dict(value)

            if value_dict is not None:

                # -------------------------------------------------
                # Points
                # -------------------------------------------------

                points = _get_value(
                    value_dict,
                    (
                        "points",
                        "score",
                        "value",
                        "contribution",
                    ),
                    default="N/A",
                )

                # -------------------------------------------------
                # Maximum points
                # -------------------------------------------------

                maximum = _get_value(
                    value_dict,
                    (
                        "max_points",
                        "maximum",
                        "max",
                        "limit",
                        "factor_max",
                    ),
                    default="N/A",
                )

                # If the analysis response does not provide
                # max_points, use the central risk-model definition.
                if maximum == "N/A":
                    maximum = FACTOR_MAX_POINTS.get(
                        name,
                        "N/A",
                    )

            else:

                # Simple dictionary value:
                #
                # "connectivity": 10
                #
                points = value

                maximum = FACTOR_MAX_POINTS.get(
                    name,
                    "N/A",
                )

            rows.append(
                {
                    "factor": name,
                    "points": points,
                    "max_points": maximum,
                }
            )

        return rows

    # =========================================================
    # 4. List format
    #
    # Example:
    #
    # [
    #     {
    #         "factor": "connectivity",
    #         "points": 10,
    #         "max_points": 15
    #     }
    # ]
    # =========================================================

    if isinstance(candidates, (list, tuple)):

        rows = []

        for item in candidates:

            item_dict = _to_dict(item)

            if item_dict is None:
                continue

            # -------------------------------------------------
            # Factor name
            # -------------------------------------------------

            factor_name = _get_value(
                item_dict,
                (
                    "factor",
                    "name",
                    "factor_name",
                    "key",
                ),
                default="N/A",
            )

            # -------------------------------------------------
            # Points
            # -------------------------------------------------

            points = _get_value(
                item_dict,
                (
                    "points",
                    "score",
                    "value",
                    "contribution",
                    "risk_points",
                ),
                default="N/A",
            )

            # -------------------------------------------------
            # Maximum points
            # -------------------------------------------------

            maximum = _get_value(
                item_dict,
                (
                    "max_points",
                    "maximum",
                    "max",
                    "limit",
                    "factor_max",
                ),
                default="N/A",
            )

            # If max_points is missing, use the central
            # advanced-risk factor definition.
            if maximum == "N/A":
                maximum = FACTOR_MAX_POINTS.get(
                    factor_name,
                    "N/A",
                )

            rows.append(
                {
                    "factor": factor_name,
                    "points": points,
                    "max_points": maximum,
                }
            )

        return rows

    return []

def _get_graph_value(graph_data, keys, default="N/A"):
    """
    Retrieve graph analytics values while supporting nested
    graph response structures.
    """

    direct = _get_value(
        graph_data,
        keys,
        default=None,
    )

    if direct is not None:
        return direct

    recursive = _recursive_find(
        graph_data,
        keys,
    )

    if recursive is not None:
        return recursive

    return default


def _get_risk_value(risk_data, keys, default="N/A"):
    """
    Retrieve risk values from direct or nested structures.
    """

    direct = _get_value(
        risk_data,
        keys,
        default=None,
    )

    if direct is not None:
        return direct

    recursive = _recursive_find(
        risk_data,
        keys,
    )

    if recursive is not None:
        return recursive

    return default


# =========================================================
# REPORT GENERATOR
# =========================================================


def generate_investigation_report(
    case,
    wallets,
    notes,
    evidence,
    bookmarks,
    wallet_analyses=None,
):
    """
    Generate a PDF investigation report for a case.

    wallet_analyses should contain one analysis dictionary
    per wallet.

    Expected logical structure:

        {
            "wallet": wallet,
            "risk": {...},
            "graph": {...},
            "timeline": {...},
            "intelligence": {...},
            "ml": {...},
            "aml": {...},
            "vasp_attribution": {...},
        }

    The report generator also accepts nested/aliased
    structures from the analytical services.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title=f"Investigation Report - Case {case.id}",
        author="Crypto Guard V2",
    )

    styles = getSampleStyleSheet()

    # =====================================================
    # STYLES
    # =====================================================

    brand_navy = colors.HexColor("#0F172A")
    brand_blue = colors.HexColor("#1D4ED8")
    brand_teal = colors.HexColor("#0F766E")
    light_panel = colors.HexColor("#F1F5F9")
    border_color = colors.HexColor("#CBD5E1")
    muted_text = colors.HexColor("#64748B")

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=25,
        leading=29,
        textColor=brand_navy,
        spaceAfter=8,
    )

    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=brand_navy,
        spaceBefore=15,
        spaceAfter=8,
        keepWithNext=True,
    )

    subheading_style = ParagraphStyle(
        "ReportSubHeading",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=brand_teal,
        spaceBefore=9,
        spaceAfter=6,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    small_style = ParagraphStyle(
        "ReportSmall",
        parent=styles["BodyText"],
        fontSize=7.5,
        leading=10,
        textColor=muted_text,
    )

    table_cell_style = ParagraphStyle(
        "ReportTableCell",
        parent=styles["BodyText"],
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#334155"),
        spaceAfter=0,
    )

    table_cell_small_style = ParagraphStyle(
        "ReportTableCellSmall",
        parent=styles["BodyText"],
        fontSize=6.5,
        leading=8,
        spaceAfter=0,
    )

    table_header_style = ParagraphStyle(
        "ReportTableHeader",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=colors.white,
        spaceAfter=0,
    )

    table_style = TableStyle(
        [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                brand_navy,
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                border_color,
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.3,
                border_color,
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [colors.white, colors.HexColor("#F8FAFC")],
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
        ]
    )

    def _draw_first_page(canvas_obj, doc):
        canvas_obj.saveState()
        width, height = A4
        canvas_obj.setFillColor(brand_navy)
        canvas_obj.rect(0, height - 8 * mm, width, 8 * mm, fill=1, stroke=0)
        canvas_obj.setFillColor(brand_teal)
        canvas_obj.rect(0, height - 10 * mm, width, 2 * mm, fill=1, stroke=0)
        canvas_obj.setFillColor(muted_text)
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawCentredString(width / 2, 10 * mm, "Crypto Guard V2  |  Cryptocurrency Investigation Report")
        canvas_obj.restoreState()

    def _draw_later_pages(canvas_obj, doc):
        canvas_obj.saveState()
        width, height = A4
        canvas_obj.setStrokeColor(border_color)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(18 * mm, height - 11 * mm, width - 18 * mm, height - 11 * mm)
        canvas_obj.setFont("Helvetica-Bold", 7)
        canvas_obj.setFillColor(brand_navy)
        canvas_obj.drawString(18 * mm, height - 8 * mm, "CRYPTO GUARD V2")
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.setFillColor(muted_text)
        canvas_obj.drawRightString(width - 18 * mm, height - 8 * mm, f"CASE {case.id}  |  INVESTIGATION REPORT")
        canvas_obj.line(18 * mm, 12 * mm, width - 18 * mm, 12 * mm)
        canvas_obj.drawString(18 * mm, 8 * mm, "Development-stage analytical report  |  Analyst review required")
        canvas_obj.drawRightString(width - 18 * mm, 8 * mm, f"Page {doc.page}")
        canvas_obj.restoreState()

    story = []

    story.append(Spacer(1, 28 * mm))
    story.append(Paragraph("CRYPTO GUARD V2", title_style))
    story.append(Paragraph(
        "Cryptocurrency Investigation Report",
        ParagraphStyle(
            "CoverSubtitle", parent=styles["Heading1"], alignment=TA_CENTER,
            fontName="Helvetica", fontSize=16, leading=20, textColor=brand_teal,
            spaceAfter=16,
        ),
    ))

    accent = Table([[""]], colWidths=[160 * mm], rowHeights=[2.5 * mm])
    accent.setStyle(TableStyle([["BACKGROUND", (0,0), (-1,-1), brand_teal]]))
    story.append(accent)
    story.append(Spacer(1, 20 * mm))

    cover_data = [
        [Paragraph("CASE", table_header_style), Paragraph(str(case.id), table_cell_style)],
        [Paragraph("CASE TITLE", table_header_style), _paragraph_cell(case.title, table_cell_style)],
        [Paragraph("STATUS", table_header_style), _paragraph_cell(case.status, table_cell_style)],
        [Paragraph("WALLETS INVESTIGATED", table_header_style), Paragraph(str(len(wallets)), table_cell_style)],
        [Paragraph("REPORT GENERATED", table_header_style), Paragraph(f"{datetime.utcnow().isoformat()} UTC", table_cell_style)],
    ]
    cover_table = Table(cover_data, colWidths=[55 * mm, 105 * mm])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), brand_navy),
        ("TEXTCOLOR", (0,0), (0,-1), colors.white),
        ("BACKGROUND", (1,0), (1,-1), light_panel),
        ("BOX", (0,0), (-1,-1), 0.7, border_color),
        ("INNERGRID", (0,0), (-1,-1), 0.4, border_color),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,-1), 9),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 22 * mm))
    story.append(Paragraph(
        "Investigation scope",
        ParagraphStyle("CoverScope", parent=subheading_style, alignment=TA_CENTER, textColor=brand_navy),
    ))
    story.append(Paragraph(
        "Blockchain activity, risk indicators, graph relationships, temporal activity, "
        "intelligence exposure, and case documentation available at the time of report generation.",
        ParagraphStyle("CoverBody", parent=body_style, alignment=TA_CENTER, fontSize=9.5, leading=14, leftIndent=15*mm, rightIndent=15*mm),
    ))
    story.append(PageBreak())

    # =====================================================
    # 1. CASE OVERVIEW
    # =====================================================

    story.append(
        Paragraph(
            "1. Case Overview",
            heading_style,
        )
    )

    story.append(
        Paragraph(
            "This report summarizes the cryptocurrency "
            "investigation data currently available in "
            "Crypto Guard V2 for the selected case.",
            body_style,
        )
    )

    overview_data = [
        [
            Paragraph("Property", table_header_style),
            Paragraph("Value", table_header_style),
        ],
        ["Case ID", str(case.id)],
        ["Case Title", str(case.title)],
        ["Status", str(case.status)],
        ["Wallet Count", str(len(wallets))],
        ["Notes", str(len(notes))],
        ["Evidence Items", str(len(evidence))],
        ["Bookmarks", str(len(bookmarks))],
    ]

    overview_table = Table(
        overview_data,
        colWidths=[
            55 * mm,
            105 * mm,
        ],
        repeatRows=1,
    )

    overview_table.setStyle(table_style)

    story.append(overview_table)

    # =====================================================
    # 2. INVESTIGATED WALLETS
    # =====================================================

    story.append(
        Paragraph(
            "2. Investigated Wallets",
            heading_style,
        )
    )

    wallet_rows = [
        [
            Paragraph("ID", table_header_style),
            Paragraph("Chain", table_header_style),
            Paragraph("Address", table_header_style),
            Paragraph("Label", table_header_style),
        ]
    ]

    for wallet in wallets:

        wallet_rows.append(
            [
                str(wallet.id),
                str(wallet.chain),
                _paragraph_cell(
                    wallet.address,
                    table_cell_small_style,
                ),
                _paragraph_cell(
                    wallet.label or "",
                    table_cell_style,
                ),
            ]
        )

    if len(wallet_rows) == 1:

        wallet_rows.append(
            [
                "-",
                "-",
                "No wallets",
                "-",
            ]
        )

    wallet_table = Table(
        wallet_rows,
        colWidths=[
            12 * mm,
            24 * mm,
            82 * mm,
            42 * mm,
        ],
        repeatRows=1,
    )

    wallet_table.setStyle(table_style)

    story.append(wallet_table)

    # =====================================================
    # 3. RISK ASSESSMENT
    # =====================================================

    story.append(
        Paragraph(
            "3. Risk Assessment",
            heading_style,
        )
    )

    if wallet_analyses:

        for analysis in wallet_analyses:

            wallet = analysis["wallet"]

            risk_data = _find_section(
                analysis,
                "risk",
            )

            story.append(
                Paragraph(
                    f"Wallet {wallet.id} — {wallet.address}",
                    subheading_style,
                )
            )

            if risk_data:

                risk_score = _get_risk_value(
                    risk_data,
                    (
                        "score",
                        "risk_score",
                        "total_score",
                    ),
                )

                risk_level = _get_risk_value(
                    risk_data,
                    (
                        "level",
                        "risk_level",
                    ),
                )

                risk_rows = [
                    [
                        Paragraph("Metric", table_header_style),
                        Paragraph("Value", table_header_style),
                    ],
                    [
                        "Risk Score",
                        _format_cell(risk_score),
                    ],
                    [
                        "Risk Level",
                        _format_cell(risk_level),
                    ],
                ]

                risk_table = Table(
                    risk_rows,
                    colWidths=[
                        55 * mm,
                        105 * mm,
                    ],
                    repeatRows=1,
                )

                risk_table.setStyle(table_style)

                story.append(risk_table)

                risk_card = Table([
                    [
                        Paragraph("ANALYTICAL RISK SCORE", table_header_style),
                        Paragraph(_format_cell(risk_score), ParagraphStyle("RiskScore", parent=table_header_style, fontSize=18, leading=20, alignment=TA_CENTER)),
                        Paragraph("DEVELOPMENT-STAGE", table_header_style),
                    ],
                    [
                        Paragraph("Current model output", table_cell_style),
                        Paragraph("/ 100", ParagraphStyle("RiskDenom", parent=table_cell_style, alignment=TA_CENTER, textColor=muted_text)),
                        Paragraph("Not a validated real-world probability", table_cell_style),
                    ],
                ], colWidths=[55*mm, 35*mm, 70*mm])
                risk_card.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), brand_navy),
                    ("BACKGROUND", (0,1), (-1,1), light_panel),
                    ("BOX", (0,0), (-1,-1), 0.7, border_color),
                    ("INNERGRID", (0,0), (-1,-1), 0.3, border_color),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("ALIGN", (1,0), (1,-1), "CENTER"),
                    ("LEFTPADDING", (0,0), (-1,-1), 7),
                    ("RIGHTPADDING", (0,0), (-1,-1), 7),
                    ("TOPPADDING", (0,0), (-1,-1), 6),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
                ]))
                story.append(risk_card)
                story.append(Spacer(1, 8))

                factor_rows_data = _get_factor_rows(
                    risk_data
                )

                # -------------------------------------------------
                # FALLBACK:
                # If the response doesn't contain an explicit
                # factor list, try extracting known development
                # factor names individually.
                # -------------------------------------------------

                if not factor_rows_data:

                    known_factors = [
                        "connectivity",
                        "transaction_activity",
                        "value_flow",
                        "asset_diversity",
                        "intelligence_exposure",
                        "graph_risk",
                        "temporal_risk",
                    ]

                    for factor_name in known_factors:

                        factor_value = _recursive_find(
                            risk_data,
                            (
                                factor_name,
                            ),
                        )

                        if factor_value is not None:

                            factor_dict = _to_dict(
                                factor_value
                            )

                            if factor_dict:

                                points = _get_value(
                                    factor_dict,
                                    (
                                        "points",
                                        "score",
                                        "value",
                                        "contribution",
                                    ),
                                    default="N/A",
                                )

                                maximum = _get_value(
                                    factor_dict,
                                    (
                                        "max_points",
                                        "maximum",
                                        "max",
                                        "limit",
                                        "factor_max",
                                    ),
                                    default="N/A",
                                )

                                if maximum == "N/A":
                                    maximum = FACTOR_MAX_POINTS.get(
                                        factor_name,
                                        "N/A",
                                    )

                            else:

                                points = factor_value
                                maximum = FACTOR_MAX_POINTS.get(
                                    factor_name,
                                    "N/A",
                                )

                            factor_rows_data.append(
                                {
                                    "factor": factor_name,
                                    "points": points,
                                    "max_points": maximum,
                                }
                            )

                if factor_rows_data:

                    story.append(
                        Paragraph(
                            "Risk Factors",
                            subheading_style,
                        )
                    )

                    factor_rows = [
                        [
                            Paragraph(
                                "Factor",
                                table_header_style,
                            ),
                            Paragraph(
                                "Points",
                                table_header_style,
                            ),
                            Paragraph(
                                "Maximum",
                                table_header_style,
                            ),
                        ]
                    ]

                    for factor in factor_rows_data:

                        factor_rows.append(
                            [
                                _paragraph_cell(
                                    factor.get(
                                        "factor",
                                        "N/A",
                                    ),
                                    table_cell_style,
                                ),
                                _format_cell(
                                    factor.get(
                                        "points",
                                        "N/A",
                                    )
                                ),
                                _format_cell(
                                    factor.get(
                                        "max_points",
                                        "N/A",
                                    )
                                ),
                            ]
                        )

                    factor_table = Table(
                        factor_rows,
                        colWidths=[
                            75 * mm,
                            42 * mm,
                            43 * mm,
                        ],
                        repeatRows=1,
                    )

                    factor_table.setStyle(
                        table_style
                    )

                    story.append(
                        factor_table
                    )

                else:

                    story.append(
                        Paragraph(
                            "No individual risk factor "
                            "breakdown was available.",
                            body_style,
                        )
                    )

            else:

                story.append(
                    Paragraph(
                        "No risk assessment data "
                        "was available.",
                        body_style,
                    )
                )

            story.append(
                Spacer(1, 10)
            )

    else:

        story.append(
            Paragraph(
                "No wallet risk assessment data "
                "was available.",
                body_style,
            )
        )

    # =====================================================
    # 4. ANALYST NOTES
    # =====================================================

    story.append(
        Paragraph(
            "4. Analyst Notes",
            heading_style,
        )
    )

    if notes:

        for note in notes:

            story.append(
                Paragraph(
                    f"<b>Note #{note.id}</b>",
                    body_style,
                )
            )

            story.append(
                Paragraph(
                    str(note.content),
                    body_style,
                )
            )

            story.append(
                Spacer(1, 4)
            )

    else:

        story.append(
            Paragraph(
                "No analyst notes were recorded.",
                body_style,
            )
        )

    # =====================================================
    # 5. EVIDENCE
    # =====================================================

    story.append(
        Paragraph(
            "5. Evidence",
            heading_style,
        )
    )

    if evidence:

        evidence_rows = [
            [
                Paragraph("Type", table_header_style),
                Paragraph("Title", table_header_style),
                Paragraph("Reference", table_header_style),
            ]
        ]

        for item in evidence:

            evidence_rows.append(
                [
                    _paragraph_cell(
                        item.evidence_type,
                        table_cell_style,
                    ),
                    _paragraph_cell(
                        item.title,
                        table_cell_style,
                    ),
                    _paragraph_cell(
                        item.reference or "",
                        table_cell_small_style,
                    ),
                ]
            )

        evidence_table = Table(
            evidence_rows,
            colWidths=[
                30 * mm,
                55 * mm,
                75 * mm,
            ],
            repeatRows=1,
        )

        evidence_table.setStyle(
            table_style
        )

        story.append(
            evidence_table
        )

    else:

        story.append(
            Paragraph(
                "No evidence items were recorded.",
                body_style,
            )
        )

    # =====================================================
    # 6. BOOKMARKS
    # =====================================================

    story.append(
        Paragraph(
            "6. Investigation Bookmarks",
            heading_style,
        )
    )

    if bookmarks:

        bookmark_rows = [
            [
                Paragraph("Type", table_header_style),
                Paragraph("Title", table_header_style),
                Paragraph("Reference", table_header_style),
            ]
        ]

        for bookmark in bookmarks:

            bookmark_rows.append(
                [
                    _paragraph_cell(
                        bookmark.bookmark_type,
                        table_cell_style,
                    ),
                    _paragraph_cell(
                        bookmark.title,
                        table_cell_style,
                    ),
                    _paragraph_cell(
                        bookmark.reference,
                        table_cell_small_style,
                    ),
                ]
            )

        bookmark_table = Table(
            bookmark_rows,
            colWidths=[
                30 * mm,
                55 * mm,
                75 * mm,
            ],
            repeatRows=1,
        )

        bookmark_table.setStyle(
            table_style
        )

        story.append(
            bookmark_table
        )

    else:

        story.append(
            Paragraph(
                "No investigation bookmarks "
                "were recorded.",
                body_style,
            )
        )

    # =====================================================
    # 7. BLOCKCHAIN GRAPH ANALYSIS
    # =====================================================

    story.append(
        Paragraph(
            "7. Blockchain Graph Analysis",
            heading_style,
        )
    )

    if wallet_analyses:

        for analysis in wallet_analyses:

            wallet = analysis["wallet"]

            graph_data = _find_section(
                analysis,
                "graph",
            )

            story.append(
                Paragraph(
                    f"Wallet {wallet.id} — {wallet.address}",
                    subheading_style,
                )
            )

            if graph_data:

                outgoing_connections = _get_graph_value(
                    graph_data,
                    (
                        "outgoing_connections",
                        "outgoing_connection_count",
                    ),
                )

                incoming_connections = _get_graph_value(
                    graph_data,
                    (
                        "incoming_connections",
                        "incoming_connection_count",
                    ),
                )

                outgoing_transactions = _get_graph_value(
                    graph_data,
                    (
                        "outgoing_transaction_count",
                        "outgoing_transactions",
                    ),
                )

                incoming_transactions = _get_graph_value(
                    graph_data,
                    (
                        "incoming_transaction_count",
                        "incoming_transactions",
                    ),
                )

                outgoing_value = _get_graph_value(
                    graph_data,
                    (
                        "outgoing_value",
                    ),
                )

                incoming_value = _get_graph_value(
                    graph_data,
                    (
                        "incoming_value",
                    ),
                )

                fan_out = _get_graph_value(
                    graph_data,
                    (
                        "fan_out",
                    ),
                )

                fan_in = _get_graph_value(
                    graph_data,
                    (
                        "fan_in",
                    ),
                )

                outgoing_concentration = _get_graph_value(
                    graph_data,
                    (
                        "outgoing_concentration",
                    ),
                )

                incoming_concentration = _get_graph_value(
                    graph_data,
                    (
                        "incoming_concentration",
                    ),
                )

                multi_hop_exposure = _get_graph_value(
                    graph_data,
                    (
                        "multi_hop_exposure_count",
                        "multi_hop_exposure",
                    ),
                )

                graph_rows = [
                    [
                        Paragraph(
                            "Metric",
                            table_header_style,
                        ),
                        Paragraph(
                            "Value",
                            table_header_style,
                        ),
                    ],
                    [
                        "Outgoing Connections",
                        _format_cell(
                            outgoing_connections
                        ),
                    ],
                    [
                        "Incoming Connections",
                        _format_cell(
                            incoming_connections
                        ),
                    ],
                    [
                        "Outgoing Transactions",
                        _format_cell(
                            outgoing_transactions
                        ),
                    ],
                    [
                        "Incoming Transactions",
                        _format_cell(
                            incoming_transactions
                        ),
                    ],
                    [
                        "Outgoing Value",
                        _format_number(
                            outgoing_value
                        ),
                    ],
                    [
                        "Incoming Value",
                        _format_number(
                            incoming_value
                        ),
                    ],
                    [
                        "Fan Out",
                        _format_cell(
                            fan_out
                        ),
                    ],
                    [
                        "Fan In",
                        _format_cell(
                            fan_in
                        ),
                    ],
                    [
                        "Outgoing Concentration",
                        _format_ratio(
                            outgoing_concentration
                        ),
                    ],
                    [
                        "Incoming Concentration",
                        _format_ratio(
                            incoming_concentration
                        ),
                    ],
                    [
                        "Multi-Hop Exposure",
                        _format_cell(
                            multi_hop_exposure
                        ),
                    ],
                ]

                graph_table = Table(
                    graph_rows,
                    colWidths=[
                        75 * mm,
                        85 * mm,
                    ],
                    repeatRows=1,
                )

                graph_table.setStyle(
                    table_style
                )

                story.append(
                    graph_table
                )

                graph_signals = _recursive_find(
                    graph_data,
                    (
                        "graph_signals",
                        "signals",
                    ),
                )

                if isinstance(
                    graph_signals,
                    (list, tuple),
                ) and graph_signals:

                    story.append(
                        Spacer(1, 8)
                    )

                    story.append(
                        Paragraph(
                            "Graph Signals",
                            subheading_style,
                        )
                    )

                    signal_rows = [
                        [
                            Paragraph(
                                "Signal",
                                table_header_style,
                            ),
                            Paragraph(
                                "Severity",
                                table_header_style,
                            ),
                            Paragraph(
                                "Description",
                                table_header_style,
                            ),
                        ]
                    ]

                    for signal in graph_signals:

                        signal_dict = (
                            _to_dict(signal)
                            or {}
                        )

                        signal_name = _get_value(
                            signal_dict,
                            (
                                "signal",
                                "indicator",
                                "name",
                            ),
                        )

                        severity = _get_value(
                            signal_dict,
                            (
                                "severity",
                                "level",
                            ),
                        )

                        description = _get_value(
                            signal_dict,
                            (
                                "description",
                                "reason",
                            ),
                            default="",
                        )

                        signal_rows.append(
                            [
                                _paragraph_cell(
                                    signal_name,
                                    table_cell_style,
                                ),
                                _paragraph_cell(
                                    severity,
                                    table_cell_style,
                                ),
                                _paragraph_cell(
                                    description,
                                    table_cell_style,
                                ),
                            ]
                        )

                    signal_table = Table(
                        signal_rows,
                        colWidths=[
                            50 * mm,
                            30 * mm,
                            80 * mm,
                        ],
                        repeatRows=1,
                    )

                    signal_table.setStyle(
                        table_style
                    )

                    story.append(
                        signal_table
                    )

            else:

                story.append(
                    Paragraph(
                        "No graph analytics data "
                        "was available.",
                        body_style,
                    )
                )

            story.append(
                Spacer(1, 10)
            )

    else:

        story.append(
            Paragraph(
                "No graph analytics data "
                "was available.",
                body_style,
            )
        )

    # =====================================================
    # 8. TIMELINE ANALYSIS
    # =====================================================

    story.append(
        Paragraph(
            "8. Timeline Analysis",
            heading_style,
        )
    )

    if wallet_analyses:

        for analysis in wallet_analyses:

            wallet = analysis["wallet"]

            timeline_data = _find_section(
                analysis,
                "timeline",
            )

            story.append(
                Paragraph(
                    f"Wallet {wallet.id} — {wallet.address}",
                    subheading_style,
                )
            )

            if timeline_data:

                first_activity = _get_value(
                    timeline_data,
                    (
                        "first_activity",
                    ),
                )

                last_activity = _get_value(
                    timeline_data,
                    (
                        "last_activity",
                    ),
                )

                total_transactions = _get_value(
                    timeline_data,
                    (
                        "total_transactions",
                    ),
                )

                incoming_transactions = _get_value(
                    timeline_data,
                    (
                        "incoming_transactions",
                    ),
                )

                outgoing_transactions = _get_value(
                    timeline_data,
                    (
                        "outgoing_transactions",
                    ),
                )

                incoming_value = _get_value(
                    timeline_data,
                    (
                        "incoming_value",
                    ),
                )

                outgoing_value = _get_value(
                    timeline_data,
                    (
                        "outgoing_value",
                    ),
                )

                total_value = _get_value(
                    timeline_data,
                    (
                        "total_value",
                    ),
                )

                activity_duration = _get_value(
                    timeline_data,
                    (
                        "activity_duration_seconds",
                    ),
                )

                average_gap = _get_value(
                    timeline_data,
                    (
                        "average_transaction_gap_seconds",
                    ),
                )

                shortest_gap = _get_value(
                    timeline_data,
                    (
                        "shortest_transaction_gap_seconds",
                    ),
                )

                longest_gap = _get_value(
                    timeline_data,
                    (
                        "longest_transaction_gap_seconds",
                    ),
                )

                timeline_rows = [
                    [
                        Paragraph(
                            "Metric",
                            table_header_style,
                        ),
                        Paragraph(
                            "Value",
                            table_header_style,
                        ),
                    ],
                    [
                        "First Activity",
                        _format_cell(
                            first_activity
                        ),
                    ],
                    [
                        "Last Activity",
                        _format_cell(
                            last_activity
                        ),
                    ],
                    [
                        "Total Transactions",
                        _format_cell(
                            total_transactions
                        ),
                    ],
                    [
                        "Incoming Transactions",
                        _format_cell(
                            incoming_transactions
                        ),
                    ],
                    [
                        "Outgoing Transactions",
                        _format_cell(
                            outgoing_transactions
                        ),
                    ],
                    [
                        "Incoming Value",
                        _format_number(
                            incoming_value
                        ),
                    ],
                    [
                        "Outgoing Value",
                        _format_number(
                            outgoing_value
                        ),
                    ],
                    [
                        "Total Value",
                        _format_number(
                            total_value
                        ),
                    ],
                    [
                        "Activity Duration (seconds)",
                        _format_number(
                            activity_duration
                        ),
                    ],
                    [
                        "Average Transaction Gap",
                        _format_number(
                            average_gap
                        ),
                    ],
                    [
                        "Shortest Transaction Gap",
                        _format_number(
                            shortest_gap
                        ),
                    ],
                    [
                        "Longest Transaction Gap",
                        _format_number(
                            longest_gap
                        ),
                    ],
                ]

                timeline_table = Table(
                    timeline_rows,
                    colWidths=[
                        75 * mm,
                        85 * mm,
                    ],
                    repeatRows=1,
                )

                timeline_table.setStyle(
                    table_style
                )

                story.append(
                    timeline_table
                )

                # -------------------------------------------------
                # ACTIVITY BURSTS
                # -------------------------------------------------

                bursts = _get_value(
                    timeline_data,
                    (
                        "bursts",
                        "activity_bursts",
                    ),
                    default=[],
                )

                if isinstance(
                    bursts,
                    (list, tuple),
                ) and bursts:

                    story.append(
                        Spacer(1, 8)
                    )

                    story.append(
                        Paragraph(
                            "Detected Activity Bursts",
                            subheading_style,
                        )
                    )

                    burst_rows = [
                        [
                            Paragraph(
                                "Start",
                                table_header_style,
                            ),
                            Paragraph(
                                "End",
                                table_header_style,
                            ),
                            Paragraph(
                                "Transactions",
                                table_header_style,
                            ),
                            Paragraph(
                                "Duration",
                                table_header_style,
                            ),
                        ]
                    ]

                    for burst in bursts:

                        burst_dict = (
                            _to_dict(burst)
                            or {}
                        )

                        burst_rows.append(
                            [
                                _paragraph_cell(
                                    _get_value(
                                        burst_dict,
                                        (
                                            "start_time",
                                            "start",
                                        ),
                                    ),
                                    table_cell_small_style,
                                ),
                                _paragraph_cell(
                                    _get_value(
                                        burst_dict,
                                        (
                                            "end_time",
                                            "end",
                                        ),
                                    ),
                                    table_cell_small_style,
                                ),
                                _format_cell(
                                    _get_value(
                                        burst_dict,
                                        (
                                            "transaction_count",
                                            "transactions",
                                        ),
                                    )
                                ),
                                _format_number(
                                    _get_value(
                                        burst_dict,
                                        (
                                            "duration_seconds",
                                            "duration",
                                        ),
                                    )
                                ),
                            ]
                        )

                    burst_table = Table(
                        burst_rows,
                        colWidths=[
                            45 * mm,
                            45 * mm,
                            30 * mm,
                            40 * mm,
                        ],
                        repeatRows=1,
                    )

                    burst_table.setStyle(
                        table_style
                    )

                    story.append(
                        burst_table
                    )

                # -------------------------------------------------
                # TEMPORAL SIGNALS
                # -------------------------------------------------

                temporal_signals = _get_value(
                    timeline_data,
                    (
                        "temporal_signals",
                        "signals",
                    ),
                    default=[],
                )

                if isinstance(
                    temporal_signals,
                    (list, tuple),
                ) and temporal_signals:

                    story.append(
                        Spacer(1, 8)
                    )

                    story.append(
                        Paragraph(
                            "Temporal Signals",
                            subheading_style,
                        )
                    )

                    temporal_rows = [
                        [
                            Paragraph(
                                "Signal",
                                table_header_style,
                            ),
                            Paragraph(
                                "Severity",
                                table_header_style,
                            ),
                            Paragraph(
                                "Description",
                                table_header_style,
                            ),
                        ]
                    ]

                    for signal in temporal_signals:

                        signal_dict = (
                            _to_dict(signal)
                            or {}
                        )

                        temporal_rows.append(
                            [
                                _paragraph_cell(
                                    _get_value(
                                        signal_dict,
                                        (
                                            "signal",
                                            "indicator",
                                            "name",
                                        ),
                                    ),
                                    table_cell_style,
                                ),
                                _paragraph_cell(
                                    _get_value(
                                        signal_dict,
                                        (
                                            "severity",
                                            "level",
                                        ),
                                    ),
                                    table_cell_style,
                                ),
                                _paragraph_cell(
                                    _get_value(
                                        signal_dict,
                                        (
                                            "description",
                                            "reason",
                                        ),
                                        default="",
                                    ),
                                    table_cell_style,
                                ),
                            ]
                        )

                    temporal_table = Table(
                        temporal_rows,
                        colWidths=[
                            50 * mm,
                            30 * mm,
                            80 * mm,
                        ],
                        repeatRows=1,
                    )

                    temporal_table.setStyle(
                        table_style
                    )

                    story.append(
                        temporal_table
                    )

                # -------------------------------------------------
                # LARGEST TRANSACTIONS
                # -------------------------------------------------

                largest_transactions = _get_value(
                    timeline_data,
                    (
                        "largest_transactions",
                        "largest_transfers",
                    ),
                    default=[],
                )

                if isinstance(
                    largest_transactions,
                    (list, tuple),
                ) and largest_transactions:

                    story.append(
                        Spacer(1, 10)
                    )

                    story.append(
                        Paragraph(
                            "Largest Transactions",
                            subheading_style,
                        )
                    )

                    transaction_rows = [
                        [
                            Paragraph(
                                "Transaction",
                                table_header_style,
                            ),
                            Paragraph(
                                "Direction",
                                table_header_style,
                            ),
                            Paragraph(
                                "Counterparty",
                                table_header_style,
                            ),
                            Paragraph(
                                "Asset",
                                table_header_style,
                            ),
                            Paragraph(
                                "Value",
                                table_header_style,
                            ),
                            Paragraph(
                                "Block",
                                table_header_style,
                            ),
                        ]
                    ]

                    for transaction in largest_transactions:

                        tx_dict = (
                            _to_dict(transaction)
                            or {}
                        )

                        transaction_hash = _get_value(
                            tx_dict,
                            (
                                "transaction_hash",
                                "hash",
                                "tx_hash",
                            ),
                        )

                        direction = _get_value(
                            tx_dict,
                            (
                                "direction",
                            ),
                        )

                        counterparty = _get_value(
                            tx_dict,
                            (
                                "counterparty",
                                "address",
                            ),
                        )

                        asset = _get_value(
                            tx_dict,
                            (
                                "asset",
                                "token",
                            ),
                        )

                        value = _get_value(
                            tx_dict,
                            (
                                "value",
                                "amount",
                            ),
                        )

                        block_number = _get_value(
                            tx_dict,
                            (
                                "block_number",
                                "block",
                            ),
                        )

                        transaction_rows.append(
                            [
                                _paragraph_cell(
                                    transaction_hash,
                                    table_cell_small_style,
                                ),
                                _paragraph_cell(
                                    direction,
                                    table_cell_style,
                                ),
                                _paragraph_cell(
                                    counterparty,
                                    table_cell_small_style,
                                ),
                                _paragraph_cell(
                                    asset,
                                    table_cell_style,
                                ),
                                _format_number(
                                    value
                                ),
                                _format_cell(
                                    block_number
                                ),
                            ]
                        )

                    # IMPORTANT:
                    # Wider transaction/counterparty columns and
                    # Paragraph cells prevent the overlap seen in
                    # the previous PDF.
                    transaction_table = Table(
                        transaction_rows,
                        colWidths=[
                            42 * mm,
                            20 * mm,
                            48 * mm,
                            18 * mm,
                            22 * mm,
                            18 * mm,
                        ],
                        repeatRows=1,
                    )

                    transaction_table.setStyle(
                        table_style
                    )

                    story.append(
                        transaction_table
                    )

            else:

                story.append(
                    Paragraph(
                        "No timeline analytics data "
                        "was available.",
                        body_style,
                    )
                )

            story.append(
                Spacer(1, 10)
            )

    else:

        story.append(
            Paragraph(
                "No timeline analytics data "
                "was available.",
                body_style,
            )
        )

    # =====================================================
    # 9. ML / AML ANALYSIS
    # =====================================================

    story.append(
        Paragraph(
            "9. ML / AML Analysis",
            heading_style,
        )
    )

    story.append(
        Paragraph(
            "This section records the research-stage machine-learning output "
            "and the structured behavioral evidence assessment available for "
            "analyst review. The ML output is not a validated real-world AML "
            "probability and is not a definitive illicit-activity determination.",
            body_style,
        )
    )

    if wallet_analyses:
        ml_aml_found = False

        for analysis in wallet_analyses:
            wallet = analysis["wallet"]
            ml_data = analysis.get("ml")
            aml_data = analysis.get("aml")

            if not ml_data and not aml_data:
                continue

            ml_aml_found = True

            story.append(
                Paragraph(
                    f"Wallet {wallet.id} — {wallet.address}",
                    subheading_style,
                )
            )

            # -------------------------------------------------
            # ML MODEL OUTPUT
            # -------------------------------------------------
            if ml_data:
                prediction = _get_value(
                    ml_data,
                    ("prediction",),
                    default="N/A",
                )
                probability = _get_value(
                    ml_data,
                    ("probability",),
                    default="N/A",
                )
                model_version = _get_value(
                    ml_data,
                    ("model_version",),
                    default="N/A",
                )
                schema_version = _get_value(
                    ml_data,
                    ("schema_version",),
                    default="N/A",
                )
                status = _get_value(
                    ml_data,
                    ("status",),
                    default="N/A",
                )

                if isinstance(probability, (int, float)):
                    probability_display = f"{float(probability) * 100:.2f}%"
                else:
                    probability_display = _format_cell(probability)

                ml_rows = [
                    [
                        Paragraph("ML Output", table_header_style),
                        Paragraph("Value", table_header_style),
                    ],
                    ["Prediction", _format_cell(prediction)],
                    ["Model Output", probability_display],
                    ["Model Version", _format_cell(model_version)],
                    ["Schema Version", _format_cell(schema_version)],
                    ["Status", _format_cell(status)],
                ]

                ml_table = Table(
                    ml_rows,
                    colWidths=[55 * mm, 105 * mm],
                    repeatRows=1,
                )
                ml_table.setStyle(table_style)
                story.append(ml_table)

                features = _get_value(
                    ml_data,
                    ("features", "feature_values", "model_feature_values"),
                    default={},
                )
                features_dict = _to_dict(features) or {}

                if features_dict:
                    story.append(Spacer(1, 7))
                    story.append(
                        Paragraph(
                            "Model Features",
                            subheading_style,
                        )
                    )

                    feature_rows = [
                        [
                            Paragraph("Feature", table_header_style),
                            Paragraph("Value", table_header_style),
                        ]
                    ]

                    for feature_name, feature_value in features_dict.items():
                        feature_rows.append([
                            _paragraph_cell(feature_name, table_cell_style),
                            _paragraph_cell(
                                _format_number(feature_value)
                                if isinstance(feature_value, (int, float))
                                else feature_value,
                                table_cell_style,
                            ),
                        ])

                    feature_table = Table(
                        feature_rows,
                        colWidths=[100 * mm, 60 * mm],
                        repeatRows=1,
                    )
                    feature_table.setStyle(table_style)
                    story.append(feature_table)

                notice = _get_value(
                    ml_data,
                    ("notice",),
                    default="",
                )
                if notice:
                    story.append(Spacer(1, 6))
                    story.append(
                        Paragraph(
                            f"<b>ML Notice:</b> {_format_cell(notice)}",
                            small_style,
                        )
                    )

            # -------------------------------------------------
            # AML EVIDENCE ASSESSMENT
            # -------------------------------------------------
            if aml_data:
                story.append(Spacer(1, 9))
                story.append(
                    Paragraph(
                        "AML Evidence Assessment",
                        subheading_style,
                    )
                )

                review_status = _get_value(
                    aml_data,
                    ("review_status",),
                    default="N/A",
                )
                assessment_type = _get_value(
                    aml_data,
                    ("assessment_type",),
                    default="N/A",
                )
                indicator_count = _get_value(
                    aml_data,
                    ("indicator_count",),
                    default="N/A",
                )
                high_count = _get_value(
                    aml_data,
                    ("high_severity_indicator_count",),
                    default="N/A",
                )
                medium_count = _get_value(
                    aml_data,
                    ("medium_severity_indicator_count",),
                    default="N/A",
                )

                aml_rows = [
                    [
                        Paragraph("Assessment", table_header_style),
                        Paragraph("Value", table_header_style),
                    ],
                    ["Review Status", _format_cell(review_status)],
                    ["Assessment Type", _format_cell(assessment_type)],
                    ["Indicator Count", _format_cell(indicator_count)],
                    ["High Severity Indicators", _format_cell(high_count)],
                    ["Medium Severity Indicators", _format_cell(medium_count)],
                ]

                aml_table = Table(
                    aml_rows,
                    colWidths=[55 * mm, 105 * mm],
                    repeatRows=1,
                )
                aml_table.setStyle(table_style)
                story.append(aml_table)

                signals = _get_value(
                    aml_data,
                    ("signals", "indicators"),
                    default=[],
                )

                if isinstance(signals, (list, tuple)) and signals:
                    story.append(Spacer(1, 7))
                    signal_rows = [
                        [
                            Paragraph("Source", table_header_style),
                            Paragraph("Signal", table_header_style),
                            Paragraph("Severity", table_header_style),
                            Paragraph("Reason", table_header_style),
                        ]
                    ]

                    for signal in signals:
                        signal_dict = _to_dict(signal) or {}
                        signal_name = _get_value(
                            signal_dict,
                            ("signal",),
                            default="N/A",
                        )
                        source = _get_value(
                            signal_dict,
                            ("source",),
                            default="N/A",
                        )
                        severity = _get_value(
                            signal_dict,
                            ("severity", "level"),
                            default="N/A",
                        )
                        reason = _get_value(
                            signal_dict,
                            ("reason", "description"),
                            default="",
                        )

                        signal_rows.append([
                            _paragraph_cell(source, table_cell_style),
                            _paragraph_cell(signal_name, table_cell_style),
                            _paragraph_cell(severity, table_cell_style),
                            _paragraph_cell(reason, table_cell_style),
                        ])

                    signal_table = Table(
                        signal_rows,
                        colWidths=[22 * mm, 38 * mm, 25 * mm, 75 * mm],
                        repeatRows=1,
                    )
                    signal_table.setStyle(table_style)
                    story.append(signal_table)

                aml_notice = _get_value(
                    aml_data,
                    ("notice",),
                    default="",
                )
                if aml_notice:
                    story.append(Spacer(1, 6))
                    story.append(
                        Paragraph(
                            f"<b>AML Notice:</b> {_format_cell(aml_notice)}",
                            small_style,
                        )
                    )

            story.append(Spacer(1, 10))

        if not ml_aml_found:
            story.append(
                Paragraph(
                    "No ML / AML analysis data was available for the analyzed wallets.",
                    body_style,
                )
            )

    else:
        story.append(
            Paragraph(
                "No ML / AML analysis data was available.",
                body_style,
            )
        )

    # =====================================================
    # 10. INTELLIGENCE EXPOSURE
    # =====================================================

    story.append(
        Paragraph(
            "10. Intelligence Exposure",
            heading_style,
        )
    )

    if wallet_analyses:

        for analysis in wallet_analyses:

            wallet = analysis["wallet"]

            intelligence_data = _find_section(
                analysis,
                "intelligence",
            )

            story.append(
                Paragraph(
                    f"Wallet {wallet.id} — {wallet.address}",
                    subheading_style,
                )
            )

            # ML / AML output is rendered in the dedicated section above.
            # Do not append ML/AML rows to the later observation table here.
            # This keeps observation_rows scoped to its own section.

            if intelligence_data:

                exposure_count = _get_value(
                    intelligence_data,
                    (
                        "exposure_count",
                        "count",
                    ),
                )

                story.append(
                    Paragraph(
                        f"<b>Exposure Count:</b> "
                        f"{exposure_count}",
                        body_style,
                    )
                )

                exposures = _get_value(
                    intelligence_data,
                    (
                        "exposures",
                        "results",
                    ),
                    default=[],
                )

                if isinstance(
                    exposures,
                    (list, tuple),
                ) and exposures:

                    exposure_rows = [
                        [
                            Paragraph(
                                "Entity",
                                table_header_style,
                            ),
                            Paragraph(
                                "Type",
                                table_header_style,
                            ),
                            Paragraph(
                                "Source",
                                table_header_style,
                            ),
                            Paragraph(
                                "Category",
                                table_header_style,
                            ),
                            Paragraph(
                                "Confidence",
                                table_header_style,
                            ),
                            Paragraph(
                                "Hop",
                                table_header_style,
                            ),
                        ]
                    ]

                    for exposure in exposures:

                        exposure_dict = (
                            _to_dict(exposure)
                            or {}
                        )

                        entity_name = _get_value(
                            exposure_dict,
                            (
                                "name",
                                "entity_name",
                                "risk_entity_name",
                                "address",
                                "risk_entity_address",
                            ),
                        )

                        exposure_rows.append(
                            [
                                _paragraph_cell(
                                    entity_name,
                                    table_cell_small_style,
                                ),
                                _paragraph_cell(
                                    _get_value(
                                        exposure_dict,
                                        (
                                            "entity_type",
                                            "type",
                                        ),
                                    ),
                                    table_cell_small_style,
                                ),
                                _paragraph_cell(
                                    _get_value(
                                        exposure_dict,
                                        (
                                            "source",
                                        ),
                                    ),
                                    table_cell_small_style,
                                ),
                                _paragraph_cell(
                                    _get_value(
                                        exposure_dict,
                                        (
                                            "risk_category",
                                            "category",
                                        ),
                                    ),
                                    table_cell_small_style,
                                ),
                                _format_cell(
                                    _get_value(
                                        exposure_dict,
                                        (
                                            "confidence",
                                        ),
                                    )
                                ),
                                _format_cell(
                                    _get_value(
                                        exposure_dict,
                                        (
                                            "hop_count",
                                            "hop",
                                        ),
                                    )
                                ),
                            ]
                        )

                    exposure_table = Table(
                        exposure_rows,
                        colWidths=[
                            38 * mm,
                            25 * mm,
                            30 * mm,
                            30 * mm,
                            22 * mm,
                            15 * mm,
                        ],
                        repeatRows=1,
                    )

                    exposure_table.setStyle(
                        table_style
                    )

                    story.append(
                        exposure_table
                    )

                else:

                    story.append(
                        Paragraph(
                            "No matching intelligence "
                            "entities were found in "
                            "the analyzed exposure.",
                            body_style,
                        )
                    )

            else:

                story.append(
                    Paragraph(
                        "No intelligence exposure "
                        "data was available.",
                        body_style,
                    )
                )

            story.append(
                Spacer(1, 10)
            )

    else:

        story.append(
            Paragraph(
                "No intelligence exposure "
                "data was available.",
                body_style,
            )
        )

    # =====================================================
    # 11. INVESTIGATION SUMMARY
    # =====================================================

    story.append(
        Paragraph(
            "11. Investigation Summary",
            heading_style,
        )
    )

    story.append(
        Paragraph(
            "The report consolidates the blockchain "
            "investigation information available for "
            "the case at the time of generation. "
            "The information includes wallet activity, "
            "analytical indicators, graph relationships, "
            "temporal activity, intelligence exposure, "
            "analyst notes, evidence and investigation "
            "bookmarks.",
            body_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Total wallets analyzed:</b> "
            f"{len(wallets)}",
            body_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Total analyst notes:</b> "
            f"{len(notes)}",
            body_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Total evidence items:</b> "
            f"{len(evidence)}",
            body_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Total bookmarks:</b> "
            f"{len(bookmarks)}",
            body_style,
        )
    )

    # =====================================================
    # ANALYSIS COVERAGE
    # =====================================================

    if wallet_analyses:

        advanced_risk_count = 0
        graph_count = 0
        timeline_count = 0
        intelligence_count = 0
        ml_aml_count = 0
        vasp_count = 0

        for analysis in wallet_analyses:

            if _find_section(
                analysis,
                "risk",
            ):
                advanced_risk_count += 1

            if _find_section(
                analysis,
                "graph",
            ):
                graph_count += 1

            if _find_section(
                analysis,
                "timeline",
            ):
                timeline_count += 1

            if _find_section(
                analysis,
                "intelligence",
            ):
                intelligence_count += 1

            if analysis.get("ml") or analysis.get("aml"):
                ml_aml_count += 1

            if analysis.get("vasp_attribution"):
                vasp_count += 1

        story.append(
            Spacer(1, 8)
        )

        story.append(
            Paragraph(
                "Analysis Coverage",
                subheading_style,
            )
        )

        coverage_rows = [
            [
                Paragraph(
                    "Analysis",
                    table_header_style,
                ),
                Paragraph(
                    "Wallets With Data",
                    table_header_style,
                ),
            ],
            [
                "Advanced Risk",
                str(advanced_risk_count),
            ],
            [
                "Graph Analytics",
                str(graph_count),
            ],
            [
                "Timeline Analytics",
                str(timeline_count),
            ],
            [
                "Intelligence Exposure",
                str(intelligence_count),
            ],
            [
                "ML / AML Analysis",
                str(ml_aml_count),
            ],
            [
                "VASP Attribution",
                str(vasp_count),
            ],
        ]

        coverage_table = Table(
            coverage_rows,
            colWidths=[
                75 * mm,
                85 * mm,
            ],
            repeatRows=1,
        )

        coverage_table.setStyle(
            table_style
        )

        story.append(
            coverage_table
        )

    # =====================================================
    # KEY INVESTIGATION OBSERVATIONS
    # =====================================================

    # Initialize this before the conditional so the report generator
    # can never reference an unbound local variable.
    observation_rows = [
        [
            Paragraph("Observation", table_header_style),
            Paragraph("Supporting Data", table_header_style),
        ]
    ]

    if wallet_analyses:

        for analysis in wallet_analyses:
            wallet = analysis.get("wallet")
            wallet_label = (
                f"Wallet {getattr(wallet, 'id', 'N/A')}"
                if wallet is not None
                else "Wallet"
            )

            risk_data = _find_section(analysis, "risk")
            graph_data = _find_section(analysis, "graph")
            timeline_data = _find_section(analysis, "timeline")
            intelligence_data = _find_section(analysis, "intelligence")
            ml_data = analysis.get("ml")
            aml_data = analysis.get("aml")

            if risk_data:
                risk_score = _get_risk_value(
                    risk_data,
                    ("score", "risk_score", "total_score"),
                )
                observation_rows.append([
                    _paragraph_cell(
                        f"{wallet_label} analytical risk output",
                        table_cell_style,
                    ),
                    _paragraph_cell(
                        f"Score: {_format_cell(risk_score)} / 100; "
                        "development-stage model output.",
                        table_cell_style,
                    ),
                ])

            if graph_data:
                outgoing_tx = _get_value(
                    graph_data,
                    ("outgoing_transaction_count", "outgoing_transactions"),
                    default=None,
                )
                outgoing_value = _get_value(
                    graph_data,
                    ("outgoing_value",),
                    default=None,
                )
                fan_out = _get_value(
                    graph_data,
                    ("fan_out", "outgoing_connections"),
                    default=None,
                )
                multi_hop = _get_value(
                    graph_data,
                    ("multi_hop_exposure_count",),
                    default=None,
                )

                graph_parts = []
                if outgoing_tx is not None:
                    graph_parts.append(f"outgoing transactions: {outgoing_tx}")
                if outgoing_value is not None:
                    graph_parts.append(
                        f"outgoing value: {_format_cell(outgoing_value)}"
                    )
                if fan_out is not None:
                    graph_parts.append(f"fan-out: {fan_out}")
                if multi_hop is not None:
                    graph_parts.append(f"multi-hop exposure: {multi_hop}")

                if graph_parts:
                    observation_rows.append([
                        _paragraph_cell(
                            f"{wallet_label} graph activity",
                            table_cell_style,
                        ),
                        _paragraph_cell(
                            "; ".join(graph_parts) + ".",
                            table_cell_style,
                        ),
                    ])

            if timeline_data:
                total_tx = _get_value(
                    timeline_data,
                    ("total_transactions",),
                    default=None,
                )
                bursts = _get_value(
                    timeline_data,
                    ("bursts",),
                    default=None,
                )
                temporal_signals = _get_value(
                    timeline_data,
                    ("temporal_signals",),
                    default=None,
                )

                timeline_parts = []
                if total_tx is not None:
                    timeline_parts.append(f"transactions: {total_tx}")
                if isinstance(bursts, list):
                    timeline_parts.append(f"detected bursts: {len(bursts)}")
                if isinstance(temporal_signals, list):
                    timeline_parts.append(
                        f"temporal signals: {len(temporal_signals)}"
                    )

                if timeline_parts:
                    observation_rows.append([
                        _paragraph_cell(
                            f"{wallet_label} temporal activity",
                            table_cell_style,
                        ),
                        _paragraph_cell(
                            "; ".join(timeline_parts) + ".",
                            table_cell_style,
                        ),
                    ])

            if ml_data or aml_data:
                ml_parts = []

                if ml_data:
                    ml_probability = _get_value(
                        ml_data,
                        ("probability",),
                        default=None,
                    )
                    ml_prediction = _get_value(
                        ml_data,
                        ("prediction",),
                        default=None,
                    )
                    if isinstance(ml_probability, (int, float)):
                        ml_probability_text = f"{float(ml_probability) * 100:.2f}%"
                    else:
                        ml_probability_text = _format_cell(ml_probability)

                    ml_parts.append(
                        f"ML output: {ml_probability_text}; prediction: "
                        f"{_format_cell(ml_prediction)}"
                    )

                if aml_data:
                    review_status = _get_value(
                        aml_data,
                        ("review_status",),
                        default=None,
                    )
                    indicator_count = _get_value(
                        aml_data,
                        ("indicator_count",),
                        default=None,
                    )
                    if review_status is not None:
                        ml_parts.append(
                            f"AML review status: {_format_cell(review_status)}"
                        )
                    if indicator_count is not None:
                        ml_parts.append(
                            f"behavioral indicators: {_format_cell(indicator_count)}"
                        )

                if ml_parts:
                    observation_rows.append([
                        _paragraph_cell(
                            f"{wallet_label} ML / AML assessment",
                            table_cell_style,
                        ),
                        _paragraph_cell(
                            "; ".join(ml_parts) + ".",
                            table_cell_style,
                        ),
                    ])

            if intelligence_data:
                exposures = _get_value(
                    intelligence_data,
                    ("exposures",),
                    default=None,
                )
                exposure_count = _get_value(
                    intelligence_data,
                    ("exposure_count",),
                    default=None,
                )
                if exposure_count is None and isinstance(exposures, list):
                    exposure_count = len(exposures)

                if exposure_count is not None:
                    observation_rows.append([
                        _paragraph_cell(
                            f"{wallet_label} intelligence exposure",
                            table_cell_style,
                        ),
                        _paragraph_cell(
                            f"Observed exposure records: {exposure_count}.",
                            table_cell_style,
                        ),
                    ])

        if len(observation_rows) > 1:
            story.append(
                Spacer(1, 10)
            )
            story.append(
                Paragraph(
                    "Key Investigation Observations",
                    subheading_style,
                )
            )

            observations_table = Table(
                observation_rows,
                colWidths=[
                    60 * mm,
                    100 * mm,
                ],
                repeatRows=1,
            )
            observations_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), brand_navy),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.6, border_color),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, border_color),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                        colors.white,
                        colors.HexColor("#F8FAFC"),
                    ]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(observations_table)

    # =====================================================
    # 11. VASP ATTRIBUTION
    # =====================================================

    story.append(
        Paragraph(
            "11. VASP Attribution",
            heading_style,
        )
    )

    story.append(
        Paragraph(
            "This section records known VASP intelligence matches "
            "identified through transaction-connected wallet paths. "
            "A transaction-path match does not by itself establish "
            "ownership, control, or illicit activity.",
            body_style,
        )
    )

    vasp_found = False

    if wallet_analyses:

        for analysis in wallet_analyses:

            wallet = analysis.get("wallet")
            vasp_data = analysis.get("vasp_attribution")

            if not vasp_data:
                continue

            candidates = _get_value(
                vasp_data,
                ("candidates",),
                default=[],
            )

            if not isinstance(candidates, (list, tuple)):
                candidates = []

            story.append(
                Paragraph(
                    f"Wallet {getattr(wallet, 'id', 'N/A')} — "
                    f"{getattr(wallet, 'address', 'N/A')}",
                    subheading_style,
                )
            )

            status = _get_value(
                vasp_data,
                ("status",),
                default="N/A",
            )

            candidate_count = _get_value(
                vasp_data,
                ("candidate_count",),
                default=len(candidates),
            )

            max_hops = _get_value(
                vasp_data,
                ("max_hops",),
                default="N/A",
            )

            story.append(
                Paragraph(
                    f"<b>Status:</b> {_format_cell(status)} "
                    f"&nbsp;&nbsp; "
                    f"<b>Candidates:</b> {_format_cell(candidate_count)} "
                    f"&nbsp;&nbsp; "
                    f"<b>Max Hops:</b> {_format_cell(max_hops)}",
                    body_style,
                )
            )

            if candidates:

                vasp_found = True

                for candidate in candidates:

                    candidate_dict = _to_dict(candidate) or {}

                    name = _get_value(
                        candidate_dict,
                        ("name",),
                        default="N/A",
                    )
                    address = _get_value(
                        candidate_dict,
                        ("address",),
                        default="N/A",
                    )
                    chain = _get_value(
                        candidate_dict,
                        ("chain",),
                        default="N/A",
                    )
                    confidence = _get_value(
                        candidate_dict,
                        ("confidence",),
                        default=None,
                    )
                    hop = _get_value(
                        candidate_dict,
                        ("hop",),
                        default="N/A",
                    )
                    basis = _get_value(
                        candidate_dict,
                        ("attribution_basis",),
                        default="N/A",
                    )
                    source = _get_value(
                        candidate_dict,
                        ("source",),
                        default="N/A",
                    )
                    risk_category = _get_value(
                        candidate_dict,
                        ("risk_category",),
                        default="N/A",
                    )
                    reason = _get_value(
                        candidate_dict,
                        ("reason",),
                        default="N/A",
                    )
                    evidence_text = _get_value(
                        candidate_dict,
                        ("evidence",),
                        default="N/A",
                    )

                    if isinstance(confidence, (int, float)):
                        confidence_display = (
                            f"{float(confidence) * 100:.1f}%"
                        )
                    else:
                        confidence_display = _format_cell(confidence)

                    candidate_rows = [
                        [
                            Paragraph(
                                "Field",
                                table_header_style,
                            ),
                            Paragraph(
                                "Value",
                                table_header_style,
                            ),
                        ],
                        [
                            _paragraph_cell(
                                "Candidate VASP",
                                table_cell_style,
                            ),
                            _paragraph_cell(
                                name,
                                table_cell_style,
                            ),
                        ],
                        [
                            _paragraph_cell(
                                "VASP Address",
                                table_cell_style,
                            ),
                            _paragraph_cell(
                                address,
                                table_cell_small_style,
                            ),
                        ],
                        [
                            _paragraph_cell(
                                "Chain",
                                table_cell_style,
                            ),
                            _paragraph_cell(
                                chain,
                                table_cell_style,
                            ),
                        ],
                        [
                            _paragraph_cell(
                                "Confidence",
                                table_cell_style,
                            ),
                            _paragraph_cell(
                                confidence_display,
                                table_cell_style,
                            ),
                        ],
                        [
                            _paragraph_cell(
                                "Hop Count",
                                table_cell_style,
                            ),
                            _paragraph_cell(
                                hop,
                                table_cell_style,
                            ),
                        ],
                        [
                            _paragraph_cell(
                                "Attribution Basis",
                                table_cell_style,
                            ),
                            _paragraph_cell(
                                basis,
                                table_cell_style,
                            ),
                        ],
                        [
                            _paragraph_cell(
                                "Intelligence Source",
                                table_cell_style,
                            ),
                            _paragraph_cell(
                                source,
                                table_cell_style,
                            ),
                        ],
                        [
                            _paragraph_cell(
                                "Risk Category",
                                table_cell_style,
                            ),
                            _paragraph_cell(
                                risk_category,
                                table_cell_style,
                            ),
                        ],
                        [
                            _paragraph_cell(
                                "Reason",
                                table_cell_style,
                            ),
                            _paragraph_cell(
                                reason,
                                table_cell_style,
                            ),
                        ],
                        [
                            _paragraph_cell(
                                "Evidence",
                                table_cell_style,
                            ),
                            _paragraph_cell(
                                evidence_text,
                                table_cell_style,
                            ),
                        ],
                    ]

                    candidate_table = Table(
                        candidate_rows,
                        colWidths=[
                            45 * mm,
                            115 * mm,
                        ],
                        repeatRows=1,
                    )
                    candidate_table.setStyle(table_style)
                    story.append(candidate_table)

                    wallet_path = _get_value(
                        candidate_dict,
                        ("wallets",),
                        default=[],
                    )

                    if isinstance(wallet_path, (list, tuple)) and wallet_path:

                        story.append(Spacer(1, 7))
                        story.append(
                            Paragraph(
                                "Wallet Path",
                                subheading_style,
                            )
                        )

                        path_rows = [
                            [
                                Paragraph(
                                    "Hop",
                                    table_header_style,
                                ),
                                Paragraph(
                                    "Wallet Address",
                                    table_header_style,
                                ),
                            ]
                        ]

                        for index, path_wallet in enumerate(wallet_path):
                            path_rows.append(
                                [
                                    _format_cell(index),
                                    _paragraph_cell(
                                        path_wallet,
                                        table_cell_small_style,
                                    ),
                                ]
                            )

                        path_table = Table(
                            path_rows,
                            colWidths=[
                                20 * mm,
                                140 * mm,
                            ],
                            repeatRows=1,
                        )
                        path_table.setStyle(table_style)
                        story.append(path_table)

                    transfers = _get_value(
                        candidate_dict,
                        ("transfers",),
                        default=[],
                    )

                    if isinstance(transfers, (list, tuple)) and transfers:

                        story.append(Spacer(1, 7))
                        story.append(
                            Paragraph(
                                "Transaction Path Evidence",
                                subheading_style,
                            )
                        )

                        transfer_rows = [
                            [
                                Paragraph(
                                    "Transaction Hash",
                                    table_header_style,
                                ),
                                Paragraph(
                                    "Asset / Value",
                                    table_header_style,
                                ),
                                Paragraph(
                                    "Category",
                                    table_header_style,
                                ),
                                Paragraph(
                                    "Block / Timestamp",
                                    table_header_style,
                                ),
                            ]
                        ]

                        for transfer in transfers:

                            transfer_dict = _to_dict(transfer) or {}

                            tx_hash = _get_value(
                                transfer_dict,
                                ("transaction_hash",),
                                default="N/A",
                            )
                            asset = _get_value(
                                transfer_dict,
                                ("asset",),
                                default="N/A",
                            )
                            value = _get_value(
                                transfer_dict,
                                ("value",),
                                default="N/A",
                            )
                            category = _get_value(
                                transfer_dict,
                                ("category",),
                                default="N/A",
                            )
                            block_number = _get_value(
                                transfer_dict,
                                ("block_number",),
                                default="N/A",
                            )
                            timestamp = _get_value(
                                transfer_dict,
                                ("timestamp",),
                                default="N/A",
                            )

                            transfer_rows.append(
                                [
                                    _paragraph_cell(
                                        tx_hash,
                                        table_cell_small_style,
                                    ),
                                    _paragraph_cell(
                                        f"{_format_cell(asset)} / "
                                        f"{_format_cell(value)}",
                                        table_cell_small_style,
                                    ),
                                    _paragraph_cell(
                                        category,
                                        table_cell_small_style,
                                    ),
                                    _paragraph_cell(
                                        f"Block: {_format_cell(block_number)}; "
                                        f"{_format_cell(timestamp)}",
                                        table_cell_small_style,
                                    ),
                                ]
                            )

                        transfer_table = Table(
                            transfer_rows,
                            colWidths=[
                                52 * mm,
                                32 * mm,
                                30 * mm,
                                46 * mm,
                            ],
                            repeatRows=1,
                        )
                        transfer_table.setStyle(table_style)
                        story.append(transfer_table)

                    story.append(Spacer(1, 10))

            else:

                story.append(
                    Paragraph(
                        "No explicitly labelled VASP candidate was found "
                        "within the analyzed hop limit.",
                        body_style,
                    )
                )

            notice = _get_value(
                vasp_data,
                ("notice",),
                default="",
            )

            if notice:
                story.append(
                    Paragraph(
                        f"<b>VASP Notice:</b> {_format_cell(notice)}",
                        small_style,
                    )
                )

            story.append(Spacer(1, 8))

    if not vasp_found:
        story.append(
            Paragraph(
                "No VASP attribution candidate was found for the "
                "analyzed wallets.",
                body_style,
            )
        )

    # =====================================================
    # INVESTIGATION NOTICE
    # =====================================================

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "<b>Investigation Notice:</b> "
            "This report presents data and analytical "
            "indicators available in Crypto Guard V2 "
            "at the time of generation. Automated risk "
            "scores and indicators are not, by themselves, "
            "definitive determinations of illicit activity "
            "and should be reviewed by a qualified analyst. "
            "The current risk model and thresholds are "
            "development-stage analytical mechanisms and "
            "should not be interpreted as validated "
            "real-world risk probabilities.",
            small_style,
        )
    )

    # =====================================================
    # BUILD PDF
    # =====================================================

    document.build(
        story,
        onFirstPage=_draw_first_page,
        onLaterPages=_draw_later_pages,
    )

    buffer.seek(0)

    return buffer