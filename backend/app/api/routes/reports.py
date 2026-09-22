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
from app.services.ml_features import build_ml_features
from app.services.ml_model import get_ml_model
from app.services.aml_determination import build_aml_evidence_assessment
from app.services.vasp_attribution import analyze_vasp_attribution


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
            "ml": None,
            "aml": None,
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

        # -----------------------------------------------------
        # Research-stage ML Analysis + AML Evidence Assessment
        # -----------------------------------------------------

        try:
            # Reuse the same graph/timeline data already collected
            # for this report. This avoids another blockchain request.
            if analysis["graph"] is not None and analysis["timeline"] is not None:
                ml_features = build_ml_features(
                    behavior=analysis["graph"],
                    graph=analysis["graph"],
                    timeline=analysis["timeline"],
                )

                model = get_ml_model()
                ml_result = model.predict(ml_features)

                analysis["ml"] = {
                    "address": wallet.address,
                    "chain": wallet.chain,
                    "prediction": ml_result["prediction"],
                    "probability": ml_result["probability"],
                    "model_version": ml_result["model_version"],
                    "schema_version": ml_result["schema_version"],
                    "features": ml_result["feature_values"],
                    "status": "research_candidate",
                    "notice": (
                        "This is a research-stage ML model output. "
                        "The probability is not a validated real-world "
                        "AML probability and is not a definitive "
                        "illicit-activity determination."
                    ),
                }

                analysis["aml"] = build_aml_evidence_assessment(
                    graph=analysis["graph"],
                    timeline=analysis["timeline"],
                    ml_result=ml_result,
                )
        except (ValueError, FileNotFoundError):
            analysis["ml"] = None
            analysis["aml"] = None
        except Exception:
            # Report generation should remain available even if the
            # research-stage ML model is unavailable.
            analysis["ml"] = None
            analysis["aml"] = None

        # ---------------------------------------------------------
        # VASP Attribution
        # ---------------------------------------------------------
        try:
            analysis["vasp_attribution"] = analyze_vasp_attribution(
                address=wallet.address,
                chain=wallet.chain,
                max_hops=2,
            )
        except Exception:
            analysis["vasp_attribution"] = None
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

