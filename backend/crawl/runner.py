import asyncio, time, json
from dataclasses import dataclass
from typing import Dict
from backend.core.config import settings
from backend.crawl.frontier import Frontier
from backend.crawl.fetch import Fetcher
from backend.crawl.bot_avoidance import BotAvoidanceStrategy
from backend.crawl.performance import preflight_ping_test
from backend.extract.html import extract_html
from backend.extract.pdfs import extract_pdf
from backend.extract.docx_ import extract_docx
from backend.extract.json_csv import extract_json_csv
from backend.storage.runs import RunStore
from backend.storage.confirmation import ConfirmationStore

@dataclass
class RunState:
    frontier: Frontier
    fetcher: Fetcher
    store: RunStore
    confirmation_store: ConfirmationStore
    started_at: float
    max_pages: int
    bot_strategy: BotAvoidanceStrategy | None = None
    is_complete: bool = False

class RunManager:
    def __init__(self):
        self._runs: Dict[str, RunState] = {}

    async def start(self, req) -> str:
        run_id = str(int(time.time()))
        bot_enabled = bool(req.botAvoidanceEnabled) if hasattr(req, "botAvoidanceEnabled") else False
        perf_mode = getattr(req, "perfMode", None) or settings.PERF_MODE
        
        # Store perf_mode in metadata
        store = RunStore(run_id, meta_overrides={
            "botAvoidanceEnabled": bot_enabled,
            "perf_mode": perf_mode
        })
        confirmation_store = ConfirmationStore(run_id)
        frontier = Frontier(req.url, max_pages=req.maxPages or settings.MAX_PAGES_DEFAULT)
        
        # Apply controlled measurement conditions
        if perf_mode == "controlled":
            # Controlled mode: fixed concurrency=1, no JS, static headers
            effective_concurrency = 1
            effective_render_enabled = False
            # Use controlled bot strategy (no randomization)
            bot_strategy = BotAvoidanceStrategy(controlled_mode=True) if bot_enabled else None
        elif perf_mode == "stress":
            # Stress mode: max concurrency, JS enabled
            effective_concurrency = req.concurrency or settings.GLOBAL_CONCURRENCY
            effective_render_enabled = True
            bot_strategy = BotAvoidanceStrategy() if bot_enabled else None
        else:  # realistic
            # Realistic mode: existing behavior
            effective_concurrency = req.concurrency or settings.GLOBAL_CONCURRENCY
            effective_render_enabled = settings.RENDER_ENABLED
            bot_strategy = BotAvoidanceStrategy() if bot_enabled else None
        
        fetcher = Fetcher(settings, bot_strategy=bot_strategy, perf_mode=perf_mode)
        self._runs[run_id] = RunState(frontier, fetcher, store, confirmation_store, time.time(), req.maxPages or settings.MAX_PAGES_DEFAULT, bot_strategy)
        
        # Store effective settings in metadata
        store_meta = {
            "effective_concurrency": effective_concurrency,
            "effective_render_enabled": effective_render_enabled
        }
        try:
            with open(store.meta_file, 'r') as f:
                meta = json.load(f)
            meta.update(store_meta)
            with open(store.meta_file, 'w') as f:
                json.dump(meta, f)
        except Exception as e:
            print(f"Error updating run meta with effective settings: {e}")
        
        # Run pre-flight ping test in controlled mode
        if perf_mode == "controlled":
            asyncio.create_task(self._preflight_test(run_id, req.url, fetcher))
        
        asyncio.create_task(self._worker_loop(run_id, effective_concurrency))
        return run_id
    
    async def _preflight_test(self, run_id: str, base_url: str, fetcher: Fetcher):
        """Run pre-flight ping test and store results in meta.json"""
        try:
            await fetcher.__aenter__()
            preflight_result = await preflight_ping_test(base_url, fetcher.session, num_samples=7)
            
            # Store in meta.json
            store = self._runs[run_id].store
            try:
                with open(store.meta_file, 'r') as f:
                    meta = json.load(f)
                meta["preflight"] = preflight_result
                with open(store.meta_file, 'w') as f:
                    json.dump(meta, f)
                print(f"Pre-flight ping test completed: {preflight_result}")
            except Exception as e:
                print(f"Error storing pre-flight results: {e}")
        except Exception as e:
            print(f"Pre-flight ping test failed: {e}")

    async def _worker_loop(self, run_id: str, effective_concurrency: int | None = None):
        state = self._runs[run_id]
        concurrency = effective_concurrency or settings.GLOBAL_CONCURRENCY
        sem = asyncio.Semaphore(concurrency)
        async def work(url):
            async with sem:
                # Determine if we should use multiple samples (controlled mode)
                perf_mode = getattr(state.fetcher, "perf_mode", "realistic")
                use_samples = perf_mode == "controlled" and settings.PERF_SAMPLES_PER_URL > 1
                
                if use_samples:
                    # Fetch multiple samples for performance measurement
                    samples = await state.fetcher.fetch_samples(
                        url,
                        num_samples=settings.PERF_SAMPLES_PER_URL,
                        render_mode="raw"  # Default to raw, JS rendering handled separately
                    )
                    
                    # Use first successful sample for content extraction
                    resp = None
                    for sample in samples:
                        if sample.get("status") == 200:
                            # Fetch once more to get full response for extraction
                            resp = await state.fetcher.fetch(url, render_mode="raw")
                            break
                    
                    if not resp:
                        # Try to get any response for error handling
                        resp = await state.fetcher.fetch(url, render_mode="raw")
                    
                    # Store performance samples in page data
                    if resp:
                        # Store samples in the page document
                        performance_samples = samples
                else:
                    # Single fetch (realistic/stress mode)
                    resp = await state.fetcher.fetch(url, render_mode="raw")
                    performance_samples = None
                
                if not resp:
                    state.store.log_error(url, "fetch_failed")
                    return
                if getattr(resp, "blocked_reason", None):
                    reason = resp.blocked_reason
                    state.store.log_error(url, f"bot_blocked:{reason}")
                    if state.bot_strategy:
                        state.bot_strategy.record_block(url, reason, resp.status)
                    return
                ct = resp.content_type
                if ct.startswith("text/html"):
                    doc = await extract_html(resp, run_id)
                    # Extract site data from first page
                    if url == state.frontier.start_url:
                        try:
                            state.confirmation_store.extract_site_data(resp.content.decode('utf-8', errors='ignore'), url)
                            print(f"Extracted site data for base URL: {url}")
                        except Exception as e:
                            print(f"Error extracting site data: {e}")
                elif ct in ("application/pdf",):
                    doc = await extract_pdf(resp)
                elif ct in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",):
                    doc = await extract_docx(resp)
                elif ct in ("application/json", "text/csv"):
                    doc = await extract_json_csv(resp)
                else:
                    doc = {"summary": {"url": resp.url, "contentType": ct, "title": None, "words": 0, "images": 0, "links": 0, "status": resp.status, "path": resp.path, "type": "BIN"}, "meta": {}, "text": None}
                
                # Add performance samples to document if available
                if performance_samples:
                    doc["performance_samples"] = performance_samples
                
                state.store.save_doc(doc)
                
                # Add to confirmation store pages index
                if doc.get("summary"):
                    summary = doc["summary"]
                    try:
                        # Use effective_load_ms if available, otherwise load_time_ms
                        load_time = resp.effective_load_ms if resp.effective_load_ms is not None else resp.load_time_ms
                        
                        state.confirmation_store.add_page_to_index({
                            "pageId": summary.get("pageId"),
                            "title": summary.get("title"),
                            "path": summary.get("path", "/"),
                            "url": summary.get("url"),
                            "status": summary.get("status"),
                            "status_code": summary.get("status_code"),
                            "words": summary.get("words", 0),
                            "mediaCount": summary.get("images", 0),
                            "loadTimeMs": int(load_time) if load_time else summary.get("load_time_ms"),
                            "contentLengthBytes": summary.get("content_length_bytes"),
                            "page_type": summary.get("page_type", "generic")
                        })
                        print(f"Added page to index: {summary.get('pageId')}")
                    except Exception as e:
                        print(f"Error adding page to index: {e}")
                for link in doc.get("links", []):
                    if isinstance(link, dict):
                        url = link.get("url")
                    else:
                        url = link
                    if url:
                        state.frontier.enqueue(url)
        while not state.frontier.done():
            batch = state.frontier.next_batch(concurrency)
            await asyncio.gather(*(work(u) for u in batch))
        state.store.finalize()
        state.is_complete = True

    async def progress(self, run_id: str):
        st = self._runs.get(run_id)
        if not st: return None
        snapshot = st.store.progress_snapshot(st.frontier)
        snapshot["is_complete"] = st.is_complete
        return snapshot

    async def stop(self, run_id: str):
        st = self._runs.pop(run_id, None)
        if not st: return False
        st.store.finalize()
        return True