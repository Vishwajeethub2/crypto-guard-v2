from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.routes.users import get_current_user
from app.db.session import get_db

from app.db.case_model import Case
from app.db.wallet_model import Wallet
from app.db.note_model import CaseNote
from app.db.evidence_model import CaseEvidence
from app.db.bookmark_model import CaseBookmark

from app.services.report import generate_investigation_report
from app.services.advanced_risk import analyze_wallet_advanced_risk
from app.services.graph_analytics import analyze_wallet_graph_analytics
from app.services.timeline import analyze_wallet_timeline
from app.services.exposure import analyze_risk_exposure


router = APIRouter(
    prefix="/cases",
    tags=["Reports"],
)


@router.post(
    "/{case_id}/reports",
)
def generate_case_report(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # ---------------------------------------------------------
    # 1. Verify case ownership
    # ---------------------------------------------------------

    case = (
        db.query(Case)
        .filter(
            Case.id == case_id,
            Case.created_by == current_user.id,
        )
        .first()
    )

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    # ---------------------------------------------------------
    # 2. Load all case data
    # ---------------------------------------------------------

    wallets = (
        db.query(Wallet)
        .filter(
            Wallet.case_id == case_id,
        )
        .order_by(Wallet.id.asc())
        .all()
    )

    notes = (
        db.query(CaseNote)
        .filter(
            CaseNote.case_id == case_id,
        )
        .order_by(CaseNote.created_at.asc())
        .all()
    )

    evidence = (
        db.query(CaseEvidence)
        .filter(
            CaseEvidence.case_id == case_id,
        )
        .order_by(CaseEvidence.created_at.asc())
        .all()
    )

    bookmarks = (
        db.query(CaseBookmark)
        .filter(
            CaseBookmark.case_id == case_id,
        )
        .order_by(CaseBookmark.created_at.asc())
        .all()
    )

    # ---------------------------------------------------------
    # 3. Analyze every wallet
    # ---------------------------------------------------------

    wallet_analyses = []

    for wallet in wallets:
        analysis = {
            "wallet": wallet,
            "risk": None,
            "graph": None,
            "timeline": None,
            "intelligence": None,
        }

        # -----------------------------------------------------
        # Advanced Risk
        # -----------------------------------------------------

        try:
            analysis["risk"] = analyze_wallet_advanced_risk(
                address=wallet.address,
                chain=wallet.chain,
            )
        except Exception:
            analysis["risk"] = None

        # -----------------------------------------------------
        # Graph Analytics
        # -----------------------------------------------------

        try:
            analysis["graph"] = analyze_wallet_graph_analytics(
            address=wallet.address,
            chain=wallet.chain,
          )
        except Exception:
            analysis["graph"] = None

        # -----------------------------------------------------
        # Timeline Analytics
        # -----------------------------------------------------

        try:
            analysis["timeline"] = analyze_wallet_timeline(
                address=wallet.address,
                chain=wallet.chain,
            )
        except Exception:
            analysis["timeline"] = None

        # -----------------------------------------------------
        # Intelligence Exposure
        # -----------------------------------------------------

        try:
            analysis["intelligence"] = analyze_risk_exposure(
                address=wallet.address,
                chain=wallet.chain,
            )
        except Exception:
            analysis["intelligence"] = None

        wallet_analyses.append(analysis)

    # ---------------------------------------------------------
    # 4. Generate investigation PDF
    # ---------------------------------------------------------

    try:
        pdf_buffer = generate_investigation_report(
            case=case,
            wallets=wallets,
            notes=notes,
            evidence=evidence,
            bookmarks=bookmarks,
            wallet_analyses=wallet_analyses,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate investigation report: {error}",
        )

    # ---------------------------------------------------------
    # 5. Generate filename
    # ---------------------------------------------------------

    file_name = (
        f"case_{case.id}_investigation_report.pdf"
    )

    # ---------------------------------------------------------
    # 6. Return PDF
    # ---------------------------------------------------------

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{file_name}"'
            )
        },
    )