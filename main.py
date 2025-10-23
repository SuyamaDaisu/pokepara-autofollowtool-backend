from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from typing import Optional
from datetime import datetime
import random

app = FastAPI()

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins - update with your frontend domain for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class AutoFollowState:
    def __init__(self):
        self.is_running = False
        self.target_count = 0
        self.current_count = 0
        self.task: Optional[asyncio.Task] = None
        self.websocket_clients = set()
        
    def reset(self):
        self.current_count = 0

state = AutoFollowState()

class StartRequest(BaseModel):
    target_count: int

class StatusResponse(BaseModel):
    is_running: bool
    target_count: int
    current_count: int
    timestamp: str

@app.get("/")
async def root():
    return {"message": "Auto Follow Backend API"}

@app.get("/api/status")
async def get_status():
    return StatusResponse(
        is_running=state.is_running,
        target_count=state.target_count,
        current_count=state.current_count,
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/start")
async def start_following(request: StartRequest):
    if state.is_running:
        raise HTTPException(status_code=400, detail="Already running")
    
    if request.target_count <= 0:
        raise HTTPException(status_code=400, detail="Target count must be greater than 0")
    
    state.is_running = True
    state.target_count = request.target_count
    state.reset()
    
    # Start the follow task
    state.task = asyncio.create_task(follow_process())
    
    return {"message": "Follow process started", "target_count": request.target_count}

@app.post("/api/stop")
async def stop_following():
    if not state.is_running:
        raise HTTPException(status_code=400, detail="Not currently running")
    
    state.is_running = False
    
    if state.task and not state.task.done():
        state.task.cancel()
        try:
            await state.task
        except asyncio.CancelledError:
            pass
    
    return {
        "message": "Follow process stopped",
        "completed_count": state.current_count,
        "target_count": state.target_count
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.websocket_clients.add(websocket)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "is_running": state.is_running,
            "current_count": state.current_count,
            "target_count": state.target_count
        })
        
        # Keep connection alive
        while True:
            try:
                # Wait for messages (ping/pong)
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        state.websocket_clients.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        state.websocket_clients.remove(websocket)

async def broadcast_update():
    """Broadcast current state to all connected WebSocket clients"""
    if not state.websocket_clients:
        return
    
    message = {
        "type": "update",
        "is_running": state.is_running,
        "current_count": state.current_count,
        "target_count": state.target_count,
        "timestamp": datetime.now().isoformat()
    }
    
    # Send to all clients
    disconnected_clients = set()
    for websocket in state.websocket_clients:
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected_clients.add(websocket)
    
    # Remove disconnected clients
    state.websocket_clients -= disconnected_clients

async def broadcast_no_more_users():
    """Broadcast 'no more users' message to all connected WebSocket clients"""
    if not state.websocket_clients:
        return
    
    message = {
        "type": "no_more_users",
        "is_running": False,
        "current_count": state.current_count,
        "target_count": state.target_count,
        "message": f"これ以上フォローできる人がいません。{state.current_count}人をフォローしました。",
        "timestamp": datetime.now().isoformat()
    }
    
    # Send to all clients
    disconnected_clients = set()
    for websocket in state.websocket_clients:
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected_clients.add(websocket)
    
    # Remove disconnected clients
    state.websocket_clients -= disconnected_clients

async def broadcast_completed():
    """Broadcast completion message when target is reached"""
    if not state.websocket_clients:
        return
    
    message = {
        "type": "no_more_users",
        "is_running": False,
        "current_count": state.current_count,
        "target_count": state.target_count,
        "message": f"完了！目標の{state.target_count}人をフォローしました。",
        "timestamp": datetime.now().isoformat()
    }
    
    # Send to all clients
    disconnected_clients = set()
    for websocket in state.websocket_clients:
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected_clients.add(websocket)
    
    # Remove disconnected clients
    state.websocket_clients -= disconnected_clients

