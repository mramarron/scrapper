import logging
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..config.database import SessionLocal
from ..models.models import (
    MthandiziBusinessLead,
    MthandiziScrapeRun,
    ScrapedLead,
    utc_now,
)
from ..schemas.schemas import (
    BusinessResponse,
    ScrapeRunResponse,
    ScrapedListingResponse,
    serialize_business,
    serialize_listing,
    serialize_scrape_run,
)
from ..services.services import MthandiziScraperService, describe_scrape_error


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")
scrape_executor = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="mthandizi-scraper",
)


def _execute_mthandizi_scrape(run_id: str) -> None:
    output = StringIO()
    try:
        with SessionLocal() as session:
            run = session.get(MthandiziScrapeRun, run_id)
            if run is None:
                raise LookupError(f"Scrape run {run_id} no longer exists")
            run.status = "running"
            run.started_at = utc_now()
            run.progress = {
                "stage": "starting",
                "message": "Starting scraper services",
            }
            session.commit()

        def persist_progress(progress: dict) -> None:
            with SessionLocal() as session:
                run = session.get(MthandiziScrapeRun, run_id)
                if run is None:
                    raise LookupError(f"Scrape run {run_id} no longer exists")
                run.progress = progress
                session.commit()

        (
            processed_count,
            created_count,
            processed_product_count,
            created_product_count,
        ) = MthandiziScraperService(SessionLocal).scrape_directory(
            progress_callback=persist_progress
        )
        output.write(
            f"Processed {processed_count} businesses; added {created_count} "
            f"new businesses and refreshed "
            f"{processed_count - created_count} existing businesses. "
            f"Processed {processed_product_count} featured products; added "
            f"{created_product_count} new products and refreshed "
            f"{processed_product_count - created_product_count} existing "
            "products."
        )
        final_status = "completed"
        error_code = ""
        error_message = ""
    except Exception as error:
        logger.exception("Mthandizi scraper run %s failed.", run_id)
        error_code, error_message = describe_scrape_error(error)
        final_status = "failed"
    finally:
        with SessionLocal() as session:
            run = session.get(MthandiziScrapeRun, run_id)
            if run is not None:
                run.status = final_status
                run.error_code = error_code
                run.error = error_message
                run.output = output.getvalue()[-4000:]
                run.completed_at = utc_now()
                run.is_active = False
                if final_status == "completed":
                    run.progress = {
                        **run.progress,
                        "stage": "completed",
                        "message": "Scrape completed",
                    }
                session.commit()


@router.get(
    "/marketplace-listings/",
    response_model=list[ScrapedListingResponse],
)
def list_marketplace_listings() -> list[ScrapedListingResponse]:
    with SessionLocal() as session:
        listings = session.scalars(
            select(ScrapedLead)
            .order_by(ScrapedLead.scraped_at.desc())
            .limit(50)
        ).all()
        return [serialize_listing(listing) for listing in listings]


@router.get("/businesses/", response_model=list[BusinessResponse])
def list_businesses() -> list[BusinessResponse]:
    with SessionLocal() as session:
        businesses = session.scalars(
            select(MthandiziBusinessLead)
            .order_by(MthandiziBusinessLead.scraped_at.desc())
            .limit(50)
        ).all()
        return [serialize_business(business) for business in businesses]


@router.get("/scrape-mthandizi/")
def get_latest_scrape_run() -> dict[str, ScrapeRunResponse | None]:
    with SessionLocal() as session:
        run = session.scalar(
            select(MthandiziScrapeRun)
            .order_by(MthandiziScrapeRun.created_at.desc())
            .limit(1)
        )
        return {"run": serialize_scrape_run(run) if run is not None else None}


@router.post(
    "/scrape-mthandizi/",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ScrapeRunResponse,
)
def start_mthandizi_scrape(response: Response) -> ScrapeRunResponse:
    run_id = str(uuid4())
    with SessionLocal() as session:
        run = MthandiziScrapeRun(id=run_id)
        session.add(run)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            active_run = session.scalar(
                select(MthandiziScrapeRun).where(
                    MthandiziScrapeRun.is_active.is_(True)
                )
            )
            if active_run is None:
                raise
            return serialize_scrape_run(active_run)

    try:
        scrape_executor.submit(_execute_mthandizi_scrape, run_id)
    except RuntimeError:
        logger.exception("Could not start Mthandizi scraper run %s.", run_id)
        with SessionLocal() as session:
            run = session.get(MthandiziScrapeRun, run_id)
            if run is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="The scraper could not be started. Try again.",
                )
            run.status = "failed"
            run.error_code = "worker_unavailable"
            run.error = "The scraper could not be started. Try again."
            run.completed_at = utc_now()
            run.is_active = False
            session.commit()
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return serialize_scrape_run(run)

    with SessionLocal() as session:
        run = session.get(MthandiziScrapeRun, run_id)
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The scrape run could not be read after it was started.",
            )
        return serialize_scrape_run(run)


@router.get(
    "/scrape-mthandizi/{run_id}/",
    response_model=ScrapeRunResponse,
)
def get_scrape_run(run_id: str) -> ScrapeRunResponse:
    try:
        normalized_id = str(UUID(run_id))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    with SessionLocal() as session:
        run = session.get(MthandiziScrapeRun, normalized_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return serialize_scrape_run(run)
