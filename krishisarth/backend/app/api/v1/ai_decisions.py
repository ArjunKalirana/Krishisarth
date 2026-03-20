from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.db.postgres import get_db
from app.services import ai_service
from app.models.ai_decision import AIDecision

router = APIRouter()

@router.get("/{zone_id}/ai-decisions", response_model=dict)
def get_zone_ai_decisions(
    zone_id: str,
    limit: int = Query(10, ge=1, le=50),
    decision_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_farmer = Depends(deps.get_current_farmer),
    # verify_zone_owner checks farmer ownership of the zone
    _ = Depends(deps.verify_zone_owner)
) -> Any:
    """Retrieve historical AI reasoning cycles for a specific zone."""
    query = db.query(AIDecision).filter(AIDecision.zone_id == zone_id)
    if decision_type:
        query = query.filter(AIDecision.decision_type == decision_type)
    
    results = query.order_by(AIDecision.created_at.desc()).limit(limit).all()
    # Serialize results adding support for standard envelope
    return {
        "success": True, 
        "data": [
            {
                "id": str(d.id),
                "type": d.decision_type,
                "reasoning": d.reasoning,
                "confidence": d.confidence,
                "created_at": d.created_at
            } for d in results
        ]
    }

@router.post("/{zone_id}/ai-decisions/run", response_model=dict)
async def trigger_ai_inference(
    zone_id: str,
    db: Session = Depends(get_db),
    current_farmer = Depends(deps.get_current_farmer),
    _ = Depends(deps.verify_zone_owner)
) -> Any:
    """Manually initiate a real-time AI inference cycle for the specified zone."""
    try:
        decision = await ai_service.run_inference(zone_id, db)
        return {
            "success": True, 
            "data": {
                "id": str(decision.id),
                "type": decision.decision_type,
                "reasoning": decision.reasoning,
                "confidence": decision.confidence,
                "snapshot": decision.input_snapshot
            }
        }
    except Exception as e:
        logger_name = f"{__name__}.inference"
        import logging
        logging.getLogger(logger_name).error(f"Inference Failure: {str(e)}")
        
        # Mapping for safety-critical ModelLoadError
        if "ModelLoadError" in str(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI_ENGINE_UNAVAILABLE"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INFERENCE_EXECUTION_FAILED"
        )
