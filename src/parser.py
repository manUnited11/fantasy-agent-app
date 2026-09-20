import re
from typing import List
from pydantic import BaseModel

class WaiverTarget(BaseModel):
    pos: str
    player: str
    team: str
    priority_tier: str
    rz_touches: str
    route_tprr: str
    vegas_info: str
    status: str
    proj_pts: float

class SnapshotData(BaseModel):
    last_updated: str
    week: int
    season: int
    top_waiver_targets: List[WaiverTarget] = []

def parse_snapshot(markdown_text: str) -> SnapshotData:
    last_updated = ""
    ts_match = re.search(r"\*\*Last Updated:\*\*\s*(.+)", markdown_text)
    if ts_match:
        last_updated = ts_match.group(1).strip()
        
    week_match = re.search(r"\*\*Week:\*\*\s*(\d+)\s*\|\s*\*\*Season:\*\*\s*(\d+)", markdown_text)
    week = int(week_match.group(1)) if week_match else 1
    season = int(week_match.group(2)) if week_match else 2026

    waiver_targets = []
    
    waiver_table_match = re.search(
        r"## Top Available Waiver Targets.*?\n\|[^\n]+\n\|[-|\s]+\n(.*?)(?=\n---|\n##)", 
        markdown_text, 
        re.DOTALL
    )
    if waiver_table_match:
        rows = waiver_table_match.group(1).strip().split("\n")
        for row in rows:
            cols = [c.strip() for c in row.split("|")[1:-1]]
            if len(cols) >= 9:
                pos = cols[0]
                player = re.sub(r"\*", "", cols[1]).strip()
                team = cols[2]
                tier = re.sub(r"\*", "", cols[3]).strip()
                rz = cols[4]
                route = cols[5]
                vegas = cols[6]
                status = cols[7]
                pts_str = re.search(r"([\d\.]+)", cols[8])
                proj_pts = float(pts_str.group(1)) if pts_str else 0.0
                
                waiver_targets.append(WaiverTarget(
                    pos=pos, player=player, team=team,
                    priority_tier=tier, rz_touches=rz,
                    route_tprr=route, vegas_info=vegas,
                    status=status, proj_pts=proj_pts
                ))

    return SnapshotData(
        last_updated=last_updated,
        week=week,
        season=season,
        top_waiver_targets=waiver_targets
    )