async def follow_process():
    """
    Main follow automation process using Playwright
    This simulates the follow process with delays to avoid bot detection
    """
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Launch browser with realistic settings
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 520, 'height': 844}  # iPhone size
            )
            page = await context.new_page()
            
            # TODO: Navigate to your target website
            print("Navigating to login page...")
            await page.goto('https://sp.pokepara.jp/kanto/login/login_gal.aspx?back_url=%2fgal_manage%2findex.aspx', timeout=60000)
            
            print("Waiting for login form...")
            await page.wait_for_selector('input[name="login_id"]', state='visible', timeout=60000)
            await page.fill('input[name="login_id"]', 'tnjq-21755')
            await asyncio.sleep(0.5)
            await page.fill('input[name="pass"]', '6756')
            await asyncio.sleep(0.5)
            await page.click('input[type="submit"]')
            # await page.goto('https://sp.pokepara.jp/gal_manage/favorite/gal.html', timeout=60000)
            await page.goto('https://sp.pokepara.jp/gal_manage/favorite/gal.html?', timeout=60000)
            
            print(f"Followed: {state.current_count}/{state.target_count}")
            while state.is_running and state.current_count < state.target_count:
                try:
                    print(f"Progress: {state.current_count}/{state.target_count}")
                    # Get all blog_box divs
                    print("Finding all blog_box elements...")
                    await page.wait_for_selector('.blog_box', state='visible', timeout=10000)
                    blog_boxes = await page.query_selector_all('.blog_box')
                    cnt = len(blog_boxes)
                    print("Found", cnt, "blog_box elements")
                    # await asyncio.sleep(random.uniform(3, 5))
                    for i in range(cnt):
                        if state.current_count >= state.target_count:
                            break
                        print("Checking blog_box:", i)
                        blog_box = blog_boxes[i]
                        span = await blog_box.query_selector('span')
                        try:
                            if span:
                                span_class = await span.get_attribute('class')
                                print(f"Span class name: {span_class}")
                                if span_class == 'no_good':
                                    print("following blog_box:", i)
                                    link = await blog_box.query_selector('a')
                                    # Get the link URL and open in a new page
                                    link_url = await link.get_attribute('href')
                                    new_page = await context.new_page()
                                    await new_page.goto(link_url, timeout=60000)
                                    await new_page.wait_for_selector("a.bt_iine", state='visible', timeout=60000)
                                    await new_page.click("a.bt_iine")
                                    await asyncio.sleep(random.uniform(3, 5))
                                    await new_page.close()
                                    # Broadcast update to frontend after each successful follow
                                    state.current_count += 1
                                    await broadcast_update()
                        except Exception as e:
                            print(f"Error in blog_box loop: {e}")
                    if state.current_count >= state.target_count:
                        state.is_running = False
                        await broadcast_completed()
                        break
                    
                    # Check if next page button exists
                    next_button = await page.query_selector('a:has-text("→")')
                    if next_button is None:
                        print("No more pages available. Ending auto-follow process.")
                        state.is_running = False
                        await broadcast_no_more_users()
                        break
                    
                    # Click next page button
                    await page.click('a:has-text("→")')
                    await asyncio.sleep(random.uniform(2, 4))
                except Exception as e:
                    print(f"Error during follow action: {e}")
                    # If error occurs, try to check if we can continue
                    next_button = await page.query_selector('a:has-text("→")')
                    if next_button is None:
                        print("No more pages available (error state). Ending auto-follow process.")
                        state.is_running = False
                        await broadcast_no_more_users()
                        break
                    await asyncio.sleep(5)

            
            await browser.close()
            state.is_running = False
            await broadcast_update()
            
            if state.current_count >= state.target_count:
                print(f"Follow process completed! Followed {state.current_count} accounts.")
            else:
                print(f"Follow process stopped at {state.current_count}/{state.target_count}.")
                
    except asyncio.CancelledError:
        print("Follow process was cancelled")
        state.is_running = False
        await broadcast_update()
        raise
    except Exception as e:
        print(f"Fatal error in follow process: {e}")
        state.is_running = False
        await broadcast_update()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

